"""
PDF export service.

Generates downloadable PDFs for a paper's summary, study notes, or flashcards
using reportlab (no external binaries required).
"""
from __future__ import annotations

import io
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.note import StudyNote
from app.models.paper import Paper

styles = getSampleStyleSheet()
TITLE_STYLE = ParagraphStyle("TitleStyle", parent=styles["Title"], textColor=colors.HexColor("#1e293b"))
HEADING_STYLE = ParagraphStyle(
    "HeadingStyle", parent=styles["Heading2"], textColor=colors.HexColor("#4338ca"), spaceBefore=14
)
BODY_STYLE = ParagraphStyle("BodyStyle", parent=styles["BodyText"], leading=16)


def _doc(buffer: io.BytesIO) -> SimpleDocTemplate:
    return SimpleDocTemplate(
        buffer, pagesize=LETTER, topMargin=0.75 * inch, bottomMargin=0.75 * inch,
        leftMargin=0.85 * inch, rightMargin=0.85 * inch,
    )


def _bullet_list(items: List[str]) -> ListFlowable:
    return ListFlowable(
        [ListItem(Paragraph(item, BODY_STYLE)) for item in items],
        bulletType="bullet",
        leftIndent=18,
    )


def generate_summary_pdf(paper: Paper) -> bytes:
    buffer = io.BytesIO()
    doc = _doc(buffer)
    story = [
        Paragraph(paper.title or paper.original_filename, TITLE_STYLE),
        Spacer(1, 12),
    ]

    def section(title: str, content: str | None):
        if content:
            story.append(Paragraph(title, HEADING_STYLE))
            story.append(Paragraph(content.replace("\n", "<br/>"), BODY_STYLE))

    section("Executive Summary", paper.executive_summary)
    section("Abstract Summary", paper.abstract_summary)

    if paper.key_contributions:
        story.append(Paragraph("Key Contributions", HEADING_STYLE))
        story.append(_bullet_list(paper.key_contributions))

    section("Methodology", paper.methodology)
    section("Results", paper.results)
    section("Limitations", paper.limitations)
    section("Future Work", paper.future_work)

    if paper.keywords:
        story.append(Paragraph("Keywords", HEADING_STYLE))
        story.append(Paragraph(", ".join(paper.keywords), BODY_STYLE))

    if paper.important_equations:
        story.append(Paragraph("Important Equations", HEADING_STYLE))
        story.append(_bullet_list(paper.important_equations))

    if paper.important_figures:
        story.append(Paragraph("Important Figures", HEADING_STYLE))
        story.append(_bullet_list(paper.important_figures))

    story.append(Paragraph("Reference Count", HEADING_STYLE))
    story.append(Paragraph(str(paper.references_count), BODY_STYLE))

    doc.build(story)
    return buffer.getvalue()


def generate_study_notes_pdf(paper: Paper, notes: StudyNote) -> bytes:
    buffer = io.BytesIO()
    doc = _doc(buffer)
    story = [Paragraph(f"Study Notes — {paper.title or paper.original_filename}", TITLE_STYLE), Spacer(1, 12)]

    if notes.exam_notes:
        story.append(Paragraph("Exam Notes", HEADING_STYLE))
        story.append(_bullet_list(notes.exam_notes))

    if notes.bullet_notes:
        story.append(Paragraph("Bullet Notes", HEADING_STYLE))
        story.append(_bullet_list(notes.bullet_notes))

    if notes.interview_questions:
        story.append(Paragraph("Interview Questions", HEADING_STYLE))
        story.append(_bullet_list(notes.interview_questions))

    if notes.viva_questions:
        story.append(Paragraph("Viva Questions", HEADING_STYLE))
        story.append(_bullet_list(notes.viva_questions))

    if notes.mcqs:
        story.append(Paragraph("MCQs", HEADING_STYLE))
        for i, mcq in enumerate(notes.mcqs, start=1):
            story.append(Paragraph(f"{i}. {mcq['question']}", BODY_STYLE))
            opts = mcq.get("options", [])
            correct_idx = mcq.get("correct_answer_index", 0)
            for j, opt in enumerate(opts):
                marker = "&#10003;" if j == correct_idx else "&#8226;"
                story.append(Paragraph(f"&nbsp;&nbsp;{marker} {opt}", BODY_STYLE))
            story.append(Spacer(1, 6))

    doc.build(story)
    return buffer.getvalue()


def generate_flashcards_pdf(paper: Paper, notes: StudyNote) -> bytes:
    buffer = io.BytesIO()
    doc = _doc(buffer)
    story = [Paragraph(f"Flashcards — {paper.title or paper.original_filename}", TITLE_STYLE), Spacer(1, 12)]

    flashcards = notes.flashcards or []
    table_data = [["#", "Question", "Answer"]]
    for i, card in enumerate(flashcards, start=1):
        table_data.append([str(i), Paragraph(card["question"], BODY_STYLE), Paragraph(card["answer"], BODY_STYLE)])

    if len(table_data) > 1:
        table = Table(table_data, colWidths=[0.4 * inch, 2.6 * inch, 2.6 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4338ca")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                ]
            )
        )
        story.append(table)

    doc.build(story)
    return buffer.getvalue()
