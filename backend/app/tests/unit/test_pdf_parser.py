import pytest

from app.ingestion.pdf_parser import classify_heading, _clean_page_text, _strip_markdown
from app.db.enums import SectionType


@pytest.mark.parametrize(
    "heading,expected",
    [
        ("Abstract", SectionType.ABSTRACT),
        ("1 Introduction", SectionType.INTRODUCTION),
        ("2 Related Work", SectionType.RELATED_WORK),
        ("Background", SectionType.RELATED_WORK),
        ("3 Methodology", SectionType.METHODOLOGY),
        ("4 Proposed Approach", SectionType.METHODOLOGY),
        ("5 Experiments", SectionType.EXPERIMENTS),
        ("5.1 Experimental Setup", SectionType.EXPERIMENTS),
        ("6 Results", SectionType.RESULTS),
        ("Experimental Results", SectionType.RESULTS),
        ("7 Discussion", SectionType.DISCUSSION),
        ("8 Conclusion", SectionType.CONCLUSION),
        ("Conclusions", SectionType.CONCLUSION),
        ("Limitations", SectionType.LIMITATIONS),
        ("References", SectionType.REFERENCES),
        ("Bibliography", SectionType.REFERENCES),
        ("Acknowledgments", SectionType.OTHER),
    ],
)
def test_classify_heading(heading, expected):
    assert classify_heading(heading) == expected


def test_strip_markdown_removes_bold_and_numbering():
    # _strip_markdown operates on text already past the leading '#'s (HEADING_RE strips those).
    assert _strip_markdown("**3.1 Definition and Taxonomy**") == "Definition and Taxonomy"
    assert _strip_markdown("**Abstract**") == "Abstract"


def test_clean_page_text_removes_picture_captions():
    raw = "Intro text. <!-- Start of picture text -->garbled ocr noise<!-- End of picture text --> more text."
    cleaned = _clean_page_text(raw)
    assert "picture text" not in cleaned
    assert "garbled ocr noise" not in cleaned
    assert "Intro text." in cleaned
    assert "more text." in cleaned


def test_clean_page_text_strips_stray_html_tags():
    cleaned = _clean_page_text("line one<br>line two<sup>1</sup>")
    assert "<br>" not in cleaned
    assert "<sup>" not in cleaned
