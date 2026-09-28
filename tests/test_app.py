"""The Streamlit app, driven headless with Streamlit's own AppTest."""
import json
import os

import pytest
from streamlit.testing.v1 import AppTest

from conftest import ROOT

APP = os.path.join(ROOT, "app.py")
EN = json.load(open(os.path.join(ROOT, "data", "languages.json"), encoding="utf-8"))["English"]
TURKISH_LETTERS = set("çğışöüÇĞİŞÖÜ")


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("PDF_CREATOR_DRAFTS", str(tmp_path / "drafts"))
    monkeypatch.chdir(tmp_path)  # anything written to the working folder would land here
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.sidebar.selectbox[0].select("English").run()
    return at


def open_page(at, title):
    at.sidebar.selectbox[1].select(title).run()
    return at


def labels(at):
    widgets = [*at.text_input, *at.text_area, *at.selectbox, *at.slider, *at.number_input, *at.button,
               *at.color_picker]
    return [w.label for w in widgets]


def test_english_means_every_control_is_english(app):
    open_page(app, EN["pdf_creator"])
    found = labels(app)
    assert EN["ui"]["create_pdf"] in found
    assert not [label for label in found if TURKISH_LETTERS & set(label) and "/" not in label]


def test_create_pdf_from_the_content_box(app, tmp_path):
    open_page(app, EN["pdf_creator"])
    app.text_area(key="pdf_content").input("The big content box now reaches the PDF.").run()
    next(b for b in app.button if b.label == EN["ui"]["create_pdf"]).click().run()
    assert [s.value for s in app.success] == [EN["ui"]["created"]]
    assert not (tmp_path / "output.pdf").exists()
    assert (tmp_path / "drafts" / "draft.txt").read_text(encoding="utf-8").startswith("The big content box")


def test_nothing_to_print_gives_a_warning(app):
    open_page(app, EN["pdf_creator"])
    next(b for b in app.button if b.label == EN["ui"]["create_pdf"]).click().run()
    assert [w.value for w in app.warning] == [EN["ui"]["need_text"]]
