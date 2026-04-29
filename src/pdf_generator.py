import markdown
import uuid
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet
from bs4 import BeautifulSoup


def generate_pdf(report: str) -> str:
    html = markdown.markdown(report)
    soup = BeautifulSoup(html, "html.parser")

    file_path = f"report_{uuid.uuid4().hex}.pdf"
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(file_path)
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

    doc.build(story)
    return file_path