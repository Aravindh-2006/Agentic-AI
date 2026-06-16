import os
import json
import time
import threading
from flask import Blueprint, render_template, redirect, url_for, request, flash, Response, send_file, current_app
from flask_login import login_required, current_user
from models.report import Report
from services.pdf_service import generate_validation_pdf

# Import all agents
from agents.market_research import MarketResearchAgent
from agents.competitor_analysis import CompetitorAnalysisAgent
from agents.customer_persona import CustomerPersonaAgent
from agents.revenue_model import RevenueModelAgent
from agents.swot_analysis import SWOTAnalysisAgent
from agents.feasibility_scoring import FeasibilityScoringAgent
from agents.report_generator import ReportGenerationAgent

dashboard_bp = Blueprint('dashboard', __name__)

def run_agent_validation_pipeline(app, report_id, title, description):
    """
    Asynchronous background runner executing the sequential multi-agent AI pipeline.
    Uses app context to coordinate safe database state updates.
    """
    with app.app_context():
        try:
            # 1. Initialize Agents
            mr_agent = MarketResearchAgent()
            comp_agent = CompetitorAnalysisAgent()
            cust_agent = CustomerPersonaAgent()
            rev_agent = RevenueModelAgent()
            swot_agent = SWOTAnalysisAgent()
            score_agent = FeasibilityScoringAgent()
            report_agent = ReportGenerationAgent()
            
            # Step 1: Market Research
            Report.update_status(report_id, 'market_research')
            market_data = mr_agent.analyze(title, description)
            Report.update_agent_output(report_id, 'market_research', json.dumps(market_data))

            # Step 2: Competitor Analysis
            Report.update_status(report_id, 'competitor_analysis')
            competitor_data = comp_agent.analyze(title, description, market_data)
            Report.update_agent_output(report_id, 'competitor_analysis', json.dumps(competitor_data))

            # Step 3: Customer Persona
            Report.update_status(report_id, 'customer_persona')
            persona_data = cust_agent.analyze(title, description, market_data, competitor_data)
            Report.update_agent_output(report_id, 'customer_persona', json.dumps(persona_data))

            # Step 4: Revenue Model
            Report.update_status(report_id, 'revenue_model')
            revenue_data = rev_agent.analyze(title, description, market_data, persona_data)
            Report.update_agent_output(report_id, 'revenue_model', json.dumps(revenue_data))

            # Step 5: SWOT Analysis
            Report.update_status(report_id, 'swot_analysis')
            swot_data = swot_agent.analyze(title, description, market_data, competitor_data, persona_data, revenue_data)
            Report.update_agent_output(report_id, 'swot_analysis', json.dumps(swot_data))

            # Step 6: Feasibility Scoring
            Report.update_status(report_id, 'scoring')
            scoring_data = score_agent.analyze(title, description, market_data, competitor_data, persona_data, revenue_data, swot_data)
            overall_score = float(scoring_data.get("overall_score", 0.0))

            # Step 7: Final Synthesis Report
            Report.update_status(report_id, 'report_generation')
            final_report_data = report_agent.analyze(
                idea_title=title, 
                idea_description=description, 
                market_research=market_data, 
                competitor=competitor_data, 
                customer_persona=persona_data, 
                revenue_model=revenue_data, 
                swot=swot_data, 
                feasibility=scoring_data
            )
            
            # Retrieve fresh database row state to generate PDF
            report_row = Report.get(report_id)
            report_row['market_research'] = market_data
            report_row['competitor_analysis'] = competitor_data
            report_row['customer_persona'] = persona_data
            report_row['revenue_model'] = revenue_data
            report_row['swot_analysis'] = swot_data
            report_row['feasibility_scores'] = scoring_data
            report_row['final_report'] = final_report_data
            
            # Generate the PDF report using our reportlab service
            pdf_path = generate_validation_pdf(report_row, output_dir=os.path.join(app.root_path, 'reports'))
            
            # Save final scores, report path, and set status to completed
            Report.update_final(
                report_id=report_id,
                feasibility_scores=scoring_data,
                overall_score=overall_score,
                final_report=json.dumps(final_report_data),
                pdf_path=os.path.basename(pdf_path)
            )
            print(f"Validation pipeline completed successfully for report {report_id}")
            
        except Exception as e:
            print(f"Error executing validation pipeline for report {report_id}: {e}")
            import traceback
            traceback.print_exc()
            Report.update_status(report_id, 'failed', error_message=str(e))


@dashboard_bp.route('/')
@login_required
def index():
    user_reports = Report.get_by_user(current_user.id)
    return render_template('dashboard.html', reports=user_reports)


@dashboard_bp.route('/validate', methods=['POST'])
@login_required
def validate():
    title = request.form.get('idea_title', '').strip()
    description = request.form.get('idea_description', '').strip()
    
    if not title or not description:
        flash("Please enter both a startup name/title and a concept description.", "danger")
        return redirect(url_for('dashboard.index'))
        
    try:
        # Create a report entry in database
        report_id = Report.create(
            user_id=current_user.id,
            idea_title=title,
            idea_description=description
        )
        
        # Fire off the async validation pipeline thread
        app = current_app._get_current_object()
        thread = threading.Thread(
            target=run_agent_validation_pipeline,
            args=(app, report_id, title, description)
        )
        thread.daemon = True
        thread.start()
        
        # Return dashboard page focusing on the progress of the validation run
        return redirect(url_for('dashboard.index', active_validation_id=report_id))
    except Exception as e:
        flash(f"Failed to submit startup idea for validation: {e}", "danger")
        return redirect(url_for('dashboard.index'))


@dashboard_bp.route('/stream-validation/<int:report_id>')
@login_required
def stream_validation(report_id):
    """
    Server-Sent Events endpoint to stream real-time pipeline status updates to the client.
    """
    def event_stream():
        last_status = None
        while True:
            report = Report.get(report_id)
            if not report:
                yield f"data: {json.dumps({'status': 'error', 'message': 'Report not found'})}\n\n"
                break
                
            status = report.get('status')
            
            # Send initial and updated states
            if status != last_status:
                last_status = status
                yield f"data: {json.dumps(report)}\n\n"
                
            if status in ('completed', 'failed'):
                break
                
            time.sleep(1) # Poll database status every second
            
    return Response(event_stream(), mimetype="text/event-stream")


@dashboard_bp.route('/report/<int:report_id>')
@login_required
def view_report(report_id):
    report = Report.get(report_id)
    if not report or report['user_id'] != current_user.id:
        flash("You are not authorized to view this report.", "danger")
        return redirect(url_for('dashboard.index'))
        
    if report['status'] != 'completed':
        flash("This report is not fully completed yet.", "warning")
        return redirect(url_for('dashboard.index', active_validation_id=report_id))
        
    # Safely convert database string columns to JSON objects for Jinja template rendering
    report['market_research_obj'] = json.loads(report['market_research']) if report['market_research'] else {}
    report['competitor_obj'] = json.loads(report['competitor_analysis']) if report['competitor_analysis'] else {}
    report['persona_obj'] = json.loads(report['customer_persona']) if report['customer_persona'] else {}
    report['revenue_obj'] = json.loads(report['revenue_model']) if report['revenue_model'] else {}
    report['swot_obj'] = json.loads(report['swot_analysis']) if report['swot_analysis'] else {}
    report['scores_obj'] = json.loads(report['feasibility_scores']) if report['feasibility_scores'] else {}
    report['final_report_obj'] = json.loads(report['final_report']) if report['final_report'] else {}
    
    return render_template('report.html', report=report)


@dashboard_bp.route('/report/<int:report_id>/pdf')
@login_required
def download_pdf(report_id):
    report = Report.get(report_id)
    if not report or report['user_id'] != current_user.id:
        flash("You are not authorized to download this report.", "danger")
        return redirect(url_for('dashboard.index'))
        
    if not report['pdf_path']:
        flash("PDF report has not been generated for this item.", "danger")
        return redirect(url_for('dashboard.view_report', report_id=report_id))
        
    pdf_file_path = os.path.join(current_app.root_path, 'reports', report['pdf_path'])
    if not os.path.exists(pdf_file_path):
        flash("The PDF file could not be located on disk. Re-generating it now...", "warning")
        # Regenerate on the fly if deleted or missing
        try:
            # Reconstruct dict structure
            report['market_research'] = json.loads(report['market_research']) if report['market_research'] else {}
            report['competitor_analysis'] = json.loads(report['competitor_analysis']) if report['competitor_analysis'] else {}
            report['customer_persona'] = json.loads(report['customer_persona']) if report['customer_persona'] else {}
            report['revenue_model'] = json.loads(report['revenue_model']) if report['revenue_model'] else {}
            report['swot_analysis'] = json.loads(report['swot_analysis']) if report['swot_analysis'] else {}
            report['feasibility_scores'] = json.loads(report['feasibility_scores']) if report['feasibility_scores'] else {}
            report['final_report'] = json.loads(report['final_report']) if report['final_report'] else {}
            
            generate_validation_pdf(report, output_dir=os.path.join(current_app.root_path, 'reports'))
        except Exception as e:
            flash(f"Failed to regenerate PDF: {e}", "danger")
            return redirect(url_for('dashboard.view_report', report_id=report_id))
            
    # Serve file to download
    return send_file(
        pdf_file_path,
        as_attachment=True,
        download_name=f"{report['idea_title'].replace(' ', '_')}_validation_report.pdf",
        mimetype="application/pdf"
    )


@dashboard_bp.route('/report/<int:report_id>/delete', methods=['POST'])
@login_required
def delete_report(report_id):
    report = Report.get(report_id)
    if not report or report['user_id'] != current_user.id:
        flash("You are not authorized to delete this report.", "danger")
        return redirect(url_for('dashboard.index'))
        
    try:
        # Delete PDF from disk if it exists
        if report['pdf_path']:
            pdf_file_path = os.path.join(current_app.root_path, 'reports', report['pdf_path'])
            if os.path.exists(pdf_file_path):
                os.remove(pdf_file_path)
                
        # Delete database entry
        Report.delete(report_id)
        flash("Validation report deleted successfully.", "success")
    except Exception as e:
        flash(f"Failed to delete report: {e}", "danger")
        
    return redirect(url_for('dashboard.index'))
