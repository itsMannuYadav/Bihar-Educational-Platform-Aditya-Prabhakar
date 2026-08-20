import io

from pptx import Presentation as new_presentation
from pptx.presentation import Presentation
from pptx.util import Inches, Pt

# Deliberately large type: these decks get projected onto a wall or a low-end
# monitor in a government-school classroom, often from the back of the room
# (docs/07-roadmap.md Phase 6 — "large fonts, teacher-friendly layouts").
TITLE_SLIDE_TITLE_PT = 44
BODY_SLIDE_TITLE_PT = 32
BODY_TEXT_PT = 24

_TITLE_LAYOUT = 0
_TITLE_AND_CONTENT_LAYOUT = 1


class NativePptxProvider:
    """Renders the graph's provider-agnostic slide list into a real .pptx.

    Text is written as text, never as rasterized images, so PowerPoint (or
    LibreOffice, or Google Slides) does the script shaping — which is what
    makes Hindi decks render correctly without shipping fonts.
    """

    extension = "pptx"
    media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

    def render(self, *, title: str, slides: list[dict]) -> bytes:
        presentation = new_presentation()
        presentation.slide_width = Inches(13.333)  # 16:9
        presentation.slide_height = Inches(7.5)

        for index, slide_data in enumerate(slides):
            self._add_slide(presentation, slide_data, is_first=index == 0, deck_title=title)

        buffer = io.BytesIO()
        presentation.save(buffer)
        return buffer.getvalue()

    def _add_slide(
        self, presentation: Presentation, slide_data: dict, *, is_first: bool, deck_title: str
    ) -> None:
        layout_name = slide_data.get("layout", "bullets")
        heading = slide_data.get("title") or (deck_title if is_first else "")
        body: list[str] = slide_data.get("body") or []

        if layout_name == "title" or is_first:
            slide = presentation.slides.add_slide(presentation.slide_layouts[_TITLE_LAYOUT])
            slide.shapes.title.text = heading
            slide.shapes.title.text_frame.paragraphs[0].runs[0].font.size = Pt(TITLE_SLIDE_TITLE_PT)
            if len(slide.placeholders) > 1 and body:
                subtitle = slide.placeholders[1]
                subtitle.text = body[0]
                subtitle.text_frame.paragraphs[0].runs[0].font.size = Pt(BODY_TEXT_PT)
        else:
            slide = presentation.slides.add_slide(
                presentation.slide_layouts[_TITLE_AND_CONTENT_LAYOUT]
            )
            slide.shapes.title.text = heading
            slide.shapes.title.text_frame.paragraphs[0].runs[0].font.size = Pt(BODY_SLIDE_TITLE_PT)

            text_frame = slide.placeholders[1].text_frame
            text_frame.word_wrap = True
            for i, line in enumerate(body or [""]):
                paragraph = text_frame.paragraphs[0] if i == 0 else text_frame.add_paragraph()
                paragraph.text = line
                for run in paragraph.runs:
                    run.font.size = Pt(BODY_TEXT_PT)

        # Speaker notes carry what the teacher actually says — the whole point
        # of generating a deck for someone teaching from it, not presenting it.
        if notes := slide_data.get("speaker_notes"):
            slide.notes_slide.notes_text_frame.text = notes
