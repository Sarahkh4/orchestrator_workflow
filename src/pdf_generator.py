import asyncio
import html
import re
import uuid
from pathlib import Path
import markdown
from bs4 import BeautifulSoup, NavigableString, Tag
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer

from utils.loggers import logger


SUPPORTED_MARKDOWN_EXTENSIONS = ["extra", "sane_lists"]


def _normalize_inline_html(value: str) -> str:
    """Convert markdown HTML into the smaller inline tag set ReportLab supports."""
    value = re.sub(r"<(/?)strong\b[^>]*>", r"<\1b>", value)
    value = re.sub(r"<(/?)em\b[^>]*>", r"<\1i>", value)
    value = re.sub(r"<code\b[^>]*>(.*?)</code>", r"<font face=\"Courier\">\1</font>", value, flags=re.DOTALL)
    value = re.sub(r"<a\s+href=\"([^\"]+)\"[^>]*>", r'<link href="\1" color="blue">', value)
    value = value.replace("</a>", "</link>")
    return value


def _paragraph_from_node(node: Tag, style) -> Paragraph:
    content = _normalize_inline_html(node.decode_contents())
    return Paragraph(content, style)


def _text_paragraph(text: str, style) -> Paragraph | None:
    clean_text = text.strip()
    if not clean_text:
        return None

    return Paragraph(html.escape(clean_text), style)


def _list_item_flowables(li: Tag, styles, depth: int) -> list:
    flowables = []
    inline_parts = []

    for child in li.children:
        if isinstance(child, NavigableString):
            inline_parts.append(html.escape(str(child)))
            continue

        if not isinstance(child, Tag):
            continue

        if child.name in {"ul", "ol"}:
            text = "".join(inline_parts).strip()
            if text:
                flowables.append(Paragraph(_normalize_inline_html(text), styles["Normal"]))
                inline_parts = []
            flowables.extend(_flowables_from_node(child, styles, depth + 1))
        elif child.name == "p":
            text = "".join(inline_parts).strip()
            if text:
                flowables.append(Paragraph(_normalize_inline_html(text), styles["Normal"]))
                inline_parts = []
            flowables.append(_paragraph_from_node(child, styles["Normal"]))
        else:
            inline_parts.append(_normalize_inline_html(str(child)))

    text = "".join(inline_parts).strip()
    if text:
        flowables.insert(0, Paragraph(_normalize_inline_html(text), styles["Normal"]))

    return flowables or [Paragraph("", styles["Normal"])]


def _build_list(node: Tag, styles, depth: int = 0) -> ListFlowable:
    bullet_type = "1" if node.name == "ol" else "bullet"
    left_indent = 18 + (depth * 14)
    items = []

    for li in node.find_all("li", recursive=False):
        item_flowables = _list_item_flowables(li, styles, depth)
        items.append(
            ListItem(
                item_flowables,
                leftIndent=left_indent,
                bulletColor=colors.HexColor("#334155"),
            )
        )

    return ListFlowable(
        items,
        bulletType=bullet_type,
        leftIndent=left_indent,
        bulletFontName="Helvetica",
        bulletFontSize=9,
        bulletColor=colors.HexColor("#334155"),
    )


def _flowables_from_node(node: Tag, styles, depth: int = 0) -> list:
    if node.name == "h1":
        return [Paragraph(node.get_text(" ", strip=True), styles["Heading1"]), Spacer(1, 8)]
    if node.name == "h2":
        return [Paragraph(node.get_text(" ", strip=True), styles["Heading2"]), Spacer(1, 6)]
    if node.name == "h3":
        return [Paragraph(node.get_text(" ", strip=True), styles["Heading3"]), Spacer(1, 4)]
    if node.name == "p":
        return [_paragraph_from_node(node, styles["Normal"]), Spacer(1, 8)]
    if node.name in {"ul", "ol"}:
        return [_build_list(node, styles, depth), Spacer(1, 8)]
    if node.name == "hr":
        return [
            Spacer(1, 8),
            HRFlowable(width="100%", thickness=0.7, color=colors.HexColor("#CBD5E1"), spaceBefore=4, spaceAfter=10),
        ]
    if node.name == "blockquote":
        return [_paragraph_from_node(node, styles["BodyText"]), Spacer(1, 8)]

    flowables = []
    for child in node.children:
        flowables.extend(_flowables_from_child(child, styles, depth))
    return flowables


def _flowables_from_child(child, styles, depth: int = 0) -> list:
    if isinstance(child, NavigableString):
        paragraph = _text_paragraph(str(child), styles["Normal"])
        return [paragraph, Spacer(1, 8)] if paragraph else []

    if isinstance(child, Tag):
        return _flowables_from_node(child, styles, depth)

    return []


async def generate_pdf(report: str) -> str:
    logger.info("Starting PDF generation...")

    if not report or not report.strip():
        raise ValueError("Report content is empty. Cannot generate PDF.")

    try:
        html_report = markdown.markdown(report, extensions=SUPPORTED_MARKDOWN_EXTENSIONS)
        soup = BeautifulSoup(html_report, "html.parser")

        output_dir = Path("pdfs")
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = output_dir / f"report_{uuid.uuid4().hex}.pdf"

        styles = getSampleStyleSheet()
        styles["Heading1"].spaceBefore = 10
        styles["Heading1"].spaceAfter = 10
        styles["Heading2"].spaceBefore = 12
        styles["Heading2"].spaceAfter = 8
        styles["Heading3"].spaceBefore = 10
        styles["Heading3"].spaceAfter = 6
        styles["Normal"].fontSize = 10
        styles["Normal"].leading = 14
        styles["Normal"].spaceAfter = 4

        doc = SimpleDocTemplate(
            str(file_path),
            leftMargin=0.65 * inch,
            rightMargin=0.65 * inch,
            topMargin=0.65 * inch,
            bottomMargin=0.65 * inch,
        )

        story = []
        for child in soup.children:
            story.extend(_flowables_from_child(child, styles))

        await asyncio.to_thread(doc.build, story)
        logger.info("PDF generation completed successfully. File saved as %s", file_path)
        return str(file_path)

    except Exception as e:
        logger.error("Failed to generate PDF: %s", e)
        raise RuntimeError(f"Failed to generate PDF: {e}")
