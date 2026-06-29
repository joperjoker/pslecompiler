"""Exercise the hardened paper parser on a generated PDF (text MCQ + image)."""
import pytest

fitz = pytest.importorskip("fitz")

from pslecompiler.paper_parse import (
    parse_paper_pdf, render_page_png, count_page_images,
)


def _make_pdf(path):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72),
                     "1. Which object is shown in the diagram below?")
    page.insert_text((72, 90), "(1) magnet (2) battery (3) bulb (4) switch")
    # embed a small image so the parser's image path triggers
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 40, 40))
    pix.clear_with(120)
    page.insert_image(fitz.Rect(72, 120, 152, 200), stream=pix.tobytes("png"))
    doc.save(path)
    doc.close()


def test_parse_pdf_with_image(tmp_path):
    pdf = tmp_path / "mock-paper.pdf"
    _make_pdf(str(pdf))

    assets = tmp_path / "assets"
    items = parse_paper_pdf(pdf, assets_dir=assets)
    assert items, "expected at least one parsed item"
    it = items[0]
    assert len(it.options) == 4
    # text block present, image block + asset attached
    assert any(b.type == "text" for b in it.blocks)
    assert it.assets and (assets / it.assets[0]).exists()


def test_render_and_image_count(tmp_path):
    pdf = tmp_path / "mock.pdf"
    _make_pdf(str(pdf))
    png = render_page_png(pdf, 1)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"  # PNG signature
    with fitz.open(pdf) as doc:
        assert count_page_images(doc[0]) >= 1
