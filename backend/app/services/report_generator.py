import io
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from backend.app.core.config import settings
from backend.app.models.schemas import AISummary, ExtractedEntities, MathematicalResults, SourceItem, OfficialSourcesReport

logger = logging.getLogger(__name__)

SUMMARY_SYSTEM_PROMPT = """You are a senior cybersecurity intelligence analyst at CyberVerify.
You are generating a factual, objective, and executive intelligence report summarizing the investigation of a cybersecurity claim.
You must adhere strictly to the verified evidence provided. Do not invent any facts.

Respond strictly in valid JSON matching this schema:
{
  "what_reportedly_happened": "Clear factual overview of what incident was claimed to have occurred.",
  "supporting_evidence_summary": "Detailed summary of findings and sources that corroborate the claim.",
  "contradicting_evidence_summary": "Detailed summary of findings, denials, or proof that dispute or contradict the claim.",
  "official_sources_position": "What official company disclosures, CISOs, or government advisories have stated (or note that none were found).",
  "uncertainties_and_gaps": "Specific unknown details, pending investigations, or uncorroborated elements.",
  "final_assessment": "Executive conclusion synthesizing the mathematical score and verified evidence."
}"""

async def generate_ai_summary(
    claim: str,
    entities: ExtractedEntities,
    verdict: str,
    math_results: MathematicalResults,
    official_sources: OfficialSourcesReport,
    sources: List[SourceItem]
) -> AISummary:
    """Generates a structured 6-point AI intelligence summary."""
    # Try Gemini
    if settings.GEMINI_API_KEY:
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
            # Format context safely
            source_lines = [f"- [{s.source_category}] {s.publisher}: {s.title} (Stance: {s.evidence_classification})" for s in sources[:8]]
            context = (
                f"Claim: {claim}\n"
                f"Organisation: {entities.organisation}\n"
                f"Incident Type: {entities.incident_type}\n"
                f"Mathematical Verdict: {verdict}\n"
                f"Weighted Score: {math_results.weighted_evidence_score}\n"
                f"Official Sources Status: {official_sources.status_summary}\n"
                f"Collected Sources:\n" + "\n".join(source_lines)
            )
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"{SUMMARY_SYSTEM_PROMPT}\n\nContext:\n{context}",
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            if response.text:
                data = json.loads(response.text)
                return AISummary(**data)
        except Exception as e:
            logger.warning(f"LLM summary generation failed: {e}. Falling back to structured heuristic summary...")

    # Deterministic Structured Intelligence Summary Fallback
    supporting = [s for s in sources if s.evidence_classification == "SUPPORTING"]
    contradicting = [s for s in sources if s.evidence_classification == "CONTRADICTING"]
    
    what_happened = (
        f"A cybersecurity claim alleged that {entities.organisation} was affected by a {entities.incident_type.lower()}, "
        f"specifically alleging that: '{entities.allegation}'."
    )
    
    if supporting:
        sup_text = f"{len(supporting)} source(s) including {', '.join([s.publisher for s in supporting[:3]])} reported corroborating indicators."
    else:
        sup_text = "No credible independent sources provided factual evidence directly supporting the core allegation."

    if contradicting:
        con_text = f"{len(contradicting)} source(s) contradicted or refuted the claim, citing {', '.join([s.publisher for s in contradicting[:3]])}."
    else:
        con_text = "No explicit public rebuttals or formal contradictory statements were identified in collected public reporting."

    official_text = official_sources.status_summary

    uncertainties = (
        f"Confidence is estimated at {int(math_results.confidence_score * 100)}%. "
        f"Investigation analyzed {math_results.independent_source_count} independent source clusters. "
        f"{'Official vendor security advisory was not verified.' if math_results.official_sources_count == 0 else 'Official primary documentation was identified.'}"
    )

    assessment = (
        f"Based on a calculated weighted evidence score of {math_results.weighted_evidence_score} "
        f"and {math_results.independent_source_count} independent source clusters, the claim has been classified as {verdict}."
    )

    return AISummary(
        what_reportedly_happened=what_happened,
        supporting_evidence_summary=sup_text,
        contradicting_evidence_summary=con_text,
        official_sources_position=official_text,
        uncertainties_and_gaps=uncertainties,
        final_assessment=assessment
    )

def build_pdf_report(investigation_data: Dict[str, Any]) -> bytes:
    """Generates an executive PDF intelligence report using ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom professional styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=14
    )
    
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )

    badge_style = ParagraphStyle(
        'VerdictBadge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=16,
        textColor=colors.HexColor('#FFFFFF'),
        alignment=1  # Center
    )

    story = []

    # Header
    story.append(Paragraph("CYBERVERIFY | Threat Intelligence & News Verification", title_style))
    story.append(Paragraph(f"Official Investigation Briefing • Report ID: {investigation_data.get('investigation_id')} • Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=12))

    # Verdict Card Table
    verdict = investigation_data.get("verdict", "UNVERIFIED")
    conf = int(investigation_data.get("confidence_score", 0.0) * 100)
    verdict_colors = {
        "VERIFIED": colors.HexColor('#16A34A'),
        "LIKELY TRUE": colors.HexColor('#2563EB'),
        "FALSE": colors.HexColor('#DC2626'),
        "MISLEADING": colors.HexColor('#D97706'),
        "UNVERIFIED": colors.HexColor('#64748B')
    }
    v_color = verdict_colors.get(verdict, colors.HexColor('#64748B'))

    verdict_table_data = [
        [
            Paragraph(f"VERDICT: {verdict}", badge_style),
            Paragraph(f"<b>Confidence:</b> {conf}%<br/><b>Weighted Score:</b> {investigation_data.get('mathematical_results', {}).get('weighted_evidence_score', 0.0)}", body_style)
        ]
    ]
    vt = Table(verdict_table_data, colWidths=[200, 340])
    vt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), v_color),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#F1F5F9')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (0, 0), 10),
    ]))
    story.append(vt)
    story.append(Spacer(1, 10))

    # Claim Overview Section
    story.append(Paragraph("Claim Overview", h2_style))
    entities = investigation_data.get("extracted_entities", {})
    overview_data = [
        [Paragraph("<b>Original Claim:</b>", body_style), Paragraph(str(investigation_data.get("original_claim")), body_style)],
        [Paragraph("<b>Target Organisation:</b>", body_style), Paragraph(str(entities.get("organisation", "Unknown")), body_style)],
        [Paragraph("<b>Incident Category:</b>", body_style), Paragraph(str(entities.get("incident_type", "Cybersecurity Incident")), body_style)],
        [Paragraph("<b>Allegation:</b>", body_style), Paragraph(str(entities.get("allegation", "")), body_style)],
    ]
    ot = Table(overview_data, colWidths=[130, 410])
    ot.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(ot)
    story.append(Spacer(1, 10))

    # Mathematical Analysis Section
    story.append(Paragraph("Mathematical & Bayesian Evidence Calculations", h2_style))
    m = investigation_data.get("mathematical_results", {})
    dist = m.get("evidence_distribution", {})
    bayesian = m.get("bayesian_analysis", {})

    math_data = [
        [
            Paragraph("<b>Weighted Score (E):</b>", body_style),
            Paragraph(f"{m.get('weighted_evidence_score', 0.0)} (Scale: -1.0 to +1.0)", body_style),
            Paragraph("<b>Total Sources:</b>", body_style),
            Paragraph(f"{m.get('total_sources', 0)} ({m.get('independent_source_count', 0)} clusters)", body_style)
        ],
        [
            Paragraph("<b>Supporting Stance:</b>", body_style),
            Paragraph(f"{dist.get('supporting_percentage', 0)}% ({dist.get('supporting_count', 0)})", body_style),
            Paragraph("<b>Contradicting Stance:</b>", body_style),
            Paragraph(f"{dist.get('contradicting_percentage', 0)}% ({dist.get('contradicting_count', 0)})", body_style)
        ],
        [
            Paragraph("<b>Prior P(Claim):</b>", body_style),
            Paragraph(f"{int(bayesian.get('prior_probability', 0.25)*100)}%", body_style),
            Paragraph("<b>Posterior P(Claim|E):</b>", body_style),
            Paragraph(f"{int(bayesian.get('posterior_probability', 0)*100)}% (Bayes Factor: {bayesian.get('bayes_factor', 1.0)})", body_style)
        ]
    ]
    mt = Table(math_data, colWidths=[130, 140, 130, 140])
    mt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(mt)
    story.append(Spacer(1, 10))

    # AI Investigative Summary Section
    story.append(Paragraph("AI Intelligence Assessment", h2_style))
    summary = investigation_data.get("ai_summary", {})
    sections = [
        ("1. What reportedly happened?", summary.get("what_reportedly_happened", "")),
        ("2. Supporting Evidence:", summary.get("supporting_evidence_summary", "")),
        ("3. Contradicting Evidence:", summary.get("contradicting_evidence_summary", "")),
        ("4. Official Sources Position:", summary.get("official_sources_position", "")),
        ("5. Key Uncertainties & Gaps:", summary.get("uncertainties_and_gaps", "")),
        ("6. Final Intelligence Conclusion:", summary.get("final_assessment", "")),
    ]
    for subtitle, text in sections:
        story.append(Paragraph(f"<b>{subtitle}</b>", body_style))
        story.append(Paragraph(text, body_style))
        story.append(Spacer(1, 4))

    # Collected Evidence Sources Table
    story.append(Spacer(1, 8))
    story.append(Paragraph("Evaluated Evidence Sources", h2_style))
    sources = investigation_data.get("sources", [])[:8]
    if sources:
        src_table_data = [["Publisher", "Category", "Rel. Weight", "Stance", "Title"]]
        for s in sources:
            src_table_data.append([
                s.get("publisher", "Web"),
                s.get("source_category", "Web")[:20],
                str(s.get("reliability_score", 0.5)),
                s.get("evidence_classification", "NEUTRAL"),
                Paragraph(s.get("title", "")[:45] + ("..." if len(s.get("title", "")) > 45 else ""), body_style)
            ])
        st = Table(src_table_data, colWidths=[80, 110, 60, 80, 210])
        st.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#FFFFFF')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(st)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
