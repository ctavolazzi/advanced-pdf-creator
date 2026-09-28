"""Markdown in, a designed PDF guide out.

A cover, a contents page, numbered chapters, callouts, prompt cards, code blocks,
checklists and tables, on A5 pages so the result reads well on a phone and still prints.

    python guide_builder.py guides/claude-code-starter.md -o guides/claude-code-starter-guide.pdf

It is built on fpdf2 with a small text layout of its own (bold, italic, `code` and links
inside a line, measured before anything is drawn), so every box is sized to what is in it
and never split across two pages.

The Markdown it reads:

    ---
    title: My guide           front matter. Also: subtitle, author, date, version, kicker,
    subtitle: ...             highlight (words of the title to mark), promises (a | b | c),
    ---                       footer, end_title, end_text, end_link

    # Chapter                 starts a page, gets a number and a line in the contents
    ## Heading and ### Subheading
    Paragraphs with **bold**, *italic*, `code` and [links](https://example.com).
    - bullets, 1. numbered steps, - [ ] checklist items
    > [!TIP] Optional title   also [!NOTE], [!WARNING] and [!TRY]; the body can hold lists
    ```bash                   a code block; ```prompt makes a prompt card to copy
    | a | b |                 a table, first row is the header
    ![alt](path/to/image.png)
    <!-- pagebreak -->
"""
import argparse
import os
import re
from dataclasses import dataclass, field

from fpdf import FPDF

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
GUIDE_FONTS = os.path.join(FONTS, "guide")

PT = 0.3528  # millimetres in a point

# The channel's palette: the ink, paper and highlighter yellow of the video graphics.
THEME = {
    "ink": (13, 15, 20),
    "ink2": (23, 26, 34),
    "screen": (32, 36, 47),
    "paper": (247, 244, 234),
    "page": (252, 251, 247),
    "text": (28, 31, 38),
    "muted": (104, 110, 122),
    "soft": (179, 185, 198),
    "accent": (255, 210, 63),
    "link": (11, 110, 138),
    "code_ink": (154, 52, 18),
    "code_bg": (240, 236, 224),
    "rule": (222, 218, 206),
    "row": (243, 241, 234),
}

# Callout kinds: (bar colour, background, label colour, label)
CALLOUTS = {
    "tip": ((255, 210, 63), (255, 247, 214), (13, 15, 20), "Tip"),
    "note": ((69, 212, 230), (226, 246, 249), (8, 102, 120), "Note"),
    "warning": ((255, 84, 104), (255, 233, 236), (176, 24, 52), "Heads up"),
    "try": ((13, 15, 20), (237, 235, 227), (13, 15, 20), "Try this"),
}

# Page sizes in millimetres. fpdf2 changed its A5 numbers in 2.8.5, so they are spelled out.
PAGE_SIZES = {"A5": (148, 210), "A4": (210, 297), "LETTER": (215.9, 279.4)}

FONT_FILES = {
    ("Inter", ""): "Inter-Regular.ttf",
    ("Inter", "B"): "Inter-Bold.ttf",
    ("Inter", "I"): "Inter-Italic.ttf",
    ("Inter", "BI"): "Inter-BoldItalic.ttf",
    ("Grotesk", ""): "SpaceGrotesk-Medium.ttf",
    ("Grotesk", "B"): "SpaceGrotesk-Bold.ttf",
    ("Mono", ""): "JetBrainsMono-Regular.ttf",
    ("Mono", "B"): "JetBrainsMono-Bold.ttf",
    ("Pixel", ""): "Silkscreen-Regular.ttf",
}


# ---------------------------------------------------------------- parsing

@dataclass
class Block:
    kind: str
    text: str = ""
    items: list = field(default_factory=list)
    meta: dict = field(default_factory=dict)
    children: list = field(default_factory=list)


@dataclass
class Run:
    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False
    link: str = None


def split_front_matter(md):
    """Returns (meta, body). Meta is the `key: value` block between two --- lines at the top."""
    lines = md.splitlines()
    if lines and lines[0].strip() == "---":
        for end in range(1, len(lines)):
            if lines[end].strip() == "---":
                meta = {}
                for line in lines[1:end]:
                    if ":" in line:
                        key, value = line.split(":", 1)
                        meta[key.strip().lower()] = value.strip()
                return meta, "\n".join(lines[end + 1:])
    return {}, md


LIST_RE = re.compile(r"^(\s*)([-*]|\d+[.)])\s+(.*)$")
CHECK_RE = re.compile(r"^\[( |x|X)\]\s+(.*)$")


def parse_blocks(md):
    lines = md.splitlines()
    blocks, para, i = [], [], 0

    def flush():
        if para:
            blocks.append(Block("p", " ".join(s.strip() for s in para)))
            para.clear()

    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            flush()
            i += 1
        elif s == "<!-- pagebreak -->":
            flush()
            blocks.append(Block("pagebreak"))
            i += 1
        elif s.startswith("<!--"):
            flush()
            while i < len(lines) and "-->" not in lines[i]:
                i += 1
            i += 1
        elif s.startswith("```"):
            flush()
            lang, body = s[3:].strip().lower(), []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                body.append(lines[i].rstrip())
                i += 1
            i += 1
            blocks.append(Block("code", "\n".join(body), meta={"lang": lang}))
        elif re.match(r"^#{1,3}\s", s):
            flush()
            hashes, title = s.split(None, 1)
            blocks.append(Block(f"h{len(hashes)}", title.strip()))
            i += 1
        elif re.match(r"^(-{3,}|\*{3,})$", s):
            flush()
            blocks.append(Block("hr"))
            i += 1
        elif s.startswith(">"):
            flush()
            inner = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                inner.append(re.sub(r"^\s*> ?", "", lines[i]))
                i += 1
            kind, title = "note", ""
            m = re.match(r"^\[!(\w+)\]\s*(.*)$", inner[0].strip()) if inner else None
            if m:
                kind, title, inner = m.group(1).lower(), m.group(2).strip(), inner[1:]
            blocks.append(Block("callout", meta={"kind": kind if kind in CALLOUTS else "note", "title": title},
                                children=parse_blocks("\n".join(inner))))
        elif s.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            body = [r for r in rows[1:] if not all(re.match(r"^:?-+:?$", c) for c in r)]
            blocks.append(Block("table", items=body, meta={"header": rows[0]}))
        elif re.match(r"^!\[[^\]]*\]\([^)]+\)$", s):
            flush()
            alt, path = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", s).groups()
            blocks.append(Block("image", alt, meta={"path": path}))
            i += 1
        elif LIST_RE.match(line):
            flush()
            ordered = LIST_RE.match(line).group(2)[0].isdigit()
            items = []
            while i < len(lines):
                m = LIST_RE.match(lines[i])
                if m and m.group(2)[0].isdigit() == ordered:
                    items.append(m.group(3).strip())
                elif items and lines[i].startswith("  ") and lines[i].strip():
                    items[-1] += " " + lines[i].strip()  # a wrapped item
                else:
                    break
                i += 1
            checks = [CHECK_RE.match(t) for t in items]
            if not ordered and all(checks):
                blocks.append(Block("check", items=[c.group(2) for c in checks],
                                    meta={"done": [c.group(1) != " " for c in checks]}))
            else:
                blocks.append(Block("ol" if ordered else "ul", items=items))
        else:
            para.append(line)
            i += 1
    flush()
    return blocks


INLINE = re.compile(
    r"`([^`]+)`"                                   # `code`
    r"|\*\*(.+?)\*\*"                               # **bold**
    r"|(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])"   # *italic*
    r"|\[([^\]]+)\]\(([^)\s]+)\)"                   # [text](url)
)


def parse_inline(text, bold=False, italic=False, link=None):
    runs, pos = [], 0
    for m in INLINE.finditer(text):
        if m.start() > pos:
            runs.append(Run(text[pos:m.start()], bold, italic, False, link))
        code, strong, em, label, url = m.groups()
        if code is not None:
            runs.append(Run(code, bold, italic, True, link))
        elif strong is not None:
            runs.extend(parse_inline(strong, True, italic, link))
        elif em is not None:
            runs.extend(parse_inline(em, bold, True, link))
        else:
            runs.extend(parse_inline(label, bold, italic, url))
        pos = m.end()
    if pos < len(text):
        runs.append(Run(text[pos:], bold, italic, False, link))
    return runs


def smarten(runs):
    """Straight quotes to curly ones, outside code: "a" -> “a”, don't -> don’t."""
    prev = " "
    for run in runs:
        if run.code:
            prev = run.text[-1:] or prev
            continue
        out = []
        for ch in run.text:
            opening = prev.isspace() or prev in "([{/"
            if ch == '"':
                ch = "“" if opening else "”"
            elif ch == "'":
                ch = "‘" if opening else "’"
            out.append(ch)
            prev = ch
        run.text = "".join(out)
    return runs


def plain(text):
    """Inline Markdown stripped to its words, for bookmarks and the contents page."""
    return "".join(r.text for r in smarten(parse_inline(text)))


# ---------------------------------------------------------------- the document

class GuidePDF(FPDF):
    def __init__(self, meta, page_size="A5", theme=None):
        size = PAGE_SIZES.get(str(page_size).upper(), page_size)
        super().__init__(orientation="P", unit="mm", format=size)
        self.meta = meta
        self.t = dict(THEME, **(theme or {}))
        self.set_margins(14, 16, 14)
        self.bottom = 19
        self.set_auto_page_break(False)  # this layout places every line itself
        self._load_fonts()
        self.chapters = 0
        self.plain_pages = set()  # cover and back page: no footer
        # Text styles: font family, style, size (pt), line height (mm), colour
        self.body = {"family": "Inter", "style": "", "size": 10.5, "lh": 5.5, "color": self.t["text"]}
        self.small = dict(self.body, size=9.2, lh=4.7)
        self.set_title(plain(meta.get("title", "Guide")))
        self.set_author(meta.get("author", ""))
        self.set_subject(meta.get("subtitle", ""))
        self.set_creator("advanced-pdf-creator guide_builder.py")
        self.set_lang(meta.get("lang", "en"))
        self.set_display_mode(zoom="fullwidth", layout="single")

    # ------------------------------------------------------------ fonts and text

    def _load_fonts(self):
        if all(os.path.exists(os.path.join(GUIDE_FONTS, f)) for f in FONT_FILES.values()):
            for (family, style), name in FONT_FILES.items():
                self.add_font(family, style, os.path.join(GUIDE_FONTS, name))
            return
        # Without fonts/guide, everything falls back to the DejaVu the app ships with.
        dejavu = {"": "DejaVuSans.ttf", "B": "dejavu-sans-bold.ttf", "I": "DejaVuSans-Oblique.ttf",
                  "BI": "dejavu-sans-bold.ttf"}
        for family in ("Inter", "Grotesk", "Mono", "Pixel"):
            for style, name in dejavu.items():
                self.add_font(family, style, os.path.join(FONTS, name))

    @property
    def text_w(self):
        return self.w - self.l_margin - self.r_margin

    @property
    def limit(self):
        return self.h - self.bottom

    def _font(self, run, base):
        if run.code:
            return ("Mono", "", base["size"] * 0.88)
        if base["family"] == "Inter":
            style = ("B" if run.bold or "B" in base["style"] else "") + ("I" if run.italic else "")
            return ("Inter", style, base["size"])
        return (base["family"], base["style"], base["size"])

    def layout(self, runs, width, base):
        """Breaks runs into lines at spaces. A line is a list of (x, text, run, font, width)."""
        groups, cur, pending = [], None, False
        runs = smarten([Run(r.text, r.bold, r.italic, r.code, r.link) for r in runs])
        for run in runs:
            text = run.text.replace(" ", " ") if run.code else run.text
            for piece in re.split(r"( +)", text):
                if not piece:
                    continue
                if piece.startswith(" "):
                    if cur:
                        groups.append(cur)
                        cur = None
                    pending = True
                    continue
                if cur is None:
                    cur = {"space": pending, "parts": []}
                    pending = False
                font = self._font(run, base)
                self.set_font(*font)
                cur["parts"].append((piece, run, font, self.get_string_width(piece)))
        if cur:
            groups.append(cur)

        self.set_font(base["family"], base["style"], base["size"])
        space = self.get_string_width(" ")
        lines, line, x = [], [], 0.0
        for g in groups:
            parts = g["parts"]
            gw = sum(p[3] for p in parts)
            gap = space if g["space"] and line else 0.0
            if line and x + gap + gw > width + 0.01:
                lines.append(line)
                line, x, gap = [], 0.0, 0.0
            if gw > width:  # a word longer than the line, such as a long link: split it
                parts = self._split_long(parts, width - x - gap)
            for piece, run, font, w in parts:
                if piece == "\n":
                    lines.append(line)
                    line, x, gap = [], 0.0, 0.0
                    continue
                line.append((x + gap, piece, run, font, w))
                x += gap + w
                gap = 0.0
        if line:
            lines.append(line)
        return lines

    def _split_long(self, parts, first_width):
        out, room = [], first_width
        for piece, run, font, _ in parts:
            self.set_font(*font)
            chunk = ""
            for ch in piece:
                if chunk and self.get_string_width(chunk + ch) > room:
                    out.append((chunk, run, font, self.get_string_width(chunk)))
                    out.append(("\n", run, font, 0))
                    chunk, room = "", self.text_w
                chunk += ch
            if chunk:
                w = self.get_string_width(chunk)
                out.append((chunk, run, font, w))
                room -= w
        return out

    def draw_line(self, line, x0, top, base):
        size = base["size"] * PT
        baseline = top + base["lh"] * 0.5 + size * 0.36
        for x, piece, run, font, w in line:
            self.set_font(*font)
            x += x0
            color = base["color"]
            if run.code:
                self.set_fill_color(*base.get("code_bg", self.t["code_bg"]))
                self.rect(x - 0.6, baseline - size * 0.82, w + 1.2, size * 1.14, "F",
                          round_corners=True, corner_radius=0.8)
                color = base.get("code_color", self.t["code_ink"])
            elif run.link:
                color = base.get("link_color", self.t["link"])
            self.set_text_color(*color)
            self.text(x, baseline, piece.replace(" ", " "))
            if run.link:
                self.set_draw_color(*color)
                self.set_line_width(0.2)
                self.line(x, baseline + 0.9, x + w, baseline + 0.9)
                self.link(x, top, w, base["lh"], run.link)

    def lines_height(self, lines, base):
        return len(lines) * base["lh"]

    def flow(self, lines, x, base, breaks=True):
        """Draws lines from the current y, starting a new page when one does not fit.
        A page break never leaves a single line of a paragraph on either side of it."""
        if breaks:
            room = int((self.limit - self.y) // base["lh"])
            if room < len(lines):
                if room < 2 or len(lines) <= 3:
                    self.new_page()
                elif len(lines) - room < 2:
                    lines = list(lines)
                    head, tail = lines[:room - 1], lines[room - 1:]
                    self._draw_lines(head, x, base)
                    self.new_page()
                    lines = tail
        self._draw_lines(lines, x, base, breaks)

    def _draw_lines(self, lines, x, base, breaks=False):
        for line in lines:
            if breaks and self.y + base["lh"] > self.limit:
                self.new_page()
            self.draw_line(line, x, self.y, base)
            self.y += base["lh"]

    def new_page(self):
        self.add_page()
        self.set_y(self.t_margin)

    def fits(self, height):
        return self.y + height <= self.limit

    def at_top(self):
        return self.y <= self.t_margin + 0.5

    def pixel_label(self, x, y, text, color, size=6.6):
        self.set_font("Pixel", "", size)
        self.set_text_color(*color)
        self.text(x, y, text.upper())
        return self.get_string_width(text.upper())

    # ------------------------------------------------------------ page furniture

    def footer(self):
        if self.page in self.plain_pages:
            return
        y = self.h - 10
        self.set_draw_color(*self.t["rule"])
        self.set_line_width(0.2)
        self.line(self.l_margin, y - 4.2, self.w - self.r_margin, y - 4.2)
        self.set_font("Inter", "", 7)
        self.set_text_color(*self.t["muted"])
        self.text(self.l_margin, y, self.meta.get("footer", plain(self.meta.get("title", ""))))
        label = f"{self.page:02d}"
        self.set_font("Pixel", "", 7)
        self.text(self.w - self.r_margin - self.get_string_width(label), y, label)

    def cover(self):
        m, t = self.meta, self.t
        self.add_page()
        self.plain_pages.add(self.page)
        self.set_fill_color(*t["ink"])
        self.rect(0, 0, self.w, self.h, "F")
        x = self.l_margin
        # a strip of pixels along the top, like the video's lower thirds
        for k in range(24):
            shade = t["accent"] if k % 5 == 0 else t["screen"]
            self.set_fill_color(*shade)
            self.rect(x + k * 5.0, 10, 3.2, 3.2, "F")

        kicker = m.get("kicker", "Free guide").upper()
        self.set_font("Pixel", "", 8)
        kw = self.get_string_width(kicker)
        self.set_fill_color(*t["accent"])
        self.rect(x, 20, kw + 7, 7, "F", round_corners=True, corner_radius=1.2)
        self.pixel_label(x + 3.5, 25.1, kicker, t["ink"], 8)

        # Title: highlighted words get the yellow marker box, like the video titles.
        marked = {w.lower() for w in m.get("highlight", "").split()}
        title_base = {"family": "Grotesk", "style": "B", "size": 29, "lh": 12.2, "color": t["paper"]}
        y = 36
        for text_line in m.get("title", "Guide").split("|"):
            words = text_line.split()
            self.set_font("Grotesk", "B", 29)
            cx = x
            for word in words:
                w = self.get_string_width(word)
                if word.lower().strip(",.!?:") in marked:
                    self.set_fill_color(*t["accent"])
                    self.rect(cx - 1.2, y + 1.2, w + 2.4, title_base["lh"] - 1.6, "F")
                    self.set_text_color(*t["ink"])
                else:
                    self.set_text_color(*t["paper"])
                self.text(cx, y + title_base["lh"] * 0.5 + 29 * PT * 0.36, word)
                cx += w + self.get_string_width(" ")
            y += title_base["lh"]

        sub = {"family": "Inter", "style": "", "size": 11, "lh": 5.6, "color": t["soft"]}
        self.set_y(y + 4)
        self.flow(self.layout(parse_inline(m.get("subtitle", "")), self.text_w - 8, sub), x, sub, breaks=False)

        # promises on the left, a phone on the right
        py = 112
        promise = {"family": "Inter", "style": "B", "size": 9.4, "lh": 4.8, "color": t["paper"]}
        for item in [p.strip() for p in m.get("promises", "").split("|") if p.strip()]:
            self.set_fill_color(*t["accent"])
            self.rect(x, py + 1.5, 2.2, 2.2, "F")
            lines = self.layout(parse_inline(item), 50, promise)
            self.set_y(py)
            self.flow(lines, x + 5, promise, breaks=False)
            py = self.y + 4
        self.phone(84, 100)

        self.set_font("Inter", "B", 10)
        self.set_text_color(*t["paper"])
        self.text(x, self.h - 22, m.get("author", ""))
        self.set_font("Inter", "", 8)
        self.set_text_color(*t["soft"])
        edition = "  ·  ".join(v for v in (m.get("version", ""), m.get("date", "")) if v)
        self.text(x, self.h - 16.5, edition)

    def phone(self, x, y):
        """A phone with a Claude Code session on it, drawn in vectors."""
        t = self.t
        w, h = 50, 94
        self.set_fill_color(*t["ink2"])
        self.set_draw_color(70, 76, 92)
        self.set_line_width(0.7)
        self.rect(x, y, w, h, "DF", round_corners=True, corner_radius=7)
        self.set_fill_color(*t["screen"])
        self.rect(x + 3, y + 3, w - 6, h - 6, "F", round_corners=True, corner_radius=5)
        self.set_fill_color(*t["ink"])
        self.rect(x + w / 2 - 7, y + 5, 14, 3.4, "F", round_corners=True, corner_radius=1.7)
        # the Code tab
        self.pixel_label(x + 6.5, y + 14.5, "Code", t["accent"], 5.6)
        self.set_draw_color(58, 64, 80)
        self.set_line_width(0.3)
        self.line(x + 6, y + 17, x + w - 6, y + 17)
        # your message, right aligned
        bubble = {"family": "Inter", "style": "", "size": 6.2, "lh": 3.1, "color": t["ink"]}
        lines = self.layout(parse_inline("Fix the preview bug and open a pull request"), 27, bubble)
        bh = len(lines) * bubble["lh"] + 3.4
        self.set_fill_color(*t["accent"])
        self.rect(x + w - 6 - 31, y + 21, 31, bh, "F", round_corners=True, corner_radius=2.2)
        self.set_y(y + 22.7)
        self.flow(lines, x + w - 6 - 29, bubble, breaks=False)
        # Claude's reply, drawn as text lines
        ry = y + 21 + bh + 4
        self.set_fill_color(48, 54, 69)
        self.rect(x + 6, ry, 32, 17, "F", round_corners=True, corner_radius=2.2)
        self.set_fill_color(120, 128, 146)
        for k, lw in enumerate((24, 19, 26, 14)):
            self.rect(x + 9, ry + 3 + k * 3.2, lw, 1.3, "F", round_corners=True, corner_radius=0.6)
        # a terminal line and the pull request it ends with
        ty = ry + 22
        self.set_font("Mono", "", 6)
        self.set_text_color(*t["accent"])
        self.text(x + 7, ty + 2, "$ pytest")
        self.set_text_color(*t["soft"])
        self.text(x + 7, ty + 6, "12 passed")
        self.set_fill_color(69, 212, 230)
        self.rect(x + 6, ty + 10, 38, 7.5, "F", round_corners=True, corner_radius=2)
        self.pixel_label(x + 9, ty + 15, "PR ready", t["ink"], 5.6)
        self.set_fill_color(*t["ink"])
        self.circle(x + 39.5, ty + 13.75, 2, "F")
        self.set_draw_color(69, 212, 230)
        self.set_line_width(0.5)
        self.line(x + 38.6, ty + 13.8, x + 39.3, ty + 14.6)
        self.line(x + 39.3, ty + 14.6, x + 40.6, ty + 12.9)
        # the home bar
        self.set_fill_color(90, 96, 112)
        self.rect(x + w / 2 - 8, y + h - 6.5, 16, 1.2, "F", round_corners=True, corner_radius=0.6)

    def contents(self, pdf, outline):
        """Draws the contents page once every chapter's page number is known."""
        t = self.t
        pdf.set_y(pdf.t_margin)
        self.pixel_label(pdf.l_margin, pdf.y + 3, "Inside", t["muted"], 7)
        pdf.set_font("Grotesk", "B", 22)
        pdf.set_text_color(*t["ink"])
        pdf.text(pdf.l_margin, pdf.y + 14, "What's in this guide")
        pdf.set_fill_color(*t["accent"])
        pdf.rect(pdf.l_margin, pdf.y + 18, 18, 1.6, "F")
        y = pdf.y + 28
        for section in outline:
            if section.level != 0:
                continue
            number, _, name = section.name.partition(". ")
            self.pixel_label(pdf.l_margin, y + 4.6, number.zfill(2), t["muted"], 7.4)
            pdf.set_font("Inter", "B", 10.6)
            pdf.set_text_color(*t["text"])
            pdf.text(pdf.l_margin + 10, y + 4.6, name)
            name_w = pdf.get_string_width(name)
            page = f"{section.page_number:02d}"
            pdf.set_font("Grotesk", "B", 10.6)
            page_w = pdf.get_string_width(page)
            pdf.text(pdf.w - pdf.r_margin - page_w, y + 4.6, page)
            pdf.set_draw_color(*t["rule"])
            pdf.set_line_width(0.25)
            pdf.set_dash_pattern(dash=0.4, gap=1.1)
            pdf.line(pdf.l_margin + 12 + name_w, y + 4.2, pdf.w - pdf.r_margin - page_w - 2, y + 4.2)
            pdf.set_dash_pattern()
            pdf.link(pdf.l_margin, y, pdf.text_w, 7, pdf.add_link(page=section.page_number))
            y += 9.2
        note = self.meta.get("contents_note")
        if note:
            pdf.set_y(y + 4)
            box = Block("callout", meta={"kind": "tip", "title": ""}, children=parse_blocks(note))
            self.block(box)

    def back_page(self):
        m, t = self.meta, self.t
        if not m.get("end_title"):
            return
        self.add_page()
        self.plain_pages.add(self.page)
        self.set_fill_color(*t["ink"])
        self.rect(0, 0, self.w, self.h, "F")
        x = self.l_margin
        self.pixel_label(x, 42, m.get("end_kicker", "What's next"), t["accent"], 8)
        big = {"family": "Grotesk", "style": "B", "size": 24, "lh": 10.4, "color": t["paper"]}
        self.set_y(48)
        self.flow(self.layout(parse_inline(m["end_title"]), self.text_w, big), x, big, breaks=False)
        body = dict(self.body, color=t["soft"], link_color=t["accent"], code_bg=t["screen"], code_color=t["accent"])
        self.set_y(self.y + 5)
        for chunk in m.get("end_text", "").split("|"):
            self.flow(self.layout(parse_inline(chunk.strip()), self.text_w, body), x, body, breaks=False)
            self.set_y(self.y + 3)
        link = m.get("end_link")
        if link:
            self.set_font("Inter", "B", 10.5)
            lw = self.get_string_width(link)
            y = self.y + 4
            self.set_fill_color(*t["accent"])
            self.rect(x, y, lw + 10, 9, "F", round_corners=True, corner_radius=2)
            self.set_text_color(*t["ink"])
            self.text(x + 5, y + 6, link)
            target = link if re.match(r"^https?://", link) else f"https://{link}"
            self.link(x, y, lw + 10, 9, target)
        for k in range(24):
            self.set_fill_color(*(t["accent"] if k % 5 == 0 else t["screen"]))
            self.rect(x + k * 5.0, self.h - 16, 3.2, 3.2, "F")

    # ------------------------------------------------------------ blocks

    def block(self, b, x=None, width=None, draw=True, breaks=True):
        """Renders one block at the current y, or with draw=False returns the height it needs."""
        x = self.l_margin if x is None else x
        width = self.text_w if width is None else width
        return getattr(self, f"b_{b.kind}")(b, x, width, draw, breaks)

    def b_p(self, b, x, width, draw, breaks):
        lines = self.layout(parse_inline(b.text), width, self.body)
        if draw:
            self.flow(lines, x, self.body, breaks)
            self.y += 2.8
        return self.lines_height(lines, self.body) + 2.8

    def b_h1(self, b, x, width, draw, breaks):
        if not draw:
            return 0
        if not self.at_top() or self.page == 1:
            self.new_page()
        self.chapters += 1
        self.start_section(f"{self.chapters}. {plain(b.text)}", level=0)
        self.pixel_label(x, self.y + 3, f"Part {self.chapters:02d}", self.t["muted"], 7)
        head = {"family": "Grotesk", "style": "B", "size": 21, "lh": 9.2, "color": self.t["ink"]}
        self.set_y(self.y + 6)
        self.flow(self.layout(parse_inline(b.text), width, head), x, head, breaks=False)
        self.set_fill_color(*self.t["accent"])
        self.rect(x, self.y + 1.6, 18, 1.6, "F")
        self.y += 8
        return 0

    def b_h2(self, b, x, width, draw, breaks):
        head = {"family": "Grotesk", "style": "B", "size": 13.5, "lh": 6.4, "color": self.t["ink"]}
        lines = self.layout(parse_inline(b.text), width, head)
        need = self.lines_height(lines, head) + 3.4 + 3 * self.body["lh"]
        if draw:
            if not self.fits(need):
                self.new_page()
            if not self.at_top():
                self.y += 2.2
            self.start_section(plain(b.text), level=1)
            self.flow(lines, x, head, breaks=False)
            self.y += 1.6
        return self.lines_height(lines, head) + 3.8

    def b_h3(self, b, x, width, draw, breaks):
        head = dict(self.body, style="B", size=10.8, color=self.t["ink"])
        lines = self.layout(parse_inline(b.text), width, head)
        if draw:
            if not self.fits(self.lines_height(lines, head) + 2 * self.body["lh"]):
                self.new_page()
            if not self.at_top():
                self.y += 1.2
            self.flow(lines, x, head, breaks=False)
            self.y += 0.6
        return self.lines_height(lines, head) + 1.8

    def _items(self, b, x, width, draw, breaks, indent, gap, marker):
        total = 0.0
        for k, item in enumerate(b.items):
            lines = self.layout(parse_inline(item), width - indent, self.body)
            h = self.lines_height(lines, self.body)
            if draw:
                if breaks and not self.fits(min(h, 3 * self.body["lh"])):
                    self.new_page()
                marker(k, x, self.y)
                self.flow(lines, x + indent, self.body, breaks)
                self.y += gap
            total += h + gap
        if draw:
            self.y += 1.8
        return total + 1.8

    def b_ul(self, b, x, width, draw, breaks):
        def square(k, x0, top):
            self.set_fill_color(*self.t["ink"])
            self.rect(x0 + 0.8, top + self.body["lh"] / 2 - 0.8, 1.6, 1.6, "F")
        return self._items(b, x, width, draw, breaks, 5.6, 1.1, square)

    def b_ol(self, b, x, width, draw, breaks):
        def badge(k, x0, top):
            cy = top + self.body["lh"] / 2
            self.set_fill_color(*self.t["accent"])
            self.circle(x0 + 2.7, cy, 2.7, "F")
            self.set_font("Grotesk", "B", 8.4)
            self.set_text_color(*self.t["ink"])
            label = str(k + 1)
            self.text(x0 + 2.7 - self.get_string_width(label) / 2, cy + 1.05, label)
        return self._items(b, x, width, draw, breaks, 8.2, 2.0, badge)

    def b_check(self, b, x, width, draw, breaks):
        done = b.meta.get("done", [])

        def box(k, x0, top):
            cy = top + self.body["lh"] / 2
            self.set_draw_color(*self.t["ink"])
            self.set_line_width(0.35)
            self.rect(x0 + 0.2, cy - 1.7, 3.4, 3.4, "D", round_corners=True, corner_radius=0.7)
            if k < len(done) and done[k]:
                self.line(x0 + 0.9, cy, x0 + 1.7, cy + 0.9)
                self.line(x0 + 1.7, cy + 0.9, x0 + 3.0, cy - 1.0)
        return self._items(b, x, width, draw, breaks, 6.6, 1.6, box)

    def b_callout(self, b, x, width, draw, breaks):
        bar, bg, label_color, label = CALLOUTS[b.meta["kind"]]
        pad, bar_w = 4.2, 1.4
        inner_x, inner_w = x + bar_w + pad, width - bar_w - 2 * pad
        title = b.meta.get("title", "")
        head_h = 5.2
        body_h = sum(self.block(c, inner_x, inner_w, draw=False) for c in b.children)
        body_h -= self._tail_gap(b.children)
        h = pad + head_h + body_h + pad - 0.8
        if not draw:
            return h + 4
        if breaks and not self.fits(h):
            self.new_page()
        top = self.y
        self.set_fill_color(*bg)
        self.rect(x, top, width, h, "F", round_corners=True, corner_radius=2.2)
        self.set_fill_color(*bar)
        self.rect(x, top, bar_w + 1.2, h, "F", round_corners=True, corner_radius=1.2)
        self.set_fill_color(*bg)
        self.rect(x + bar_w, top, 1.4, h, "F")
        lw = self.pixel_label(inner_x, top + pad + 2.9, label, label_color, 6.8)
        if title:
            self.set_font("Inter", "B", 9.8)
            self.set_text_color(*self.t["ink"])
            self.text(inner_x + lw + 3, top + pad + 3.1, plain(title))
        self.set_y(top + pad + head_h)
        for c in b.children:
            self.block(c, inner_x, inner_w, draw=True, breaks=False)
        self.set_y(top + h + 4)
        return h + 4

    def _tail_gap(self, children):
        last = children[-1].kind if children else ""
        return {"p": 2.8, "ul": 1.1 + 1.8, "ol": 2.0 + 1.8, "check": 1.6 + 1.8}.get(last, 0)

    def b_code(self, b, x, width, draw, breaks):
        if b.meta.get("lang") == "prompt":
            return self._prompt(b, x, width, draw, breaks)
        pad = 3.6
        base = {"family": "Mono", "style": "", "size": 8.4, "lh": 4.3, "color": self.t["paper"]}
        self.set_font("Mono", "", 8.4)
        per_line = max(8, int((width - 2 * pad) / self.get_string_width("M")))
        lines = []
        for src in b.text.split("\n"):
            while len(src) > per_line:
                lines.append(src[:per_line])
                src = "  " + src[per_line:]
            lines.append(src)
        label = {"bash": "Terminal", "sh": "Terminal", "shell": "Terminal", "terminal": "Terminal",
                 "powershell": "PowerShell", "": ""}.get(b.meta.get("lang", ""), b.meta.get("lang", ""))
        head = 5.0 if label else 0
        h = pad + head + len(lines) * base["lh"] + pad - 0.6
        if not draw:
            return h + 4
        if breaks and not self.fits(h):
            self.new_page()
        top = self.y
        self.set_fill_color(*self.t["ink2"])
        self.rect(x, top, width, h, "F", round_corners=True, corner_radius=2.2)
        if label:
            self.pixel_label(x + pad, top + pad + 2.4, label, self.t["soft"], 6)
        y = top + pad + head
        for src in lines:
            self.set_font("Mono", "", 8.4)
            prompt = src.startswith("$ ")
            if prompt:
                self.set_text_color(*self.t["accent"])
                self.text(x + pad, y + 3.1, "$")
                src = "  " + src[2:]
            self.set_text_color(*self.t["paper"])
            self.text(x + pad, y + 3.1, src)
            y += base["lh"]
        self.set_y(top + h + 4)
        return h + 4

    def _prompt(self, b, x, width, draw, breaks):
        pad = 4.0
        base = dict(self.body, size=10, lh=5.1, color=self.t["ink"])
        lines = []
        for src in b.text.split("\n"):
            lines.extend(self.layout(parse_inline(src), width - 2 * pad - 1.4, base) or [[]])
        head = 5.4
        h = pad + head + len(lines) * base["lh"] + pad - 0.6
        if not draw:
            return h + 4
        if breaks and not self.fits(h):
            self.new_page()
        top = self.y
        self.set_fill_color(255, 250, 229)
        self.set_draw_color(*self.t["accent"])
        self.set_line_width(0.5)
        self.rect(x, top, width, h, "DF", round_corners=True, corner_radius=2.2)
        self.pixel_label(x + pad + 1.4, top + pad + 2.7, "Prompt  ·  copy this", self.t["ink"], 6.4)
        self.set_y(top + pad + head)
        self.flow(lines, x + pad + 1.4, base, breaks=False)
        self.set_y(top + h + 4)
        return h + 4

    def b_table(self, b, x, width, draw, breaks):
        header, rows = b.meta["header"], b.items
        cols = len(header)
        rows = [(r + [""] * cols)[:cols] for r in rows]
        pad = 2.0
        cell = dict(self.small)
        head = dict(self.small, style="B", color=self.t["paper"])
        # column widths: each column's longest word is the floor, the rest shared by text length
        floors, weights = [], []
        for c in range(cols):
            texts = [header[c]] + [r[c] for r in rows]
            words = [w for text in texts for w in plain(text).split()] or [""]
            self.set_font("Inter", "B", cell["size"])
            floors.append(max(self.get_string_width(w) for w in words) + 2 * pad)
            self.set_font("Inter", "", cell["size"])
            weights.append(max(self.get_string_width(plain(t)) for t in texts) + 2 * pad)
        spare = max(0.0, width - sum(floors))
        extra = [max(0.0, w - f) for w, f in zip(weights, floors)]
        total_extra = sum(extra) or 1.0
        widths = [f + spare * e / total_extra for f, e in zip(floors, extra)]
        if sum(extra) == 0:
            widths = [f + spare / cols for f in floors]

        def layout_row(values, style):
            laid = [self.layout(parse_inline(v), widths[c] - 2 * pad, style) for c, v in enumerate(values)]
            return laid, max(len(ls) for ls in laid) * style["lh"] + 2 * pad - 0.4

        head_lines, head_h = layout_row(header, head)
        body = [layout_row(r, cell) for r in rows]
        total = head_h + sum(h for _, h in body)
        if not draw:
            return total + 4

        def draw_row(laid, h, style, fill):
            if fill:
                self.set_fill_color(*fill)
                self.rect(x, self.y, width, h, "F")
            cx = x
            for c, lines in enumerate(laid):
                top = self.y + pad - 0.2
                for line in lines:
                    self.draw_line(line, cx + pad, top, style)
                    top += style["lh"]
                cx += widths[c]
            self.y += h

        if breaks and not self.fits(head_h + (body[0][1] if body else 0)):
            self.new_page()
        top = self.y
        draw_row(head_lines, head_h, head, self.t["ink"])
        for k, (laid, h) in enumerate(body):
            if breaks and not self.fits(h):
                self.new_page()
                draw_row(head_lines, head_h, head, self.t["ink"])
            draw_row(laid, h, cell, self.t["row"] if k % 2 else None)
        self.set_draw_color(*self.t["rule"])
        self.set_line_width(0.25)
        self.line(x, self.y, x + width, self.y)
        if self.page == self.page and self.y > top:
            self.y += 4
        return total + 4

    def b_image(self, b, x, width, draw, breaks):
        path = b.meta["path"]
        if not os.path.isabs(path):
            path = os.path.join(self.meta.get("_base", HERE), path)
        from PIL import Image
        with Image.open(path) as im:
            ratio = im.height / im.width
        w = width
        h = w * ratio
        if draw:
            if breaks and not self.fits(h):
                self.new_page()
            self.image(path, x=x, y=self.y, w=w)
            self.y += h + 4
        return h + 4

    def b_hr(self, b, x, width, draw, breaks):
        if draw:
            self.set_draw_color(*self.t["rule"])
            self.set_line_width(0.3)
            self.line(x, self.y + 2, x + width, self.y + 2)
            self.y += 6
        return 6

    def b_pagebreak(self, b, x, width, draw, breaks):
        if draw and not self.at_top():
            self.new_page()
        return 0


def build_guide(markdown_text, page_size="A5", theme=None, base_dir=None):
    """Returns (pdf bytes, page count) for a Markdown guide."""
    meta, body = split_front_matter(markdown_text)
    meta["_base"] = base_dir or HERE
    pdf = GuidePDF(meta, page_size=page_size, theme=theme)
    pdf.set_page_background(pdf.t["page"])
    pdf.cover()
    pdf.add_page()  # the contents are drawn on this page at the end, once page numbers are known
    pdf.insert_toc_placeholder(pdf.contents, pages=1)
    pdf.set_y(pdf.t_margin)
    for b in parse_blocks(body):
        pdf.block(b)
    pdf.back_page()
    data = bytes(pdf.output())
    return data, pdf.pages_count


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build a designed PDF guide from a Markdown file.")
    ap.add_argument("markdown", help="the guide, in Markdown")
    ap.add_argument("-o", "--out", help="where to write the PDF (default: next to the Markdown)")
    ap.add_argument("--size", default="A5", help="page size: A5 (default), A4 or Letter")
    args = ap.parse_args(argv)
    with open(args.markdown, encoding="utf-8") as f:
        text = f.read()
    out = args.out or os.path.splitext(args.markdown)[0] + ".pdf"
    data, pages = build_guide(text, page_size=args.size, base_dir=os.path.dirname(os.path.abspath(args.markdown)))
    with open(out, "wb") as f:
        f.write(data)
    print(f"{out}: {pages} pages, {len(data) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
