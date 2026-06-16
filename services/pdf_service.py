import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# Color Palette Definitions
PRIMARY_COLOR = colors.HexColor("#0f172a")    # Deep Slate
SECONDARY_COLOR = colors.HexColor("#0d9488")  # Teal Accent
TEXT_DARK = colors.HexColor("#1e293b")        # Dark Gray
TEXT_MUTED = colors.HexColor("#64748b")       # Muted Gray
BG_LIGHT = colors.HexColor("#f8fafc")         # Light Slate
WHITE = colors.HexColor("#ffffff")
BORDER_COLOR = colors.HexColor("#e2e8f0")

class NumberedCanvas(canvas.Canvas):
    """
    Canvas to calculate total page count and add page numbers dynamically in a two-pass render.
    Also adds a professional header and footer.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        # We don't draw header/footer on page 1 (cover page)
        if self._pageNumber == 1:
            return

        self.saveState()
        
        # Draw Header
        self.setFont("Helvetica", 8)
        self.setFillColor(TEXT_MUTED)
        self.drawString(54, 750, "AI Startup Validation Report")
        self.drawRightString(612 - 54, 750, datetime.now().strftime("%Y-%m-%d"))
        
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.5)
        self.line(54, 742, 612 - 54, 742)
        
        # Draw Footer
        self.line(54, 55, 612 - 54, 55)
        self.drawString(54, 42, "CONFIDENTIAL - For Entrepreneurial Review Only")
        self.drawRightString(612 - 54, 42, f"Page {self._pageNumber} of {page_count}")
        
        self.restoreState()


def get_safe_json(data_field):
    """
    Safely deserializes JSON columns which may be strings or already dictionaries.
    """
    if not data_field:
        return {}
    if isinstance(data_field, dict):
        return data_field
    try:
        return json.loads(data_field)
    except Exception as e:
        print(f"Failed to parse JSON for PDF: {e}")
        return {}


def get_safe_string(val, join_str=", "):
    """
    Safely converts a field to a string, joining lists if necessary.
    """
    if val is None:
        return "N/A"
    if isinstance(val, list):
        return join_str.join(str(item) for item in val)
    return str(val)



def generate_validation_pdf(report_data, output_dir="reports"):
    """
    Generates a beautifully structured multi-page PDF report for a given startup idea.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    report_id = report_data.get('id', 'temp')
    filename = f"report_{report_id}.pdf"
    filepath = os.path.join(output_dir, filename)

    # Letter size: 612 x 792 points. Margins: 0.75 in (54 pt)
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )

    styles = getSampleStyleSheet()
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=32,
        leading=38,
        textColor=PRIMARY_COLOR,
        spaceAfter=12
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=14,
        leading=18,
        textColor=SECONDARY_COLOR,
        spaceAfter=30
    )
    
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=PRIMARY_COLOR,
        spaceBefore=20,
        spaceAfter=10,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=SECONDARY_COLOR,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'ReportBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=TEXT_DARK,
        spaceAfter=8
    )

    body_bold = ParagraphStyle(
        'ReportBodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=TEXT_MUTED
    )
    
    badge_style = ParagraphStyle(
        'ScoreBadge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=WHITE,
        alignment=1 # Centered
    )

    story = []

    # Parse JSON fields safely
    market = get_safe_json(report_data.get('market_research'))
    competitor = get_safe_json(report_data.get('competitor_analysis'))
    persona = get_safe_json(report_data.get('customer_persona'))
    revenue = get_safe_json(report_data.get('revenue_model'))
    swot = get_safe_json(report_data.get('swot_analysis'))
    scores = get_safe_json(report_data.get('feasibility_scores'))
    final = get_safe_json(report_data.get('final_report'))

    idea_title = report_data.get('idea_title', 'Untitled Startup Idea')
    idea_description = report_data.get('idea_description', '')
    overall_score = report_data.get('overall_score', 0.0)
    created_at = report_data.get('created_at', datetime.now().strftime('%Y-%m-%d'))

    # ================= PAGE 1: COVER PAGE =================
    story.append(Spacer(1, 40))
    story.append(Paragraph("STARTUP VALIDATION REPORT", subtitle_style))
    story.append(Paragraph(idea_title.upper(), title_style))
    
    # Divider line
    story.append(Table(
        [['']], 
        colWidths=[504], 
        rowHeights=[4], 
        style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), SECONDARY_COLOR),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ])
    ))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph(f"<b>Submitted Idea:</b> {idea_description}", body_style))
    story.append(Spacer(1, 80))

    # Score Card Banner
    score_table_data = [
        [
            Paragraph("<b>VALIDATION METRIC</b><br/>Overall feasibility rating based on autonomous agent analysis.", meta_style),
            Paragraph(f"{overall_score:.1f}<font size=10>/10</font>", badge_style)
        ]
    ]
    
    score_banner = Table(
        score_table_data, 
        colWidths=[384, 120],
        style=TableStyle([
            ('BACKGROUND', (0,0), (0,0), BG_LIGHT),
            ('BACKGROUND', (1,0), (1,0), SECONDARY_COLOR),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (1,0), (1,0), 'CENTER'),
            ('TOPPADDING', (0,0), (-1,-1), 16),
            ('BOTTOMPADDING', (0,0), (-1,-1), 16),
            ('LEFTPADDING', (0,0), (-1,-1), 16),
            ('RIGHTPADDING', (0,0), (-1,-1), 16),
            ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ])
    )
    story.append(score_banner)
    story.append(Spacer(1, 120))

    # Metadata Footer of Cover Page
    metadata_data = [
        [Paragraph(f"<b>Analyst:</b> Autonomous AI Startup Validator", meta_style), 
         Paragraph(f"<b>Date:</b> {created_at}", meta_style)],
        [Paragraph(f"<b>System:</b> Gemini Orchestrated Multi-Agent", meta_style), 
         Paragraph("<b>Status:</b> Production Ready", meta_style)]
    ]
    meta_table = Table(metadata_data, colWidths=[252, 252])
    meta_table.setStyle(TableStyle([
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(meta_table)
    story.append(PageBreak())

    # ================= PAGE 2: EXECUTIVE SUMMARY & FEASIBILITY =================
    story.append(Paragraph("Executive Summary", h1_style))
    exec_summary = final.get("executive_summary", "No executive summary available.")
    if isinstance(exec_summary, list):
        for p in exec_summary:
            story.append(Paragraph(p, body_style))
    else:
        story.append(Paragraph(str(exec_summary), body_style))
        
    story.append(Spacer(1, 15))

    # Feasibility Score Breakdown Table
    story.append(Paragraph("Feasibility Scores Breakdown", h1_style))
    
    score_header = [Paragraph("<b>Category</b>", body_bold), Paragraph("<b>Score</b>", body_bold), Paragraph("<b>Evaluation Justification</b>", body_bold)]
    score_rows = [score_header]
    
    raw_scores = scores.get("scores", {})
    explanations = scores.get("explanations", {})
    
    category_labels = {
        "market_demand": "Market Demand",
        "competition": "Competition (Favorable)",
        "revenue_potential": "Revenue Potential",
        "technical_complexity": "Technical Feasibility",
        "scalability": "Scalability",
        "innovation": "Innovation / Moat",
        "investment_readiness": "Investment Readiness"
    }

    for key, label in category_labels.items():
        val = raw_scores.get(key, 0.0)
        exp = explanations.get(key, "N/A")
        score_rows.append([
            Paragraph(label, body_style),
            Paragraph(f"{val}/10", body_bold),
            Paragraph(exp, body_style)
        ])
        
    score_table = Table(score_rows, colWidths=[150, 60, 294])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_LIGHT),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, BG_LIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(score_table)
    story.append(PageBreak())

    # ================= PAGE 3: MARKET & COMPETITOR ANALYSIS =================
    story.append(Paragraph("Market Analysis", h1_style))
    story.append(Paragraph(f"<b>Primary Domain:</b> {market.get('domain', 'N/A')}", body_bold))
    story.append(Spacer(1, 4))
    demand_analysis = market.get('demand_analysis')
    if isinstance(demand_analysis, list):
        demand_text = "<br/>".join(f"• {item}" for item in demand_analysis)
    else:
        demand_text = get_safe_string(demand_analysis)
    story.append(Paragraph(demand_text, body_style))
    story.append(Spacer(1, 10))

    # Market Size Table
    m_size = market.get('market_size', {})
    size_data = [
        [Paragraph("<b>TAM</b> (Total Addressable Market)", body_bold), Paragraph(m_size.get('TAM', 'N/A'), body_style)],
        [Paragraph("<b>SAM</b> (Serviceable Addressable Market)", body_bold), Paragraph(m_size.get('SAM', 'N/A'), body_style)],
        [Paragraph("<b>SOM</b> (Serviceable Obtainable Market)", body_bold), Paragraph(m_size.get('SOM', 'N/A'), body_style)]
    ]
    size_table = Table(size_data, colWidths=[200, 304])
    size_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('BACKGROUND', (0,0), (0,-1), BG_LIGHT),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(size_table)
    story.append(Spacer(1, 5))
    story.append(Paragraph(f"<i>Justification:</i> {m_size.get('explanation', 'N/A')}", meta_style))
    
    story.append(Spacer(1, 15))
    
    # Competitor Comparison
    story.append(Paragraph("Competitor Comparison", h1_style))
    comp_list = competitor.get('competitors', [])
    if isinstance(comp_list, str):
        comp_list = [comp_list]
    elif not isinstance(comp_list, list):
        comp_list = []
    
    for c in comp_list:
        if isinstance(c, dict):
            c_title = get_safe_string(c.get('name', 'Competitor'))
            features_text = get_safe_string(c.get('features'))
            strengths_text = get_safe_string(c.get('strengths'))
            weaknesses_text = get_safe_string(c.get('weaknesses'))
        else:
            c_title = "Competitor"
            features_text = str(c)
            strengths_text = "N/A"
            weaknesses_text = "N/A"
            
        c_data = [
            [Paragraph(f"<b>Competitor: {c_title}</b>", body_bold), Paragraph("", body_style)],
            [Paragraph("<b>Key Features</b>", body_bold), Paragraph(features_text, body_style)],
            [Paragraph("<b>Strengths</b>", body_bold), Paragraph(strengths_text, body_style)],
            [Paragraph("<b>Weaknesses / Gaps</b>", body_bold), Paragraph(weaknesses_text, body_style)]
        ]
        c_table = Table(c_data, colWidths=[130, 374])
        c_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
            ('BACKGROUND', (0,0), (0,-1), BG_LIGHT),
            ('SPAN', (0,0), (1,0)),
            ('BACKGROUND', (0,0), (1,0), colors.HexColor("#f1f5f9")),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(c_table)
        story.append(Spacer(1, 10))
        
    story.append(PageBreak())

    # ================= PAGE 4: CUSTOMER PERSONAS & REVENUE STRATEGY =================
    story.append(Paragraph("Target Customer Personas", h1_style))
    personas = persona.get('personas', [])
    if isinstance(personas, str):
        personas = [personas]
    elif not isinstance(personas, list):
        personas = []
    
    for p_idx, p in enumerate(personas):
        if isinstance(p, dict):
            p_name = get_safe_string(p.get('name', 'Persona'))
            p_role = get_safe_string(p.get('role_or_occupation', 'N/A'))
            demographics_text = get_safe_string(p.get('demographics'))
            goals_text = get_safe_string(p.get('goals'))
            pain_points_text = get_safe_string(p.get('pain_points'))
            behavior_text = get_safe_string(p.get('behavior'))
        else:
            p_name = f"Persona #{p_idx+1}"
            p_role = "N/A"
            demographics_text = str(p)
            goals_text = "N/A"
            pain_points_text = "N/A"
            behavior_text = "N/A"
            
        p_data = [
            [Paragraph(f"<b>Persona #{p_idx+1}: {p_name}</b> ({p_role})", body_bold), Paragraph("", body_style)],
            [Paragraph("<b>Demographics</b>", body_bold), Paragraph(demographics_text, body_style)],
            [Paragraph("<b>Goals</b>", body_bold), Paragraph(goals_text, body_style)],
            [Paragraph("<b>Pain Points</b>", body_bold), Paragraph(pain_points_text, body_style)],
            [Paragraph("<b>Digital Behavior</b>", body_bold), Paragraph(behavior_text, body_style)]
        ]
        p_table = Table(p_data, colWidths=[120, 384])
        p_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
            ('BACKGROUND', (0,0), (0,-1), BG_LIGHT),
            ('SPAN', (0,0), (1,0)),
            ('BACKGROUND', (0,0), (1,0), colors.HexColor("#f1f5f9")),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(p_table)
        story.append(Spacer(1, 12))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Revenue & Monetization Model", h1_style))
    monetization = revenue.get('monetization_strategies', [])
    if isinstance(monetization, str):
        monetization = [monetization]
    elif not isinstance(monetization, list):
        monetization = []
    
    mon_bullets = []
    for m in monetization:
        if isinstance(m, dict):
            mon_bullets.append(f"<b>{m.get('strategy', 'Stream')}:</b> {m.get('description', '')}")
        else:
            mon_bullets.append(str(m))
    
    story.append(Paragraph("<br/>".join([f"• {b}" for b in mon_bullets]), body_style))
    story.append(Spacer(1, 10))
    
    # Pricing Tiers Table
    pricing = revenue.get('pricing_tiers', [])
    if isinstance(pricing, str):
        pricing = [pricing]
    elif not isinstance(pricing, list):
        pricing = []
        
    if pricing:
        price_header = [Paragraph("<b>Tier</b>", body_bold), Paragraph("<b>Price Point</b>", body_bold), Paragraph("<b>Features Included</b>", body_bold)]
        price_rows = [price_header]
        for t in pricing:
            if isinstance(t, dict):
                tier_name = get_safe_string(t.get('tier_name', 'N/A'))
                price_point = get_safe_string(t.get('price_point', 'N/A'))
                billing_cycle = get_safe_string(t.get('billing_cycle', 'monthly'))
                feat_list = t.get('key_features', [])
                feats = get_safe_string(feat_list)
                price_rows.append([
                    Paragraph(tier_name, body_style),
                    Paragraph(f"{price_point} ({billing_cycle})", body_style),
                    Paragraph(feats, body_style)
                ])
            else:
                price_rows.append([
                    Paragraph("Tier", body_style),
                    Paragraph("N/A", body_style),
                    Paragraph(str(t), body_style)
                ])
            
        price_table = Table(price_rows, colWidths=[100, 150, 254])
        price_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), BG_LIGHT),
            ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, BG_LIGHT]),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(price_table)
        
    story.append(PageBreak())


    # ================= PAGE 5: SWOT MATRIX & RECOMMENDATIONS =================
    story.append(Paragraph("SWOT Matrix", h1_style))
    
    # SWOT Grid simulated via a Table
    s_list = swot.get('strengths', [])
    w_list = swot.get('weaknesses', [])
    o_list = swot.get('opportunities', [])
    t_list = swot.get('threats', [])
    
    def list_to_p(lst):
        if isinstance(lst, str):
            return lst
        if not isinstance(lst, list):
            return str(lst)
        return "<br/>".join([f"• {x}" for x in lst])

    swot_table_data = [
        [
            Paragraph("<b>STRENGTHS (Internal)</b><br/>" + list_to_p(s_list), body_style),
            Paragraph("<b>WEAKNESSES (Internal)</b><br/>" + list_to_p(w_list), body_style)
        ],
        [
            Paragraph("<b>OPPORTUNITIES (External)</b><br/>" + list_to_p(o_list), body_style),
            Paragraph("<b>THREATS (External)</b><br/>" + list_to_p(t_list), body_style)
        ]
    ]
    
    swot_table = Table(swot_table_data, colWidths=[252, 252])
    swot_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('BACKGROUND', (0,0), (0,0), colors.HexColor("#f0fdf4")), # Light emerald green for S
        ('BACKGROUND', (1,0), (1,0), colors.HexColor("#fef2f2")), # Light red for W
        ('BACKGROUND', (0,1), (0,1), colors.HexColor("#eff6ff")), # Light blue for O
        ('BACKGROUND', (1,1), (1,1), colors.HexColor("#fff7ed")), # Light orange for T
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(swot_table)
    story.append(Spacer(1, 20))

    # Recommendations & Risks
    story.append(Paragraph("Key Risk Mitigation Roadmap", h1_style))
    risks = final.get("key_risks", [])
    if isinstance(risks, str):
        risks = [risks]
    elif not isinstance(risks, list):
        risks = []
    
    risk_rows = [[Paragraph("<b>Identified Risk Factor</b>", body_bold), Paragraph("<b>Strategic Mitigation Pathway</b>", body_bold)]]
    for r in risks:
        if isinstance(r, dict):
            risk_text = get_safe_string(r.get('risk', 'N/A'))
            mitigation_text = get_safe_string(r.get('mitigation', 'N/A'))
        else:
            risk_text = str(r)
            mitigation_text = 'N/A'
            
        risk_rows.append([
            Paragraph(risk_text, body_style),
            Paragraph(mitigation_text, body_style)
        ])
        
    risk_table = Table(risk_rows, colWidths=[200, 304])
    risk_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('BACKGROUND', (0,0), (-1,0), BG_LIGHT),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(risk_table)
    
    story.append(Spacer(1, 15))
    story.append(Paragraph("Actionable Recommendations Roadmap", h2_style))
    recs = final.get("recommendations", [])
    if isinstance(recs, str):
        recs = [recs]
    elif not isinstance(recs, list):
        recs = []
        
    rec_bullets = []
    for r in recs:
        if isinstance(r, dict):
            # If the LLM returned structured recommendation objects
            rec_desc = r.get('description', r.get('text', get_safe_string(r)))
        else:
            rec_desc = str(r)
        rec_bullets.append(Paragraph(f"• {rec_desc}", body_style))
    
    for r_bullet in rec_bullets:
        story.append(r_bullet)
        
    story.append(Spacer(1, 10))
    story.append(Paragraph("Strategic Conclusion", h2_style))
    story.append(Paragraph(get_safe_string(final.get("conclusion", "No strategic conclusion available.")), body_style))


    # Build PDF Document
    doc.build(story, canvasmaker=NumberedCanvas)
    return filepath
