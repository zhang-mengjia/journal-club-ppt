"""Apply native shape text and the Journal Club paragraph style to an exported PPTX."""

import argparse
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as E


A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS = {"a": A, "p": P}
E.register_namespace("a", A)
E.register_namespace("p", P)
LIST_BODIES = {"Outline body", "Summary body", "Discussion body"}
PARAGRAPH_ORDER = {
    "lnSpc": 0, "spcBef": 1, "spcAft": 2, "buClrTx": 3, "buClr": 3,
    "buSzTx": 4, "buSzPct": 4, "buSzPts": 4, "buFontTx": 5, "buFont": 5,
    "buNone": 6, "buAutoNum": 6, "buChar": 6, "buBlip": 6, "tabLst": 7,
    "defRPr": 8, "extLst": 9,
}


def child(parent, name):
    element = parent.find(f"a:{name}", NS)
    if element is None:
        element = E.SubElement(parent, f"{{{A}}}{name}")
    return element


def set_color(properties, value):
    for fill in properties.findall("a:solidFill", NS):
        properties.remove(fill)
    fill = E.Element(f"{{{A}}}solidFill")
    E.SubElement(fill, f"{{{A}}}srgbClr", {"val": value.lstrip("#").upper()})
    properties.insert(0, fill)


def format_paragraph(paragraph, item=None, is_list=False):
    props = paragraph.find("a:pPr", NS)
    if props is None:
        props = E.Element(f"{{{A}}}pPr")
        paragraph.insert(0, props)
    for name in ("lnSpc", "spcBef", "spcAft"):
        existing = props.find(f"a:{name}", NS)
        if existing is not None:
            props.remove(existing)
    line = E.SubElement(props, f"{{{A}}}lnSpc")
    E.SubElement(line, f"{{{A}}}spcPct", {"val": "150000"})
    for name in ("spcBef", "spcAft"):
        element = E.SubElement(props, f"{{{A}}}{name}")
        E.SubElement(element, f"{{{A}}}spcPts", {"val": "0"})
    if item is not None:
        color = item.get("color", "#000000")
        default = child(props, "defRPr")
        default.set("sz", "1800")
        set_color(default, color)
        for run in paragraph.findall("a:r", NS):
            properties = child(run, "rPr")
            if list(run)[0] is not properties:
                run.remove(properties)
                run.insert(0, properties)
            properties.set("sz", "1800")
            set_color(properties, color)
        ending = paragraph.find("a:endParaRPr", NS)
        if ending is not None:
            set_color(ending, color)
        bullet = item.get("bullet", is_list)
        if bullet:
            level = item.get("level", 0)
            if level not in (0, 1):
                raise ValueError("Paragraph level must be 0 or 1.")
            props.set("marL", "742950" if level else "285750")
            props.set("indent", "-285750")
            props.set("lvl", str(level))
            for element in list(props):
                if element.tag.split("}")[-1].startswith("bu"):
                    props.remove(element)
            E.SubElement(props, f"{{{A}}}buClrTx")
            E.SubElement(props, f"{{{A}}}buFont", {"typeface": "Wingdings", "charset": "2", "pitchFamily": "2"})
            E.SubElement(props, f"{{{A}}}buChar", {"char": "l" if level else "p"})
    props[:] = sorted(props, key=lambda element: PARAGRAPH_ORDER.get(element.tag.split("}")[-1], 20))


def finish(source, plan_path, output):
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source) as package, zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as result:
        for member in package.infolist():
            payload = package.read(member.filename)
            match = re.fullmatch(r"ppt/slides/slide(\d+)\.xml", member.filename)
            if match:
                item = plan["slides"][int(match.group(1)) - 1]
                root = E.fromstring(payload)
                for shape in root.findall(".//p:sp", NS):
                    name = shape.find("p:nvSpPr/p:cNvPr", NS).get("name", "")
                    nonvisual = shape.find("p:nvSpPr/p:cNvSpPr", NS)
                    if name.startswith("Figure citation "):
                        nonvisual.set("txBox", "1")
                        continue
                    if nonvisual is not None:
                        nonvisual.attrib.pop("txBox", None)
                    body = shape.find("p:txBody", NS)
                    if body is None:
                        continue
                    paragraphs = body.findall("a:p", NS)
                    values = None
                    if name in LIST_BODIES:
                        values = item["items"]
                    elif name == "Body text":
                        values = item["paragraphs"]
                    if values is not None:
                        if len(values) != len(paragraphs):
                            raise ValueError(f"Paragraph count changed in {member.filename}.")
                        body.find("a:bodyPr", NS).set("anchor", "t")
                        for paragraph, value in zip(paragraphs, values):
                            format_paragraph(paragraph, value, name in LIST_BODIES)
                    elif name == "Question body" or name.startswith("Content text") or any(
                        text.get("name") == name for text in item.get("texts", [])
                    ):
                        for paragraph in paragraphs:
                            format_paragraph(paragraph)
                payload = E.tostring(root, encoding="utf-8", xml_declaration=True)
            result.writestr(member, payload)
    print(json.dumps({"output": str(output), "slides": len(plan["slides"])}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    finish(args.source, args.plan, args.output)


if __name__ == "__main__":
    main()
