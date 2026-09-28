import json
import os
import re

from conftest import ROOT

LANGS = json.load(open(os.path.join(ROOT, "data", "languages.json"), encoding="utf-8"))


def test_both_languages_have_the_same_keys():
    tr, en = LANGS["Türkçe"], LANGS["English"]
    assert set(tr) == set(en)
    assert set(tr["ui"]) == set(en["ui"])


def test_placeholders_match_between_languages():
    for key, en in LANGS["English"]["ui"].items():
        if isinstance(en, str):
            tr = LANGS["Türkçe"]["ui"][key]
            assert set(re.findall(r"{\w+}", en)) == set(re.findall(r"{\w+}", tr)), key


def test_english_labels_are_english():
    turkish_letters = set("çğışöüÇĞİŞÖÜ")
    for key, value in LANGS["English"]["ui"].items():
        text = " ".join(value) if isinstance(value, list) else value
        assert not turkish_letters & set(text), f"{key}: {text}"
