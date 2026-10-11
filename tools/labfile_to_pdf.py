#!/usr/bin/env python3
"""Render an OHS lab file (LAB-FORMAT.md syntax) to the printable PDF
described in section 10 of LAB-WRITING-STANDARD.md.

Usage:
    python3 labfile_to_pdf.py LAB.md [-o OUT.pdf] [--image IMAGE_1=path.png ...]

IMAGE_n placeholders are resolved from --image options, or from the closing
"Figures needed" comment when a line there starts with "IMAGE_n: <path>".
Paths are relative to the lab file.
"""
import argparse
import io
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)
from reportlab.platypus.flowables import Flowable, HRFlowable

# ---------------------------------------------------------------- fonts ----
MPL_FONTS = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
SYS_FONTS = "/usr/share/fonts/truetype/dejavu"


def _font(name):
    for d in (SYS_FONTS, MPL_FONTS):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(name)


pdfmetrics.registerFont(TTFont("DejaVuSans", _font("DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", _font("DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DejaVuSans-Oblique", _font("DejaVuSans-Oblique.ttf")))
pdfmetrics.registerFont(TTFont("DejaVuSans-BoldOblique", _font("DejaVuSans-BoldOblique.ttf")))
pdfmetrics.registerFont(TTFont("DejaVuSansMono", _font("DejaVuSansMono.ttf")))
pdfmetrics.registerFontFamily("DejaVuSans", normal="DejaVuSans", bold="DejaVuSans-Bold",
                              italic="DejaVuSans-Oblique", boldItalic="DejaVuSans-BoldOblique")

# --------------------------------------------------------------- styles ----
DARK = colors.HexColor("#1f2a37")
RED = colors.HexColor("#b3412f")
GREY = colors.HexColor("#5b6470")
HEAD_BG = colors.HexColor("#eef0f3")
RULE = colors.HexColor("#9aa3ad")

PAGE_W, PAGE_H = letter
MARGIN_X = 0.85 * inch
MARGIN_Y = 0.75 * inch
TEXT_W = PAGE_W - 2 * MARGIN_X

S = {
    "title": ParagraphStyle("title", fontName="DejaVuSans-Bold", fontSize=20, leading=24, textColor=DARK, spaceAfter=4),
    "h1": ParagraphStyle("h1", fontName="DejaVuSans-Bold", fontSize=13, leading=16, textColor=RED, spaceBefore=12, spaceAfter=5, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="DejaVuSans-Bold", fontSize=10.5, leading=13, textColor=DARK, spaceBefore=8, spaceAfter=3, keepWithNext=1),
    "body": ParagraphStyle("body", fontName="DejaVuSans", fontSize=9.6, leading=13, textColor=DARK, spaceAfter=6, alignment=TA_LEFT),
    "step": ParagraphStyle("step", fontName="DejaVuSans", fontSize=9.6, leading=13, textColor=DARK, spaceAfter=6,
                           leftIndent=30, bulletIndent=0, bulletFontName="DejaVuSans-Bold", bulletFontSize=9.6),
    "note": ParagraphStyle("note", fontName="DejaVuSans", fontSize=8.8, leading=11.5, textColor=GREY, spaceAfter=3),
    "cell": ParagraphStyle("cell", fontName="DejaVuSans", fontSize=9, leading=11.5, textColor=DARK),
    "cellh": ParagraphStyle("cellh", fontName="DejaVuSans-Bold", fontSize=9, leading=11.5, textColor=DARK),
    "list": ParagraphStyle("list", fontName="DejaVuSans", fontSize=9.6, leading=13, textColor=DARK, spaceAfter=2,
                           leftIndent=16, bulletIndent=2, bulletFontName="DejaVuSans", bulletFontSize=9.6),
}

# --------------------------------------------------------- inline text ----
UNICODE_FIX = {"−": "−", "→": "→", "⇌": "⇌"}


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def math_inline(src):
    """Very small LaTeX-to-paragraph-markup converter for inline math."""
    out = []
    i = 0
    n = len(src)

    def group(j):
        """return (content, next_index) for a {...} group or single char at j"""
        if j < n and src[j] == "{":
            depth = 0
            k = j
            while k < n:
                if src[k] == "{":
                    depth += 1
                elif src[k] == "}":
                    depth -= 1
                    if depth == 0:
                        return src[j + 1:k], k + 1
                k += 1
            return src[j + 1:], n
        return src[j:j + 1], j + 1

    while i < n:
        c = src[i]
        if c == "\\":
            m = re.match(r"\\([A-Za-z]+|,|;)", src[i:])
            cmd = m.group(1)
            i += len(m.group(0))
            if cmd == "mathrm":
                g, i = group(i)
                out.append(esc(g))
            elif cmd in ("log", "ln", "exp"):
                out.append(cmd)
            elif cmd == "times":
                out.append("×")
            elif cmd == "cdot":
                out.append("·")
            elif cmd in (",", ";", "quad", "qquad"):
                out.append(" ")
            elif cmd == "p":
                out.append("p")
            else:
                out.append(esc(cmd))
        elif c == "_":
            g, i = group(i + 1)
            out.append("<sub>%s</sub>" % math_inline(g))
        elif c == "^":
            g, i = group(i + 1)
            out.append("<super>%s</super>" % math_inline(g))
        elif c.isalpha():
            out.append("<i>%s</i>" % c)
            i += 1
        elif c == "-":
            out.append("−")
            i += 1
        else:
            out.append(esc(c))
            i += 1
    return "".join(out)


def inline(text):
    """Markdown inline + $math$ + \\input -> reportlab paragraph markup."""
    parts = []
    pos = 0
    pattern = re.compile(r"(\$[^$]+\$|`[^`]+`|\\input\[[^\]]*\])")
    for m in pattern.finditer(text):
        parts.append(("md", text[pos:m.start()]))
        tok = m.group(0)
        if tok.startswith("$"):
            parts.append(("raw", math_inline(tok[1:-1])))
        elif tok.startswith("`"):
            parts.append(("raw", '<font face="DejaVuSansMono">%s</font>' % esc(tok[1:-1])))
        else:
            opts = parse_opts(tok[len("\\input["):-1])
            label = opts.get("label", "")
            unit = opts.get("unit", "")
            blank = "____________"
            s = (esc(label) + " " if label else "") + blank + (" " + esc(unit) if unit else "")
            parts.append(("raw", s))
        pos = m.end()
    parts.append(("md", text[pos:]))
    out = []
    for kind, s in parts:
        if kind == "raw":
            out.append(s)
            continue
        s = esc(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<i>\1</i>", s)
        s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<link href="\2" color="#b3412f">\1</link>', s)
        out.append(s)
    return "".join(out)


def parse_opts(s):
    opts = {}
    for m in re.finditer(r'([A-Za-z_]+)\s*(?:=\s*("([^"]*)"|[^,\]]+))?', s):
        key = m.group(1)
        if m.group(2) is None:
            opts[key] = True
        elif m.group(3) is not None:
            opts[key] = m.group(3)
        else:
            opts[key] = m.group(2).strip()
    return opts


# ----------------------------------------------------------- parsing ----
def read_command(lines, i):
    """lines[i] starts with \\cmd. Return (name, opts, content, next_i)."""
    text = "\n".join(lines[i:])
    m = re.match(r"\\([A-Za-z]+)(\[(?:[^\]\"]|\"[^\"]*\")*\])?\s*(\{)?", text)
    name = m.group(1)
    opts = parse_opts(m.group(2)[1:-1]) if m.group(2) else {}
    if not m.group(3):
        consumed = text[:m.end()].count("\n") + 1
        return name, opts, "", i + consumed
    depth = 0
    k = m.end() - 1
    start = k + 1
    while k < len(text):
        if text[k] == "{":
            depth += 1
        elif text[k] == "}":
            depth -= 1
            if depth == 0:
                break
        k += 1
    content = text[start:k]
    consumed = text[:k + 1].count("\n") + 1
    return name, opts, content.strip("\n"), i + consumed


def parse(text):
    """Return (meta, blocks). A block is a dict with 'type'."""
    lines = text.split("\n")
    meta = {}
    blocks = []
    i = 0
    para = []

    def flush():
        if para:
            blocks.append({"type": "para", "text": " ".join(s.strip() for s in para)})
            para.clear()

    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if s.startswith("<!--"):
            flush()
            buf = []
            while i < len(lines) and "-->" not in lines[i]:
                buf.append(lines[i])
                i += 1
            buf.append(lines[i] if i < len(lines) else "")
            blocks.append({"type": "comment", "text": "\n".join(buf)})
            i += 1
            continue
        if not s:
            flush()
            i += 1
            continue
        if s.startswith("$$"):
            flush()
            buf = [s]
            if not (s.endswith("$$") and len(s) > 2):
                i += 1
                while i < len(lines) and not lines[i].strip().endswith("$$"):
                    buf.append(lines[i].strip())
                    i += 1
                buf.append(lines[i].strip())
            eq = " ".join(buf).strip("$").strip()
            blocks.append({"type": "equation", "latex": eq})
            i += 1
            continue
        if s.startswith("\\") and not s.startswith("\\input"):
            flush()
            name, opts, content, i = read_command(lines, i)
            if name in ("title", "summary", "tags", "minutes"):
                meta[name] = content.strip()
            else:
                blocks.append({"type": "cmd", "name": name, "opts": opts, "content": content})
            continue
        m = re.match(r"(#{1,3})\s+(.*)", s)
        if m:
            flush()
            blocks.append({"type": "h%d" % len(m.group(1)), "text": m.group(2)})
            i += 1
            continue
        if s.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            blocks.append({"type": "table", "rows": rows})
            continue
        if re.match(r"(-|\d+\.)\s", s):
            flush()
            items = []
            while i < len(lines) and re.match(r"(-|\d+\.)\s", lines[i].strip()):
                items.append(lines[i].strip())
                i += 1
            blocks.append({"type": "list", "items": items})
            continue
        if s == "---":
            flush()
            blocks.append({"type": "hr"})
            i += 1
            continue
        if s.startswith(">"):
            flush()
            blocks.append({"type": "quote", "text": s.lstrip("> ")})
            i += 1
            continue
        para.append(line)
        i += 1
    flush()
    return meta, blocks


# ----------------------------------------------------------- flowables ----
class RuledLines(Flowable):
    """Blank writing lines for answers."""

    def __init__(self, n, width, leading=16):
        Flowable.__init__(self)
        self.n, self.w, self.lead = n, width, leading

    def wrap(self, aw, ah):
        return self.w, self.n * self.lead + 4

    def draw(self):
        c = self.canv
        c.setStrokeColor(RULE)
        c.setLineWidth(0.4)
        for k in range(self.n):
            y = self.n * self.lead - (k + 1) * self.lead + 4
            c.line(0, y, self.w, y)


class PhotoBox(Flowable):
    def __init__(self, text, width, height=1.5 * inch):
        Flowable.__init__(self)
        self.text, self.w, self.h = text, width, height

    def wrap(self, aw, ah):
        return self.w, self.h

    def draw(self):
        c = self.canv
        c.setStrokeColor(RULE)
        c.setLineWidth(0.6)
        c.setDash(3, 3)
        c.rect(0, 0, self.w, self.h)
        c.setDash()
        p = Paragraph("<b>Photo.</b> " + self.text, S["note"])
        pw, ph = p.wrap(self.w - 16, self.h)
        p.drawOn(c, 8, self.h - ph - 8)


def equation_image(latex, fontsize=15):
    """Render display math with matplotlib mathtext (Computer Modern)."""
    plt.rcParams["mathtext.fontset"] = "cm"
    fig = plt.figure(figsize=(0.1, 0.1))
    t = fig.text(0, 0, "$%s$" % latex, fontsize=fontsize, color="#1f2a37")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=400, bbox_inches="tight", pad_inches=0.02, transparent=True)
    plt.close(fig)
    buf.seek(0)
    from reportlab.lib.utils import ImageReader
    ir = ImageReader(buf)
    w, h = ir.getSize()
    buf.seek(0)
    scale = 72.0 / 400.0
    return Image(buf, width=w * scale, height=h * scale)


def blank_graph_image(opts, width):
    fig, ax = plt.subplots(figsize=(5.2, 3.1))
    ax.set_title(opts.get("title", ""), fontsize=9, color="#1f2a37")
    ax.set_xlabel(opts.get("xlabel", ""), fontsize=8, color="#1f2a37")
    ax.set_ylabel(opts.get("ylabel", ""), fontsize=8, color="#1f2a37")
    ax.tick_params(labelsize=7, colors="#5b6470")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    for sp in ax.spines.values():
        sp.set_color("#9aa3ad")
    # light grid of writing squares
    for k in range(1, 10):
        ax.axhline(k / 10, color="#d8dce2", lw=0.5)
        ax.axvline(k / 10, color="#d8dce2", lw=0.5)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200)
    plt.close(fig)
    buf.seek(0)
    h = width * 3.1 / 5.2
    return Image(buf, width=width, height=h)


def md_table(rows, blank_cells=False, title=None):
    data = []
    for r in rows:
        cells = [c.strip() for c in r.strip("|").split("|")]
        data.append(cells)
    # drop separator row
    data = [d for d in data if not all(re.match(r"^:?-{2,}:?$", c) for c in d)]
    ncol = max(len(d) for d in data)
    data = [d + [""] * (ncol - len(d)) for d in data]
    # natural widths
    nat = [0] * ncol
    for ri, d in enumerate(data):
        for ci, c in enumerate(d):
            font = "DejaVuSans-Bold" if ri == 0 else "DejaVuSans"
            plain = re.sub(r"[*`$\\{}]", "", c)
            if c == "___":
                w = 46
            else:
                w = pdfmetrics.stringWidth(plain, font, 9) + 10
            nat[ci] = max(nat[ci], w)
    total = sum(nat)
    blank_cols = [ci for ci in range(ncol) if any(d[ci] == "___" for d in data[1:])]
    if total > TEXT_W:
        widths = [w * TEXT_W / total for w in nat]
    elif blank_cells and blank_cols:
        extra = (TEXT_W - total) / len(blank_cols)
        widths = [w + (extra if ci in blank_cols else 0) for ci, w in enumerate(nat)]
    else:
        widths = nat
    cells = []
    for ri, d in enumerate(data):
        row = []
        for c in d:
            if c == "___":
                row.append("")
            else:
                row.append(Paragraph(inline(c), S["cellh"] if ri == 0 else S["cell"]))
        cells.append(row)
    t = Table(cells, colWidths=widths, hAlign="LEFT", rowHeights=None)
    style = [
        ("FONTNAME", (0, 0), (-1, -1), "DejaVuSans"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), DARK),
        ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, DARK),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, RULE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    if blank_cells:
        style += [("TOPPADDING", (0, 1), (-1, -1), 7), ("BOTTOMPADDING", (0, 1), (-1, -1), 7)]
    t.setStyle(TableStyle(style))
    out = []
    if title:
        out.append(Paragraph(inline(title), S["h2"]))
    out.append(t)
    out.append(Spacer(1, 8))
    return out


def callout(label, content, label_color=DARK):
    inner = []
    _, inner_blocks = parse(content)
    first = True
    for b in inner_blocks:
        if b["type"] == "para":
            txt = inline(b["text"])
            if first and label:
                txt = '<b><font color="%s">%s.</font></b> %s' % (label_color.hexval().replace("0x", "#"), esc(label), txt)
            inner.append(Paragraph(txt, S["note"]))
            first = False
        elif b["type"] == "list":
            if first and label:
                inner.append(Paragraph('<b><font color="%s">%s</font></b>' % (label_color.hexval().replace("0x", "#"), esc(label)), S["note"]))
                first = False
            inner.extend(list_flowables(b["items"], S["note"]))
    t = Table([[inner]], colWidths=[TEXT_W], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f6f8")),
        ("LINEBEFORE", (0, 0), (0, -1), 2, label_color),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return [t, Spacer(1, 8)]


def list_flowables(items, style=None):
    style = style or S["list"]
    out = []
    for it in items:
        m = re.match(r"(-|\d+\.)\s+(.*)", it)
        marker, text = m.group(1), m.group(2)
        if text.startswith("[ ] "):
            bullet, text = "☐", text[4:]
        elif text.startswith("[x] "):
            bullet, text = "☑", text[4:]
        elif marker == "-":
            bullet = "•"
        else:
            bullet = marker
        st = ParagraphStyle("li", parent=style, leftIndent=16, bulletIndent=2, spaceAfter=2)
        out.append(Paragraph(inline(text), st, bulletText=bullet))
    out.append(Spacer(1, 5))
    return out


# ------------------------------------------------------------- builder ----
class Builder:
    def __init__(self, lab_dir, images):
        self.lab_dir = lab_dir
        self.images = images
        self.tables = {}   # id -> title
        self.graphs = {}   # id -> title
        self.photos = {}   # id -> instruction
        self.story = []

    def figure_path(self, ref):
        p = self.images.get(ref, ref)
        if not os.path.isabs(p):
            p = os.path.join(self.lab_dir, p)
        return p if os.path.exists(p) else None

    def render(self, blocks, report=False):
        st = self.story
        for bi, b in enumerate(blocks):
            t = b["type"]
            nxt = blocks[bi + 1]["type"] if bi + 1 < len(blocks) else None
            if t == "comment":
                continue
            if t == "h1":
                st.append(Paragraph(inline(b["text"]), S["h1"]))
            elif t == "h2":
                st.append(Paragraph(inline(b["text"]), S["h2"]))
            elif t == "h3":
                st.append(Paragraph(inline(b["text"]), S["h2"]))
            elif t == "para":
                m = re.match(r"\*\*(\d+\.\d+)\*\*\s+(.*)", b["text"], re.S)
                if m:
                    st.append(Paragraph(inline(m.group(2)), S["step"], bulletText=m.group(1)))
                elif nxt == "equation":
                    st.append(Paragraph(inline(b["text"]), ParagraphStyle("lead", parent=S["body"], keepWithNext=1)))
                else:
                    st.append(Paragraph(inline(b["text"]), S["body"]))
            elif t == "equation":
                img = equation_image(b["latex"])
                img.hAlign = "LEFT"
                tbl = Table([[img]], colWidths=[TEXT_W - 30], hAlign="RIGHT")
                tbl.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
                st.append(tbl)
            elif t == "table":
                st.extend(md_table(b["rows"]))
            elif t == "list":
                st.extend(list_flowables(b["items"]))
            elif t == "hr":
                st.append(HRFlowable(width="100%", thickness=0.4, color=RULE, spaceBefore=4, spaceAfter=6))
            elif t == "quote":
                st.append(Paragraph(inline(b["text"]), S["note"]))
            elif t == "cmd":
                self.command(b, report)

    def command(self, b, report):
        st = self.story
        name, o, c = b["name"], b["opts"], b["content"]
        if name in ("safety", "warning", "info", "tip", "hint"):
            label = o.get("label", name.capitalize())
            color = RED if name in ("safety", "warning") else DARK
            st.extend(callout(label, c, color))
        elif name == "style":
            st.extend(callout("Style", c, DARK))
        elif name == "datatable":
            rows = [r for r in c.split("\n") if r.strip().startswith("|")]
            title = o.get("title")
            self.tables[o.get("id", "")] = title or "Data table"
            st.append(KeepTogether(md_table(rows, blank_cells=True, title=title)))
        elif name == "graph":
            title = o.get("title", "Graph")
            self.graphs[o.get("id", "")] = title
            img = blank_graph_image(o, TEXT_W * 0.75)
            img.hAlign = "LEFT"
            parts = [img]
            if c.strip():
                parts.append(Paragraph("<b>Graph.</b> " + inline(c.strip()), S["note"]))
            parts.append(Spacer(1, 8))
            st.append(KeepTogether(parts))
        elif name == "figure":
            path = self.figure_path(c.strip())
            size = o.get("size", "full")
            w = {"full": TEXT_W, "medium": TEXT_W * 0.6, "small": TEXT_W / 3}.get(size, TEXT_W)
            parts = []
            if path:
                from reportlab.lib.utils import ImageReader
                iw, ih = ImageReader(path).getSize()
                img = Image(path, width=w, height=w * ih / iw)
                img.hAlign = "LEFT"
                parts.append(img)
            else:
                parts.append(PhotoBox("Figure placeholder: " + esc(c.strip()), w, 1.2 * inch))
            if o.get("caption"):
                parts.append(Spacer(1, 3))
                parts.append(Paragraph(inline(o["caption"]), S["note"]))
            parts.append(Spacer(1, 8))
            st.append(KeepTogether(parts))
        elif name == "photo":
            self.photos[o.get("id", "")] = c.strip()
            st.append(PhotoBox(inline(c.strip()), TEXT_W))
            st.append(Spacer(1, 8))
        elif name == "video":
            st.append(Paragraph('Video: <link href="%s" color="#b3412f">%s</link>' % (esc(c.strip()), esc(c.strip())), S["body"]))
        elif name == "answer":
            parts = []
            if o.get("title"):
                parts.append(Paragraph(esc(o["title"]), S["h2"]))
            if c.strip():
                parts.append(Paragraph(inline(c.strip()), S["body"]))
            extras = []
            if o.get("words"):
                w = str(o["words"])
                if w.startswith("-"):
                    extras.append("at most %s words" % w[1:])
                elif "-" in w:
                    extras.append("%s words" % w.replace("-", " to "))
                else:
                    extras.append("at least %s words" % w)
            if o.get("hint"):
                extras.append(o["hint"])
            if extras:
                parts.append(Paragraph("<b>Hint.</b> " + esc(" ".join(x.rstrip(".") + "." for x in extras)), S["note"]))
            n = int(o.get("lines", 6 if report else 4))
            parts.append(RuledLines(n, TEXT_W))
            parts.append(Spacer(1, 10))
            st.append(KeepTogether(parts) if n <= 8 else parts[0])
            if n > 8:
                st.extend(parts[1:])
        elif name == "notes":
            st.append(Paragraph("<b>%s</b>" % esc(c.strip() or "Notes"), S["body"]))
            st.append(RuledLines(4, TEXT_W))
            st.append(Spacer(1, 8))
        elif name == "usetable":
            st.append(Paragraph("<b>Include</b> the table “%s” from the Data section, filled with the recorded values." % esc(self.tables.get(c.strip(), c.strip())), S["note"]))
            st.append(Spacer(1, 4))
        elif name == "usegraph":
            st.append(Paragraph("<b>Include</b> the graph “%s”, drawn from the recorded values." % esc(self.graphs.get(c.strip(), c.strip())), S["note"]))
            st.append(Spacer(1, 4))
        elif name == "usephoto":
            st.append(Paragraph("<b>Include</b> the photo: %s" % inline(self.photos.get(c.strip(), c.strip())), S["note"]))
            st.append(Spacer(1, 4))
        elif name == "useanswer":
            st.append(Paragraph("<b>Include</b> the answer written in the procedure (%s)." % esc(c.strip()), S["note"]))
        elif name == "procedure":
            _, inner = parse(c)
            self.render(inner)
        elif name == "report":
            st.append(PageBreak())
            st.append(Paragraph("Report", S["h1"]))
            _, inner = parse(c)
            self.render(inner, report=True)
        elif name == "pagebreak":
            st.append(PageBreak())
        else:
            st.append(Paragraph(inline(c), S["body"]))


def figures_from_comment(blocks):
    m = {}
    for b in blocks:
        if b["type"] == "comment":
            for line in b["text"].split("\n"):
                mm = re.match(r"\s*(IMAGE_\d+)\s*:\s*(\S+?)[,\s]", line + " ")
                if mm:
                    m.setdefault(mm.group(1), mm.group(2).rstrip(","))
    return m


def build(src, out, images):
    text = open(src, encoding="utf-8").read()
    meta, blocks = parse(text)
    lab_dir = os.path.dirname(os.path.abspath(src))
    imgs = figures_from_comment(blocks)
    imgs.update(images)
    bld = Builder(lab_dir, imgs)
    bld.story.append(Paragraph(esc(meta.get("title", "Lab")), S["title"]))
    sub = []
    if meta.get("minutes"):
        sub.append("About %s minutes" % meta["minutes"])
    if sub:
        bld.story.append(Paragraph(" · ".join(sub), S["note"]))
    bld.story.append(Spacer(1, 8))
    bld.render(blocks)
    doc = SimpleDocTemplate(out, pagesize=letter, leftMargin=MARGIN_X, rightMargin=MARGIN_X,
                            topMargin=MARGIN_Y, bottomMargin=MARGIN_Y,
                            title=meta.get("title", ""), author="", subject=meta.get("summary", ""))
    doc.build(bld.story)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("-o", "--out")
    ap.add_argument("--image", action="append", default=[], help="IMAGE_1=path.png")
    a = ap.parse_args()
    out = a.out or os.path.splitext(a.src)[0] + ".pdf"
    images = dict(x.split("=", 1) for x in a.image)
    build(a.src, out, images)
    print("wrote", out)
