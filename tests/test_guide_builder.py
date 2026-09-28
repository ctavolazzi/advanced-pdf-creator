import os
import re

import fitz  # pymupdf
import pytest

import guide_builder
from conftest import ROOT
from guide_builder import build_guide, parse_blocks, parse_inline, smarten, split_front_matter

GUIDE = os.path.join(ROOT, "guides", "claude-code-starter.md")

SAMPLE = """---
title: Test|guide
highlight: guide
subtitle: A subtitle
---

# Chapter one

Some **bold**, *italic*, `code` and [a link](https://example.com).

- a bullet
- another

1. first
2. second

- [ ] todo
- [x] done

> [!TIP] Title
> Inside the box.

```bash
$ echo hello
```

```prompt
Copy me.
```

| a | b |
|---|---|
| 1 | 2 |

<!-- pagebreak -->

## Heading two

### Heading three
"""


@pytest.fixture(scope="module")
def guide():
    with open(GUIDE, encoding="utf-8") as f:
        md = f.read()
    data, pages = build_guide(md, base_dir=os.path.dirname(GUIDE))
    return md, fitz.open(stream=data, filetype="pdf"), pages


def test_front_matter():
    meta, body = split_front_matter(SAMPLE)
    assert meta["title"] == "Test|guide"
    assert body.lstrip().startswith("# Chapter one")


def test_every_block_kind_is_parsed():
    kinds = [b.kind for b in parse_blocks(split_front_matter(SAMPLE)[1])]
    assert kinds == ["h1", "p", "ul", "ol", "check", "callout", "code", "code", "table", "pagebreak", "h2", "h3"]


def test_inline_runs():
    runs = parse_inline("Some **bold**, *italic*, `a b` and [link](https://x.y)")
    assert [(r.text.strip(" ,"), r.bold, r.italic, r.code, r.link) for r in runs if r.text.strip(" ,")] == [
        ("Some", False, False, False, None),
        ("bold", True, False, False, None),
        ("italic", False, True, False, None),
        ("a b", False, False, True, None),
        ("and", False, False, False, None),
        ("link", False, False, False, "https://x.y"),
    ]


def test_smart_quotes_leave_code_alone():
    runs = smarten(parse_inline('He said "don\'t" and ran `echo "hi"`'))
    assert runs[0].text == "He said “don’t” and ran "
    assert runs[1].text == 'echo "hi"'


def test_sample_builds():
    data, pages = build_guide(SAMPLE)
    assert data.startswith(b"%PDF") and pages >= 4


def test_builds_without_the_guide_fonts(monkeypatch, tmp_path):
    monkeypatch.setattr(guide_builder, "GUIDE_FONTS", str(tmp_path))
    data, pages = build_guide(SAMPLE)
    assert data.startswith(b"%PDF")


def test_contents_page_lists_every_chapter_with_its_page(guide):
    md, doc, pages = guide
    chapters = [line[2:].strip() for line in md.splitlines() if line.startswith("# ")]
    contents = doc[1].get_text()
    for number, title in enumerate(chapters, 1):
        assert title.replace("'", "’") in contents
        # the chapter's own page carries its "Part NN" kicker and title
        page_no = int(re.search(re.escape(title.replace("'", "’")) + r"\s*\n?\s*(\d\d)", contents).group(1))
        assert f"PART {number:02d}" in doc[page_no - 1].get_text()


def test_nothing_is_drawn_outside_the_margins(guide):
    _, doc, _ = guide
    for page in list(doc)[1:-1]:  # the cover and the back page bleed on purpose
        for block in page.get_text("dict")["blocks"]:
            x0, y0, x1, y1 = block["bbox"]
            assert x0 >= 30 and x1 <= page.rect.width - 30, (page.number + 1, block["bbox"])
            assert y1 <= page.rect.height - 20, (page.number + 1, block["bbox"])


def test_no_page_is_left_empty(guide):
    _, doc, _ = guide
    for page in doc:
        assert len(page.get_text().split()) > 12, page.number + 1


def test_every_link_in_the_markdown_is_clickable(guide):
    md, doc, _ = guide
    wanted = set(re.findall(r"\]\((https?://[^)]+)\)", md))
    found = {link["uri"] for page in doc for link in page.get_links() if link.get("uri")}
    assert wanted <= found


def test_guide_has_no_long_dashes():
    with open(GUIDE, encoding="utf-8") as f:
        text = f.read()
    assert chr(0x2014) not in text and chr(0x2013) not in text
