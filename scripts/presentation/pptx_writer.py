"""Minimal OOXML .pptx writer built on the standard library only.

python-pptx is not installed and Step 8.2 forbids adding dependencies, so this
writes the Open XML package directly: a .pptx is a ZIP of XML parts. Only the
features this deck needs are implemented — 16:9 slides, text frames, pictures,
rounded rectangles, and speaker notes.

Presentation tooling only. It touches nothing in src/, api/ or the warehouse.
"""
from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape

EMU_PER_IN = 914400
W_EMU, H_EMU = 12192000, 6858000          # 13.333in x 7.5in -> 16:9
NS_P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def pt(v: float) -> int:          # points -> EMU
    return int(v * EMU_PER_IN / 72)


def hx(rgb: tuple[int, int, int]) -> str:
    return "%02X%02X%02X" % rgb


@dataclass
class Run:
    text: str
    size: float = 18
    bold: bool = False
    color: tuple = (21, 23, 28)
    italic: bool = False
    mono: bool = False


@dataclass
class Para:
    runs: list[Run] = field(default_factory=list)
    align: str = "l"            # l | ctr | r
    space_after: float = 6      # points
    bullet: bool = False
    indent: int = 0
    line_spacing: int = 100     # percent


@dataclass
class Shape:
    kind: str                   # "text" | "pic" | "rect"
    x: float; y: float; w: float; h: float      # inches
    paras: list[Para] = field(default_factory=list)
    image: Path | None = None
    fill: tuple | None = None
    line: tuple | None = None
    line_w: float = 1.25
    radius: bool = False
    v_anchor: str = "t"         # t | ctr | b
    margin: float = 0.10        # inches


@dataclass
class Slide:
    shapes: list[Shape] = field(default_factory=list)
    notes: str = ""
    bg: tuple = (255, 255, 255)


def _runs_xml(p: Para) -> str:
    out = []
    for r in p.runs:
        props = [f'sz="{int(r.size * 100)}"', f'b="{1 if r.bold else 0}"',
                 f'i="{1 if r.italic else 0}"', 'dirty="0"']
        face = "Consolas" if r.mono else "Arial"
        out.append(
            f'<a:r><a:rPr lang="en-IN" {" ".join(props)}>'
            f'<a:solidFill><a:srgbClr val="{hx(r.color)}"/></a:solidFill>'
            f'<a:latin typeface="{face}"/></a:rPr>'
            f'<a:t>{escape(r.text)}</a:t></a:r>'
        )
    if not out:
        out.append('<a:endParaRPr lang="en-IN"/>')
    return "".join(out)


def _para_xml(p: Para) -> str:
    bullet = ('<a:buFont typeface="Arial"/><a:buChar char="•"/>'
              if p.bullet else '<a:buNone/>')
    marL = f' marL="{pt(p.indent * 14)}" indent="{pt(-10) if p.bullet else 0}"' if (p.bullet or p.indent) else ""
    return (f'<a:p><a:pPr algn="{p.align}"{marL}>'
            f'<a:lnSpc><a:spcPct val="{p.line_spacing * 1000}"/></a:lnSpc>'
            f'<a:spcAft><a:spcPts val="{int(p.space_after * 100)}"/></a:spcAft>'
            f'{bullet}</a:pPr>{_runs_xml(p)}</a:p>')


def _shape_xml(s: Shape, sid: int, rid: str | None) -> str:
    x, y, w, h = pt(s.x * 72), pt(s.y * 72), pt(s.w * 72), pt(s.h * 72)
    xfrm = (f'<a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm>')

    if s.kind == "pic":
        return (f'<p:pic><p:nvPicPr><p:cNvPr id="{sid}" name="Picture {sid}"/>'
                f'<p:cNvPicPr/><p:nvPr/></p:nvPicPr>'
                f'<p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
                f'<p:spPr>{xfrm}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')

    geom = ('<a:prstGeom prst="roundRect"><a:avLst>'
            '<a:gd name="adj" fmla="val 8000"/></a:avLst></a:prstGeom>'
            if s.radius else '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>')
    fill = (f'<a:solidFill><a:srgbClr val="{hx(s.fill)}"/></a:solidFill>'
            if s.fill else '<a:noFill/>')
    ln = (f'<a:ln w="{pt(s.line_w)}"><a:solidFill>'
          f'<a:srgbClr val="{hx(s.line)}"/></a:solidFill></a:ln>'
          if s.line else '<a:ln><a:noFill/></a:ln>')
    m = pt(s.margin * 72)
    body = (f'<p:txBody><a:bodyPr anchor="{s.v_anchor}" wrap="square" '
            f'lIns="{m}" tIns="{m}" rIns="{m}" bIns="{m}">'
            f'<a:normAutofit/></a:bodyPr><a:lstStyle/>'
            + ("".join(_para_xml(p) for p in s.paras) or '<a:p><a:endParaRPr lang="en-IN"/></a:p>')
            + '</p:txBody>')
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="Shape {sid}"/>'
            f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr>{xfrm}{geom}{fill}{ln}</p:spPr>{body}</p:sp>')


_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
         '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
         '{}</Relationships>')


def _slide_xml(sl: Slide, media: dict[Path, str]) -> tuple[str, str]:
    shapes, rels, sid = [], [], 2
    rid_n = 2       # rId1 is the layout
    for sh in sl.shapes:
        rid = None
        if sh.kind == "pic":
            rid = f"rId{rid_n}"
            rels.append(f'<Relationship Id="{rid}" Type="{NS_R}/image" '
                        f'Target="../media/{media[sh.image]}"/>')
            rid_n += 1
        shapes.append(_shape_xml(sh, sid, rid))
        sid += 1
    rels.insert(0, f'<Relationship Id="rId1" Type="{NS_R}/slideLayout" '
                   f'Target="../slideLayouts/slideLayout1.xml"/>')
    if sl.notes:
        rels.append(f'<Relationship Id="rIdNotes" Type="{NS_R}/notesSlide" '
                    f'Target="../notesSlides/notesSlide{{N}}.xml"/>')
    bg = (f'<p:bg><p:bgPr><a:solidFill><a:srgbClr val="{hx(sl.bg)}"/></a:solidFill>'
          f'<a:effectLst/></p:bgPr></p:bg>')
    xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           f'<p:sld xmlns:p="{NS_P}" xmlns:a="{NS_A}" xmlns:r="{NS_R}">'
           f'<p:cSld>{bg}<p:spTree>'
           '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
           '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
           '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
           + "".join(shapes) +
           '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')
    return xml, _RELS.format("".join(rels))


def _notes_xml(text: str) -> str:
    paras = "".join(
        f'<a:p><a:r><a:rPr lang="en-IN" sz="1200"/><a:t>{escape(ln)}</a:t></a:r></a:p>'
        if ln.strip() else '<a:p><a:endParaRPr lang="en-IN"/></a:p>'
        for ln in text.split("\n"))
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<p:notes xmlns:p="{NS_P}" xmlns:a="{NS_A}" xmlns:r="{NS_R}">'
            '<p:cSld><p:spTree>'
            '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
            '<p:grpSpPr/>'
            '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Notes Placeholder"/>'
            '<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            '<p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr>'
            '<p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/>'
            f'{paras}</p:txBody></p:sp>'
            '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:notes>')


_THEME = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          f'<a:theme xmlns:a="{NS_A}" name="LMIS"><a:themeElements>'
          '<a:clrScheme name="LMIS"><a:dk1><a:srgbClr val="15171C"/></a:dk1>'
          '<a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="1A4FA0"/></a:dk2>'
          '<a:lt2><a:srgbClr val="F7F8FB"/></a:lt2><a:accent1><a:srgbClr val="1A4FA0"/></a:accent1>'
          '<a:accent2><a:srgbClr val="15543A"/></a:accent2><a:accent3><a:srgbClr val="8A6400"/></a:accent3>'
          '<a:accent4><a:srgbClr val="9A2A2A"/></a:accent4><a:accent5><a:srgbClr val="3C4A63"/></a:accent5>'
          '<a:accent6><a:srgbClr val="687080"/></a:accent6><a:hlink><a:srgbClr val="1A4FA0"/></a:hlink>'
          '<a:folHlink><a:srgbClr val="687080"/></a:folHlink></a:clrScheme>'
          '<a:fontScheme name="LMIS"><a:majorFont><a:latin typeface="Arial"/><a:ea typeface=""/>'
          '<a:cs typeface=""/></a:majorFont><a:minorFont><a:latin typeface="Arial"/>'
          '<a:ea typeface=""/><a:cs typeface=""/></a:minorFont></a:fontScheme>'
          '<a:fmtScheme name="LMIS"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
          '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
          '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>'
          '<a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
          '<a:ln w="15875"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
          '<a:ln w="25400"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>'
          '<a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle>'
          '<a:effectStyle><a:effectLst/></a:effectStyle>'
          '<a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>'
          '<a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
          '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
          '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>'
          '</a:fmtScheme></a:themeElements></a:theme>')

_EMPTY_TREE = ('<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/>'
               '<p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld>')

_MASTER = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           f'<p:sldMaster xmlns:p="{NS_P}" xmlns:a="{NS_A}" xmlns:r="{NS_R}">'
           f'{_EMPTY_TREE}<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" '
           'accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" '
           'accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
           '<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>'
           '</p:sldMaster>')

_LAYOUT = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           f'<p:sldLayout xmlns:p="{NS_P}" xmlns:a="{NS_A}" xmlns:r="{NS_R}" '
           f'type="blank" preserve="1">{_EMPTY_TREE}'
           '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>')

_NOTESMASTER = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                f'<p:notesMaster xmlns:p="{NS_P}" xmlns:a="{NS_A}" xmlns:r="{NS_R}">'
                f'{_EMPTY_TREE}<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" '
                'accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" '
                'accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
                '</p:notesMaster>')


def write_pptx(slides: list[Slide], out: Path) -> Path:
    media: dict[Path, str] = {}
    for sl in slides:
        for sh in sl.shapes:
            if sh.kind == "pic" and sh.image not in media:
                media[sh.image] = f"image{len(media) + 1}{sh.image.suffix}"

    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        ct = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
              '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
              '<Default Extension="xml" ContentType="application/xml"/>'
              '<Default Extension="png" ContentType="image/png"/>'
              '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
              '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>'
              '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>'
              '<Override PartName="/ppt/notesMasters/notesMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesMaster+xml"/>'
              '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>']
        for i, sl in enumerate(slides, 1):
            ct.append(f'<Override PartName="/ppt/slides/slide{i}.xml" '
                      'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')
            if sl.notes:
                ct.append(f'<Override PartName="/ppt/notesSlides/notesSlide{i}.xml" '
                          'ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"/>')
        z.writestr("[Content_Types].xml", "".join(ct) + "</Types>")

        z.writestr("_rels/.rels", _RELS.format(
            f'<Relationship Id="rId1" Type="{NS_R}/officeDocument" Target="ppt/presentation.xml"/>'))

        sld_ids = "".join(f'<p:sldId id="{255 + i}" r:id="rId{i + 2}"/>'
                          for i in range(1, len(slides) + 1))
        z.writestr("ppt/presentation.xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   f'<p:presentation xmlns:p="{NS_P}" xmlns:a="{NS_A}" xmlns:r="{NS_R}">'
                   '<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
                   f'<p:notesMasterIdLst><p:notesMasterId r:id="rId{len(slides) + 2}"/></p:notesMasterIdLst>'
                   f'<p:sldIdLst>{sld_ids}</p:sldIdLst>'
                   f'<p:sldSz cx="{W_EMU}" cy="{H_EMU}"/>'
                   f'<p:notesSz cx="{H_EMU}" cy="{W_EMU}"/></p:presentation>')

        prels = [f'<Relationship Id="rId1" Type="{NS_R}/slideMaster" Target="slideMasters/slideMaster1.xml"/>']
        for i in range(1, len(slides) + 1):
            prels.append(f'<Relationship Id="rId{i + 1}" Type="{NS_R}/slide" Target="slides/slide{i}.xml"/>')
        prels.append(f'<Relationship Id="rId{len(slides) + 2}" Type="{NS_R}/notesMaster" '
                     f'Target="notesMasters/notesMaster1.xml"/>')
        prels.append(f'<Relationship Id="rId{len(slides) + 3}" Type="{NS_R}/theme" Target="theme/theme1.xml"/>')
        z.writestr("ppt/_rels/presentation.xml.rels", _RELS.format("".join(prels)))

        z.writestr("ppt/theme/theme1.xml", _THEME)
        z.writestr("ppt/slideMasters/slideMaster1.xml", _MASTER)
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", _RELS.format(
            f'<Relationship Id="rId1" Type="{NS_R}/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
            f'<Relationship Id="rId2" Type="{NS_R}/theme" Target="../theme/theme1.xml"/>'))
        z.writestr("ppt/slideLayouts/slideLayout1.xml", _LAYOUT)
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", _RELS.format(
            f'<Relationship Id="rId1" Type="{NS_R}/slideMaster" Target="../slideMasters/slideMaster1.xml"/>'))
        z.writestr("ppt/notesMasters/notesMaster1.xml", _NOTESMASTER)
        z.writestr("ppt/notesMasters/_rels/notesMaster1.xml.rels", _RELS.format(
            f'<Relationship Id="rId1" Type="{NS_R}/theme" Target="../theme/theme1.xml"/>'))

        for i, sl in enumerate(slides, 1):
            xml, rels = _slide_xml(sl, media)
            z.writestr(f"ppt/slides/slide{i}.xml", xml)
            z.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", rels.replace("{N}", str(i)))
            if sl.notes:
                z.writestr(f"ppt/notesSlides/notesSlide{i}.xml", _notes_xml(sl.notes))
                z.writestr(f"ppt/notesSlides/_rels/notesSlide{i}.xml.rels", _RELS.format(
                    f'<Relationship Id="rId1" Type="{NS_R}/slide" Target="../slides/slide{i}.xml"/>'
                    f'<Relationship Id="rId2" Type="{NS_R}/notesMaster" '
                    f'Target="../notesMasters/notesMaster1.xml"/>'))

        for src, name in media.items():
            z.write(src, f"ppt/media/{name}")
    return out
