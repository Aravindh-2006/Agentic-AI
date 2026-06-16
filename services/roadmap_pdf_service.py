"""
Startup Roadmap PDF Generator
Produces a clean, structured multi-page PDF from roadmap_data.
"""
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, KeepTogether)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

PRIMARY   = colors.HexColor("#0f172a")
TEAL      = colors.HexColor("#0d9488")
INDIGO    = colors.HexColor("#6366f1")
LIGHT_BG  = colors.HexColor("#f8fafc")
MUTED     = colors.HexColor("#64748b")
WHITE     = colors.HexColor("#ffffff")
BORDER    = colors.HexColor("#e2e8f0")
SUCCESS   = colors.HexColor("#10b981")
WARNING   = colors.HexColor("#f59e0b")
DANGER    = colors.HexColor("#ef4444")


class RoadmapCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved)
        for state in self._saved:
            self.__dict__.update(state)
            if self._pageNumber > 1:
                self.saveState()
                self.setFont("Helvetica", 8)
                self.setFillColor(MUTED)
                self.drawString(54, 750, "AI Startup Validator — Execution Roadmap")
                self.drawRightString(558, 750, datetime.now().strftime("%Y-%m-%d"))
                self.setStrokeColor(BORDER)
                self.setLineWidth(0.5)
                self.line(54, 742, 558, 742)
                self.line(54, 55, 558, 55)
                self.drawString(54, 42, "Confidential — Startup Execution Plan")
                self.drawRightString(558, 42, f"Page {self._pageNumber} of {total}")
                self.restoreState()
            super().showPage()
        super().save()


def _sev_color(severity):
    s = (severity or '').lower()
    if s == 'high':   return DANGER
    if s == 'medium': return WARNING
    return SUCCESS


def _pri_color(priority):
    p = (priority or '').lower()
    if p == 'high':   return DANGER
    if p == 'medium': return WARNING
    return SUCCESS


def generate_roadmap_pdf(report, roadmap_data, progress, output_dir='reports'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    report_id = report.get('id', 'tmp')
    filepath = os.path.join(output_dir, f"roadmap_{report_id}.pdf")

    doc = SimpleDocTemplate(filepath, pagesize=letter,
                            leftMargin=54, rightMargin=54,
                            topMargin=72, bottomMargin=72)

    styles = getSampleStyleSheet()

    def sty(name, **kw):
        return ParagraphStyle(name, parent=styles['Normal'], **kw)

    cover_title = sty('CoverTitle', fontName='Helvetica-Bold', fontSize=30,
                      leading=36, textColor=PRIMARY, spaceAfter=8)
    cover_sub   = sty('CoverSub',   fontName='Helvetica', fontSize=13,
                      leading=17, textColor=TEAL, spaceAfter=24)
    h1 = sty('H1', fontName='Helvetica-Bold', fontSize=16, leading=20,
             textColor=PRIMARY, spaceBefore=16, spaceAfter=8, keepWithNext=True)
    h2 = sty('H2', fontName='Helvetica-Bold', fontSize=12, leading=15,
             textColor=TEAL,    spaceBefore=10, spaceAfter=5, keepWithNext=True)
    body  = sty('Body',  fontName='Helvetica', fontSize=10, leading=14, textColor=PRIMARY,  spaceAfter=6)
    muted = sty('Muted', fontName='Helvetica', fontSize=9,  leading=13, textColor=MUTED,    spaceAfter=4)
    bold  = sty('Bold',  fontName='Helvetica-Bold', fontSize=10, leading=14, textColor=PRIMARY)
    white_bold = sty('WBold', fontName='Helvetica-Bold', fontSize=14,
                     leading=18, textColor=WHITE, alignment=1)

    idea_title = report.get('idea_title', 'Startup Roadmap')
    overall    = report.get('overall_score', 0.0)
    phases     = roadmap_data.get('phases', [])
    monthly    = roadmap_data.get('monthly_plan', [])
    milestones = roadmap_data.get('milestones', [])
    warnings   = roadmap_data.get('risk_warnings', [])

    # Progress stats
    total_tasks = sum(len(m.get('tasks', [])) for m in monthly)
    done = sum(1 for v in progress.values() if v)
    pct  = round(done / total_tasks * 100, 1) if total_tasks else 0.0

    story = []

    # ── COVER ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 36))
    story.append(Paragraph("STARTUP EXECUTION ROADMAP", cover_sub))
    story.append(Paragraph(idea_title.upper(), cover_title))

    # Teal divider
    story.append(Table([['']], colWidths=[504], rowHeights=[4],
                       style=TableStyle([('BACKGROUND', (0,0),(-1,-1), TEAL),
                                         ('TOPPADDING',(0,0),(-1,-1),0),
                                         ('BOTTOMPADDING',(0,0),(-1,-1),0)])))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Validation Score: <b>{overall:.1f}/10</b>  |  "
                            f"Progress: <b>{done}/{total_tasks} tasks ({pct}%)</b>  |  "
                            f"Generated: {datetime.now().strftime('%Y-%m-%d')}", muted))
    story.append(Spacer(1, 60))

    # Cover stat cards
    stat_data = [[
        Paragraph(f"<b>{len(phases)}</b><br/>Phases", white_bold),
        Paragraph(f"<b>{len(monthly)}</b><br/>Months", white_bold),
        Paragraph(f"<b>{len(milestones)}</b><br/>Milestones", white_bold),
        Paragraph(f"<b>{len(warnings)}</b><br/>Risk Warnings", white_bold),
    ]]
    stat_table = Table(stat_data, colWidths=[126]*4,
                       style=TableStyle([
                           ('BACKGROUND', (0,0),(0,0), TEAL),
                           ('BACKGROUND', (1,0),(1,0), INDIGO),
                           ('BACKGROUND', (2,0),(2,0), colors.HexColor("#059669")),
                           ('BACKGROUND', (3,0),(3,0), colors.HexColor("#dc2626")),
                           ('TOPPADDING',   (0,0),(-1,-1), 16),
                           ('BOTTOMPADDING',(0,0),(-1,-1), 16),
                           ('ALIGN',  (0,0),(-1,-1), 'CENTER'),
                           ('VALIGN', (0,0),(-1,-1), 'MIDDLE'),
                           ('GRID',   (0,0),(-1,-1), 1, WHITE),
                       ]))
    story.append(stat_table)
    story.append(PageBreak())

    # ── PHASES ───────────────────────────────────────────────────────────────
    story.append(Paragraph("Execution Phases", h1))
    for ph in phases:
        pnum  = ph.get('phase_number', '')
        pname = ph.get('name', '')
        pdesc = ph.get('description', '')
        pdur  = ph.get('duration', '')
        pfoc  = ph.get('key_focus', '')
        ptasks = ph.get('tasks', [])

        header_data = [[
            Paragraph(f"Phase {pnum}: {pname}", sty(f'PhH{pnum}',
                fontName='Helvetica-Bold', fontSize=11, textColor=WHITE)),
            Paragraph(pdur, sty(f'PhD{pnum}',
                fontName='Helvetica', fontSize=9, textColor=WHITE, alignment=2))
        ]]
        header_tbl = Table(header_data, colWidths=[380, 124],
                           style=TableStyle([
                               ('BACKGROUND', (0,0),(-1,-1), TEAL),
                               ('TOPPADDING',(0,0),(-1,-1), 8),
                               ('BOTTOMPADDING',(0,0),(-1,-1), 8),
                               ('LEFTPADDING',(0,0),(-1,-1), 10),
                               ('RIGHTPADDING',(0,0),(-1,-1), 10),
                               ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                           ]))

        tasks_text = "<br/>".join(f"• {t}" for t in ptasks)
        body_data = [[
            Paragraph(f"<b>Focus:</b> {pfoc}<br/>{pdesc}", body),
            Paragraph(f"<b>Tasks:</b><br/>{tasks_text}", body)
        ]]
        body_tbl = Table(body_data, colWidths=[252, 252],
                         style=TableStyle([
                             ('GRID',(0,0),(-1,-1), 0.5, BORDER),
                             ('BACKGROUND',(0,0),(-1,-1), LIGHT_BG),
                             ('TOPPADDING',(0,0),(-1,-1), 8),
                             ('BOTTOMPADDING',(0,0),(-1,-1), 8),
                             ('LEFTPADDING',(0,0),(-1,-1), 10),
                             ('RIGHTPADDING',(0,0),(-1,-1), 10),
                             ('VALIGN',(0,0),(-1,-1),'TOP'),
                         ]))

        story.append(KeepTogether([header_tbl, body_tbl, Spacer(1, 8)]))

    story.append(PageBreak())

    # ── MONTHLY PLAN ─────────────────────────────────────────────────────────
    story.append(Paragraph("6-Month Execution Plan", h1))

    for m in monthly:
        mn    = m.get('month', '')
        theme = m.get('theme', '')
        goals = m.get('goals', [])
        tasks = m.get('tasks', [])
        dels  = m.get('deliverables', [])
        out   = m.get('expected_outcome', '')
        pri   = m.get('priority', 'Medium')

        pri_color = _pri_color(pri)

        month_header = [[
            Paragraph(f"Month {mn} — {theme}", sty(f'MH{mn}',
                fontName='Helvetica-Bold', fontSize=11, textColor=WHITE)),
            Paragraph(pri, sty(f'MP{mn}',
                fontName='Helvetica-Bold', fontSize=9, textColor=WHITE, alignment=2))
        ]]
        mh_tbl = Table(month_header, colWidths=[420, 84],
                       style=TableStyle([
                           ('BACKGROUND',(0,0),(0,0), INDIGO),
                           ('BACKGROUND',(1,0),(1,0), pri_color),
                           ('TOPPADDING',(0,0),(-1,-1), 8),
                           ('BOTTOMPADDING',(0,0),(-1,-1), 8),
                           ('LEFTPADDING',(0,0),(-1,-1), 10),
                           ('RIGHTPADDING',(0,0),(-1,-1), 10),
                           ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                       ]))

        goals_text = "<br/>".join(f"• {g}" for g in goals)
        tasks_text = "<br/>".join(f"• {t}" for t in tasks)
        dels_text  = "<br/>".join(f"• {d}" for d in dels)

        detail_data = [
            [Paragraph("<b>Goals</b>", bold), Paragraph(goals_text, body)],
            [Paragraph("<b>Tasks</b>", bold), Paragraph(tasks_text, body)],
            [Paragraph("<b>Deliverables</b>", bold), Paragraph(dels_text, body)],
            [Paragraph("<b>Expected Outcome</b>", bold), Paragraph(out, body)],
        ]
        detail_tbl = Table(detail_data, colWidths=[120, 384],
                           style=TableStyle([
                               ('GRID',(0,0),(-1,-1), 0.5, BORDER),
                               ('BACKGROUND',(0,0),(0,-1), LIGHT_BG),
                               ('TOPPADDING',(0,0),(-1,-1), 6),
                               ('BOTTOMPADDING',(0,0),(-1,-1), 6),
                               ('LEFTPADDING',(0,0),(-1,-1), 8),
                               ('RIGHTPADDING',(0,0),(-1,-1), 8),
                               ('VALIGN',(0,0),(-1,-1),'TOP'),
                           ]))

        story.append(KeepTogether([mh_tbl, detail_tbl, Spacer(1, 10)]))

    story.append(PageBreak())

    # ── MILESTONES ───────────────────────────────────────────────────────────
    story.append(Paragraph("Key Milestones", h1))
    ms_header = [[
        Paragraph("<b>#</b>", bold),
        Paragraph("<b>Milestone</b>", bold),
        Paragraph("<b>Target Month</b>", bold),
        Paragraph("<b>Success Metric</b>", bold),
    ]]
    ms_rows = ms_header[:]
    for ms in milestones:
        ms_rows.append([
            Paragraph(str(ms.get('milestone_number', '')), body),
            Paragraph(f"<b>{ms.get('title','')}</b><br/>{ms.get('description','')}", body),
            Paragraph(f"Month {ms.get('target_month','')}", body),
            Paragraph(ms.get('success_metric',''), body),
        ])

    ms_tbl = Table(ms_rows, colWidths=[30, 220, 80, 174],
                   style=TableStyle([
                       ('BACKGROUND',(0,0),(-1,0), LIGHT_BG),
                       ('GRID',(0,0),(-1,-1), 0.5, BORDER),
                       ('ROWBACKGROUNDS',(0,1),(-1,-1), [WHITE, LIGHT_BG]),
                       ('TOPPADDING',(0,0),(-1,-1), 6),
                       ('BOTTOMPADDING',(0,0),(-1,-1), 6),
                       ('VALIGN',(0,0),(-1,-1),'TOP'),
                   ]))
    story.append(ms_tbl)
    story.append(Spacer(1, 20))

    # ── RISK WARNINGS ────────────────────────────────────────────────────────
    story.append(Paragraph("Risk Warnings", h1))
    for w in warnings:
        sev   = w.get('severity', 'Medium')
        risk  = w.get('risk', '')
        phase = w.get('phase_affected', '')
        warn  = w.get('warning', '')
        mit   = w.get('mitigation', '')

        sc = _sev_color(sev)
        rw_header = [[
            Paragraph(f"⚠ {risk}  [{phase}]", sty(f'RWH_{risk[:8]}',
                fontName='Helvetica-Bold', fontSize=10, textColor=WHITE)),
            Paragraph(sev, sty(f'RWS_{sev}',
                fontName='Helvetica-Bold', fontSize=9, textColor=WHITE, alignment=2))
        ]]
        rw_h_tbl = Table(rw_header, colWidths=[420, 84],
                         style=TableStyle([
                             ('BACKGROUND',(0,0),(0,0), sc),
                             ('BACKGROUND',(1,0),(1,0), sc),
                             ('TOPPADDING',(0,0),(-1,-1), 7),
                             ('BOTTOMPADDING',(0,0),(-1,-1), 7),
                             ('LEFTPADDING',(0,0),(-1,-1), 10),
                             ('RIGHTPADDING',(0,0),(-1,-1), 10),
                             ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                         ]))
        rw_detail = [[
            Paragraph("<b>Warning</b>", bold),
            Paragraph(warn, body)
        ],[
            Paragraph("<b>Mitigation</b>", bold),
            Paragraph(mit, body)
        ]]
        rw_d_tbl = Table(rw_detail, colWidths=[90, 414],
                         style=TableStyle([
                             ('GRID',(0,0),(-1,-1), 0.5, BORDER),
                             ('BACKGROUND',(0,0),(0,-1), LIGHT_BG),
                             ('TOPPADDING',(0,0),(-1,-1), 6),
                             ('BOTTOMPADDING',(0,0),(-1,-1), 6),
                             ('LEFTPADDING',(0,0),(-1,-1), 8),
                             ('RIGHTPADDING',(0,0),(-1,-1), 8),
                             ('VALIGN',(0,0),(-1,-1),'TOP'),
                         ]))
        story.append(KeepTogether([rw_h_tbl, rw_d_tbl, Spacer(1, 8)]))

    # ── PROGRESS SUMMARY ─────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("Task Completion Summary", h1))
    story.append(Paragraph(
        f"Completed <b>{done}</b> of <b>{total_tasks}</b> tasks — <b>{pct}%</b> overall progress.",
        body))
    story.append(Spacer(1, 10))

    # Monthly progress breakdown
    prog_header = [[
        Paragraph("<b>Month</b>", bold),
        Paragraph("<b>Theme</b>", bold),
        Paragraph("<b>Tasks Done</b>", bold),
        Paragraph("<b>Completion</b>", bold),
    ]]
    prog_rows = prog_header[:]
    for m in monthly:
        mn = m.get('month', '')
        tasks = m.get('tasks', [])
        done_m = sum(1 for i, _ in enumerate(tasks)
                     if progress.get(f"month_{mn}_task_{i}", False))
        total_m = len(tasks)
        pct_m = round(done_m / total_m * 100, 1) if total_m else 0.0
        prog_rows.append([
            Paragraph(f"Month {mn}", body),
            Paragraph(m.get('theme', ''), body),
            Paragraph(f"{done_m}/{total_m}", body),
            Paragraph(f"{pct_m}%", body),
        ])

    prog_tbl = Table(prog_rows, colWidths=[60, 280, 80, 84],
                     style=TableStyle([
                         ('BACKGROUND',(0,0),(-1,0), LIGHT_BG),
                         ('GRID',(0,0),(-1,-1), 0.5, BORDER),
                         ('ROWBACKGROUNDS',(0,1),(-1,-1), [WHITE, LIGHT_BG]),
                         ('TOPPADDING',(0,0),(-1,-1), 6),
                         ('BOTTOMPADDING',(0,0),(-1,-1), 6),
                         ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                     ]))
    story.append(prog_tbl)

    doc.build(story, canvasmaker=RoadmapCanvas)
    return filepath
