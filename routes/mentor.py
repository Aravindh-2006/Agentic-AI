import json
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models.report import Report
from models.mentor import MentorChat
from agents.mentor_agent import MentorAgent

mentor_bp = Blueprint('mentor', __name__)


def _parse_report_fields(report):
    """
    Converts all JSON string columns in the report dict to Python dicts.
    Returns a new dict safe for passing into the MentorAgent.
    """
    fields = [
        ('market_research', 'market_research'),
        ('competitor_analysis', 'competitor_analysis'),
        ('customer_persona', 'customer_persona'),
        ('revenue_model', 'revenue_model'),
        ('swot_analysis', 'swot_analysis'),
        ('feasibility_scores', 'feasibility_scores'),
        ('final_report', 'final_report'),
    ]
    parsed = dict(report)
    for db_col, key in fields:
        raw = parsed.get(db_col)
        if raw and isinstance(raw, str):
            try:
                parsed[key] = json.loads(raw)
            except Exception:
                parsed[key] = {}
        elif not raw:
            parsed[key] = {}
    return parsed


@mentor_bp.route('/report/<int:report_id>/mentor')
@login_required
def mentor_page(report_id):
    """
    Renders the AI Startup Mentor page for a completed report.
    """
    report = Report.get(report_id)
    if not report or report['user_id'] != current_user.id:
        flash("You are not authorized to access this mentor session.", "danger")
        return redirect(url_for('dashboard.index'))

    if report['status'] != 'completed':
        flash("Validation must be completed before accessing the mentor.", "warning")
        return redirect(url_for('dashboard.index'))

    parsed = _parse_report_fields(report)
    history = MentorChat.get_history(report_id, limit=50)

    # Build mentor dashboard summary from report data
    swot = parsed.get('swot_analysis', {})
    final = parsed.get('final_report', {})
    scores = parsed.get('feasibility_scores', {})

    mentor_dashboard = {
        'top_strength': (swot.get('strengths') or [''])[0],
        'top_weakness': (swot.get('weaknesses') or [''])[0],
        'biggest_opportunity': (swot.get('opportunities') or [''])[0],
        'critical_risk': '',
    }

    key_risks = final.get('key_risks', [])
    if key_risks and isinstance(key_risks[0], dict):
        mentor_dashboard['critical_risk'] = key_risks[0].get('risk', '')
    elif key_risks and isinstance(key_risks[0], str):
        mentor_dashboard['critical_risk'] = key_risks[0]

    return render_template(
        'mentor.html',
        report=parsed,
        history=history,
        mentor_dashboard=mentor_dashboard,
    )


@mentor_bp.route('/report/<int:report_id>/mentor/chat', methods=['POST'])
@login_required
def mentor_chat(report_id):
    """
    API endpoint — accepts a user question, calls MentorAgent,
    saves both messages, returns structured JSON response.
    """
    report = Report.get(report_id)
    if not report or report['user_id'] != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    if report['status'] != 'completed':
        return jsonify({'error': 'Report not completed'}), 400

    data = request.get_json(silent=True) or {}
    question = (data.get('question') or '').strip()
    if not question:
        return jsonify({'error': 'Question cannot be empty'}), 400

    if len(question) > 500:
        return jsonify({'error': 'Question too long (max 500 characters)'}), 400

    # Save the user message
    MentorChat.create_message(report_id, 'user', question)

    # Fetch recent history for context (excluding the message we just saved)
    history = MentorChat.get_history(report_id, limit=12)
    # Remove the last entry (the one we just added) so it's not duplicated in context
    history_for_context = history[:-1] if history else []

    parsed = _parse_report_fields(report)

    try:
        agent = MentorAgent()
        structured = agent.answer(question, parsed, history=history_for_context)
    except Exception as e:
        print(f"MentorAgent error for report {report_id}: {e}")
        return jsonify({'error': f'AI Mentor temporarily unavailable: {str(e)}'}), 500

    # Build plain-text answer for storage and display
    answer_text = structured.get('recommendation', 'I was unable to generate a response.')

    # Save assistant message with full structured response
    MentorChat.create_message(report_id, 'assistant', answer_text, structured_response=structured)

    return jsonify({
        'success': True,
        'structured': structured,
    })


@mentor_bp.route('/report/<int:report_id>/mentor/clear', methods=['POST'])
@login_required
def mentor_clear(report_id):
    """Clears chat history for a report."""
    report = Report.get(report_id)
    if not report or report['user_id'] != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    MentorChat.clear_history(report_id)
    return jsonify({'success': True})
