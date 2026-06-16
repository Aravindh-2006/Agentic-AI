import os
import json
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from models.report import Report
from models.roadmap import Roadmap
from agents.roadmap_agent import RoadmapAgent

roadmap_bp = Blueprint('roadmap', __name__)

# ── Helpers ──────────────────────────────────────────────────────────────────

def _parse_report(report):
    """Parse all JSON string columns in a report row to dicts."""
    fields = ['market_research', 'competitor_analysis', 'customer_persona',
              'revenue_model', 'swot_analysis', 'feasibility_scores', 'final_report']
    parsed = dict(report)
    for f in fields:
        raw = parsed.get(f)
        if raw and isinstance(raw, str):
            try:
                parsed[f] = json.loads(raw)
            except Exception:
                parsed[f] = {}
        elif not raw:
            parsed[f] = {}
    return parsed


def _count_all_tasks(roadmap_data):
    """Count total trackable tasks across all monthly plans."""
    total = 0
    for m in roadmap_data.get('monthly_plan', []):
        total += len(m.get('tasks', []))
    return total


# ── Routes ────────────────────────────────────────────────────────────────────

@roadmap_bp.route('/report/<int:report_id>/roadmap')
@login_required
def roadmap_page(report_id):
    """Renders the roadmap page. Generates roadmap on first visit if not exists."""
    report = Report.get(report_id)
    if not report or report['user_id'] != current_user.id:
        flash("You are not authorized to view this roadmap.", "danger")
        return redirect(url_for('dashboard.index'))

    if report['status'] != 'completed':
        flash("Validation must be completed before generating a roadmap.", "warning")
        return redirect(url_for('dashboard.index'))

    # Check if roadmap already exists
    roadmap_row = Roadmap.get_by_report(report_id)

    if not roadmap_row:
        # Generate the roadmap now
        parsed = _parse_report(report)
        try:
            agent = RoadmapAgent()
            roadmap_data = agent.generate(parsed)
        except Exception as e:
            flash(f"Failed to generate roadmap: {e}", "danger")
            return redirect(url_for('dashboard.view_report', report_id=report_id))

        roadmap_id = Roadmap.create(report_id, roadmap_data)
        roadmap_row = Roadmap.get_by_report(report_id)

    roadmap_id = roadmap_row['id']
    roadmap_data = roadmap_row['roadmap_data']

    # Compute progress
    total_tasks = _count_all_tasks(roadmap_data)
    progress = Roadmap.get_all_progress(roadmap_id)
    completed_count = sum(1 for v in progress.values() if v)
    pct = round((completed_count / total_tasks * 100) if total_tasks > 0 else 0, 1)

    parsed_report = _parse_report(report)

    return render_template(
        'roadmap.html',
        report=parsed_report,
        roadmap=roadmap_data,
        roadmap_id=roadmap_id,
        progress=progress,
        completed_count=completed_count,
        total_tasks=total_tasks,
        completion_pct=pct,
    )


@roadmap_bp.route('/report/<int:report_id>/roadmap/regenerate', methods=['POST'])
@login_required
def roadmap_regenerate(report_id):
    """Deletes existing roadmap and regenerates a fresh one."""
    report = Report.get(report_id)
    if not report or report['user_id'] != current_user.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for('dashboard.index'))

    Roadmap.delete_by_report(report_id)
    flash("Roadmap regenerated successfully.", "success")
    return redirect(url_for('roadmap.roadmap_page', report_id=report_id))


@roadmap_bp.route('/report/<int:report_id>/roadmap/task', methods=['POST'])
@login_required
def roadmap_task_toggle(report_id):
    """API endpoint to toggle a task's completion status."""
    report = Report.get(report_id)
    if not report or report['user_id'] != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    roadmap_row = Roadmap.get_by_report(report_id)
    if not roadmap_row:
        return jsonify({'error': 'Roadmap not found'}), 404

    data = request.get_json(silent=True) or {}
    task_key = (data.get('task_key') or '').strip()
    completed = bool(data.get('completed', False))

    if not task_key:
        return jsonify({'error': 'task_key required'}), 400

    roadmap_id = roadmap_row['id']
    Roadmap.set_task_complete(roadmap_id, task_key, completed)

    # Recalculate progress
    roadmap_data = roadmap_row['roadmap_data']
    total_tasks = _count_all_tasks(roadmap_data)
    progress = Roadmap.get_all_progress(roadmap_id)
    completed_count = sum(1 for v in progress.values() if v)
    pct = round((completed_count / total_tasks * 100) if total_tasks > 0 else 0, 1)

    return jsonify({
        'success': True,
        'completed_count': completed_count,
        'total_tasks': total_tasks,
        'completion_pct': pct,
    })


@roadmap_bp.route('/report/<int:report_id>/roadmap/pdf')
@login_required
def roadmap_pdf(report_id):
    """Generates and serves the roadmap as a PDF."""
    report = Report.get(report_id)
    if not report or report['user_id'] != current_user.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for('dashboard.index'))

    roadmap_row = Roadmap.get_by_report(report_id)
    if not roadmap_row:
        flash("Roadmap not found. Please open the roadmap page first.", "warning")
        return redirect(url_for('dashboard.view_report', report_id=report_id))

    roadmap_data = roadmap_row['roadmap_data']
    roadmap_id = roadmap_row['id']
    progress = Roadmap.get_all_progress(roadmap_id)

    from services.roadmap_pdf_service import generate_roadmap_pdf
    output_dir = os.path.join(current_app.root_path, 'reports')
    pdf_path = generate_roadmap_pdf(report, roadmap_data, progress, output_dir=output_dir)

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"{report['idea_title'].replace(' ', '_')}_roadmap.pdf",
        mimetype='application/pdf'
    )
