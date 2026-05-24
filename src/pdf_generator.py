import markdown
import uuid
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet
from bs4 import BeautifulSoup
import asyncio
from utils.loggers import logger

async def generate_pdf(report: str) -> str:
    logger.info("Starting PDF generation...")

    if not report or not report.strip():
        raise ValueError("Report content is empty. Cannot generate PDF.")
    
    try:

        html = markdown.markdown(report)
        soup = BeautifulSoup(html, "html.parser")

        output_dir = Path("pdfs")    
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = output_dir / f"report_{uuid.uuid4().hex}.pdf"
        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(str(file_path))
        story = []

        for element in soup.contents:
            if element.name == "h1":
                story.append(Paragraph(element.text, styles["Heading1"]))
            elif element.name == "h2":
                story.append(Paragraph(element.text, styles["Heading2"]))
            elif element.name == "h3":
                story.append(Paragraph(element.text, styles["Heading3"]))
            elif element.name == "p":
                story.append(Paragraph(element.decode_contents(), styles["Normal"]))
            elif element.name == "ul":
                items = [
                    ListItem(Paragraph(li.decode_contents(), styles["Normal"]))
                    for li in element.find_all("li")
                ]
                story.append(ListFlowable(items, bulletType="bullet"))

            story.append(Spacer(1, 12))

        await asyncio.to_thread(doc.build, story)
        logger.info(f"PDF generation completed successfully. File saved as {file_path}")
        return str(file_path)
    
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        raise RuntimeError(f"Failed to generate PDF: {e}")
