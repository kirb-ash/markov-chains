#!/bin/sh
# builds paper.docx with required fonts (title 16, headings 14, text 12; tables 9)
cd "$(dirname "$0")"
pandoc paper.md -o paper.docx --reference-doc=reference.docx --resource-path=.
python3 - <<'PY'
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
d=Document('paper.docx')
for t in d.tables:
    b=OxmlElement('w:tblBorders')
    for e in ('top','left','bottom','right','insideH','insideV'):
        x=OxmlElement('w:'+e); x.set(qn('w:val'),'single'); x.set(qn('w:sz'),'4'); x.set(qn('w:color'),'888888'); b.append(x)
    t._tbl.tblPr.append(b)
    for row in t.rows:
        for c in row.cells:
            for p in c.paragraphs:
                for r in p.runs: r.font.size=Pt(9)
from docx.shared import Inches
for sec in d.sections:
    sec.left_margin=sec.right_margin=Inches(0.9); sec.top_margin=sec.bottom_margin=Inches(0.9)
d.save('paper.docx')
PY
