"""Check the self-contained PPTX and its planned main-figure coverage."""

import argparse
import json
import posixpath
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as E


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
UNWANTED_NOTES = re.compile(
    r"https?://|doi\.org|[A-Z]:[\\/]|(?:^|\s)/(?:home|Users|tmp)/|"
    r"\.(?:pdf|pptx|png|jpg)\b|Fig\.\s*\d|看图|左边|右边|可以看到|图中|这张图|这里展示",
    re.IGNORECASE,
)
LIST_BODIES = {"outline": "Outline body", "summary": "Summary body", "discussion": "Discussion body"}
TITLE_SHAPES = {"Black title bar", "Slide subject", "Cover title", "Question body", "Closing band"}
AUTHOR_HEADERS = {"corresponding author", "corresponding authors"}


def relationships(package, part):
    directory, filename = posixpath.split(part)
    path = posixpath.join(directory, "_rels", f"{filename}.rels")
    return {
        link.get("Id"): (link.get("Type").rsplit("/", 1)[-1],
                         posixpath.normpath(posixpath.join(directory, link.get("Target"))).lstrip("/"))
        for link in E.fromstring(package.read(path))
    }


def citation_matches(shape, citation):
    properties = shape.find("p:nvSpPr/p:cNvSpPr", NS)
    if properties is None or properties.get("txBox") not in ("1", "true"):
        return False
    first_authors = citation.get("first_authors", citation.get("authors"))
    corresponding_authors = citation.get("corresponding_authors", [])
    if not isinstance(first_authors, list) or not first_authors or not isinstance(corresponding_authors, list):
        return False
    unique_first = dict.fromkeys(first_authors)
    unique_corresponding = [name for name in dict.fromkeys(corresponding_authors) if name not in unique_first]
    names = ", ".join(unique_first)
    if unique_corresponding:
        names += " & " + ", ".join(unique_corresponding)
    expected = [(f"{names}, ", False), (citation["journal"], True), (f", {citation['year']}", False)]
    paragraphs = shape.findall("p:txBody/a:p", NS)
    if len(paragraphs) != 1:
        return False
    actual = []
    for run in paragraphs[0].findall("a:r", NS):
        style = run.find("a:rPr", NS)
        if style is None or style.get("sz") != "1400":
            return False
        actual.append((run.findtext("a:t", namespaces=NS), style.get("i") in ("1", "true")))
    return actual == expected


def is_bold_italic(style):
    return style is not None and all(style.get(attr) in ("1", "true") for attr in ("b", "i"))


def shape_text(body):
    return "\n".join("".join(t.text or "" for t in paragraph.findall(".//a:t", NS))
                     for paragraph in body.findall("a:p", NS))


def check_author_section(number, item, headings, nodes, connected, expected, profiles, trees, findings):
    header = headings.get("Black title bar", "")
    subjects = item.get("author_names", [])
    tree = headings.get("Slide subject", "").strip().casefold() == "neurotree"
    if not (subjects or tree or header.casefold() in AUTHOR_HEADERS | {"author", "authors"}):
        return
    if not isinstance(subjects, list) or not subjects or any(
        not isinstance(name, str) or name not in expected for name in subjects
    ) or len(set(subjects)) != len(subjects):
        findings.append(f"Slide {number}: identify the featured corresponding author(s) in author_names and paper.corresponding_authors.")
        return
    required_header = "Corresponding author" if len(subjects) == 1 else "Corresponding authors"
    if header != required_header:
        findings.append(f'Slide {number}: use the author-section heading "{required_header}".')
    if tree:
        for name in subjects:
            if not any(name in nodes.get(node, "") for node in connected):
                findings.append(f"Slide {number}: {name} needs a connected, editable Neurotree node.")
            else:
                trees.add(name)
    else:
        for name in subjects:
            if any(name in text for text in nodes.values()):
                profiles.add(name)


def list_matches(body, items):
    paragraphs = body.findall("a:p", NS)
    if len(paragraphs) != len(items):
        return False
    for paragraph, item in zip(paragraphs, items):
        props = paragraph.find("a:pPr", NS)
        if props is None:
            return False
        spacing = props.find("a:lnSpc/a:spcPct", NS)
        if spacing is None or spacing.get("val") != "150000":
            return False
        if item.get("bullet", True):
            level = item.get("level", 0)
            bullet = props.find("a:buChar", NS)
            if bullet is None or bullet.get("char") != ("l" if level else "p") or props.get("lvl") != str(level):
                return False
        runs = paragraph.findall("a:r", NS)
        label = item.get("label")
        prefix = f"{label} | " if label else ""
        if "".join(run.findtext("a:t", default="", namespaces=NS) for run in runs) != prefix + item["text"]:
            return False
        if label and (runs[0].findtext("a:t", namespaces=NS) != prefix or not is_bold_italic(runs[0].find("a:rPr", NS))):
            return False
        expected_color = item.get("color", "#000000").lstrip("#").upper()
        for run in runs:
            style = run.find("a:rPr", NS)
            fill = run.find("a:rPr/a:solidFill/a:srgbClr", NS)
            if style is None or style.get("sz") != "1800" or fill is None or fill.get("val") != expected_color:
                return False
    return True


def check(presentation, plan_path):
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    findings = []
    declared = plan.get("paper", {}).get("corresponding_authors", [])
    if not isinstance(declared, list) or any(not isinstance(name, str) or not name.strip() for name in declared):
        findings.append("paper.corresponding_authors must list the verified names.")
        declared = []
    expected_authors = set(declared)
    if any(slide["type"] == "cover" for slide in plan["slides"]) and not expected_authors:
        findings.append("Identify the paper's corresponding authors for the profiles and Neurotree.")
    profiles, trees = set(), set()
    prefix_pages = defaultdict(set)
    images = 0
    text_shapes = 0
    with zipfile.ZipFile(presentation) as package:
        if package.testzip():
            findings.append("A ZIP member failed its CRC check.")
        presentation_part = "ppt/presentation.xml"
        root = E.fromstring(package.read(presentation_part))
        links = relationships(package, presentation_part)
        slides = [links[slide.get(f"{{{NS['r']}}}id")][1] for slide in root.findall("p:sldIdLst/p:sldId", NS)]
        if len(slides) != len(plan["slides"]):
            findings.append("Slide count does not match the plan.")
        for name in package.namelist():
            if name.endswith(".rels"):
                for relationship in E.fromstring(package.read(name)):
                    if relationship.get("TargetMode") == "External":
                        findings.append(f"External relationship in {name}.")
        for number, (name, item) in enumerate(zip(slides, plan["slides"]), 1):
            root = E.fromstring(package.read(name))
            citations = {f"Figure citation {i}": citation for i, citation in enumerate(item.get("citations", []), 1)}
            list_body = LIST_BODIES.get(item["type"])
            list_found = False
            headings, nodes, node_ids = {}, {}, {}
            for shape in root.findall(".//p:sp", NS):
                body = shape.find("p:txBody", NS)
                if body is None:
                    continue
                text_shapes += 1
                identity = shape.find("p:nvSpPr/p:cNvPr", NS)
                shape_name = identity.get("name")
                text = shape_text(body)
                nodes[shape_name] = text
                node_ids[identity.get("id")] = shape_name
                if shape_name in TITLE_SHAPES:
                    headings[shape_name] = text
                    if "|" in text:
                        parts = [" ".join(part.split()) for part in text.split("|")]
                        if len(parts) != 2 or not all(parts):
                            findings.append(f"Slide {number}: malformed A | B heading.")
                        else:
                            prefix_pages[parts[0]].add(number)
                        separators = [run for run in body.findall("a:p/a:r", NS)
                                      if "|" in run.findtext("a:t", default="", namespaces=NS)]
                        if len(separators) != text.count("|") or any(
                            run.findtext("a:t", namespaces=NS) != "|" or not is_bold_italic(run.find("a:rPr", NS))
                            for run in separators
                        ):
                            findings.append(f"Slide {number}: format the heading separator in bold italic.")
                if shape_name in citations:
                    if not citation_matches(shape, citations.pop(shape_name)):
                        findings.append(f"Slide {number} has incorrect figure citation text or formatting.")
                    continue
                properties = shape.find("p:nvSpPr/p:cNvSpPr", NS)
                geometry = shape.find("p:spPr/a:prstGeom", NS)
                if properties is not None and properties.get("txBox") in ("1", "true"):
                    findings.append(f"Slide {number} contains a textbox.")
                if geometry is None or geometry.get("prst") != "rect":
                    findings.append(f"Slide {number} has a text object outside a rectangular shape.")
                if shape_name == list_body:
                    list_found = True
                    if not list_matches(body, item.get("items", [])):
                        findings.append(f"Slide {number} has incorrect {list_body} text or formatting.")
            for field, shape in [("header", "Black title bar"), ("subtitle", "Slide subject")]:
                if field in item and headings.get(shape) != item[field]:
                    findings.append(f"Slide {number}: {field} differs from the plan.")
            actual_edges = []
            for conn in root.findall(".//p:cxnSp/p:nvCxnSpPr/p:cNvCxnSpPr", NS):
                start, end = conn.find("a:stCxn", NS), conn.find("a:endCxn", NS)
                if start is not None and end is not None:
                    actual_edges.append((node_ids.get(start.get("id")), node_ids.get(end.get("id"))))
            expected_edges = [(edge["from"], edge["to"]) for edge in item.get("connections", [])]
            if Counter(actual_edges) != Counter(expected_edges):
                findings.append(f"Slide {number}: editable connections differ from the plan.")
            check_author_section(number, item, headings, nodes, {n for pair in actual_edges for n in pair},
                                 expected_authors, profiles, trees, findings)
            if list_body and not list_found:
                findings.append(f"Slide {number} is missing {list_body}.")
            if citations:
                findings.append(f"Slide {number} is missing one or more figure citations.")
            pictures = root.findall(".//p:pic", NS)
            if len(pictures) != len(item.get("images", [])):
                findings.append(f"Slide {number} embedded picture count does not match the plan.")
            for picture in pictures:
                images += 1
                blip = picture.find("p:blipFill/a:blip", NS)
                if blip is None or not blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"):
                    findings.append(f"Slide {number} contains an unembedded picture.")
            note_name = next((target for kind, target in relationships(package, name).values()
                              if kind == "notesSlide"), None)
            if not note_name or note_name not in package.namelist():
                findings.append(f"Slide {number} has no notes part.")
                continue
            notes_root = E.fromstring(package.read(note_name))
            note_paragraphs = [
                "".join(text.text or "" for text in paragraph.findall(".//a:t", NS))
                for shape in notes_root.findall(".//p:sp", NS)
                if shape.find("p:nvSpPr/p:nvPr/p:ph[@type='body']", NS) is not None
                for paragraph in shape.findall("p:txBody/a:p", NS)
            ]
            figure_refs = item.get("figure_refs") or []
            if figure_refs:
                figure_line = " ".join(f"[{ref}]" for ref in figure_refs)
                if note_paragraphs[:1] != [figure_line]:
                    findings.append(f"Slide {number} notes do not start with the planned figure references.")
                else:
                    note_paragraphs = note_paragraphs[1:]
            notes = "\n".join(note_paragraphs)
            expected_notes = (item.get("notes") or "").replace("\r\n", "\n")
            if notes != expected_notes or not notes.strip():
                findings.append(f"Slide {number} notes do not match the formal script.")
            if UNWANTED_NOTES.search(notes):
                findings.append(f"Slide {number} notes contain a citation, path or visual-direction phrase.")
    for prefix, pages in prefix_pages.items():
        if len(pages) == 1:
            findings.append(f'Slide {min(pages)}: "{prefix}" occurs as a heading prefix on only one slide.')
    for authors, label in [(profiles, "profile"), (trees, "Neurotree")]:
        for name in sorted(expected_authors - authors):
            findings.append(f"Missing {label} for corresponding author {name}.")
    expected = {
        f"{figure}{panel}"
        for figure, panels in plan.get("main_figures", {}).items()
        for panel in panels
    }
    covered = {
        panel for slide in plan["slides"] for image in slide.get("images", []) for panel in image.get("panels", [])
    }
    missing = sorted(expected - covered)
    if missing:
        findings.append(f"Uncovered main panels: {', '.join(missing)}")
    return {
        "file": str(presentation), "slides": len(plan["slides"]),
        "native_text_shapes": text_shapes, "embedded_pictures": images,
        "main_panels_expected": len(expected), "main_panels_covered": len(expected & covered),
        "findings": findings, "passed": not findings,
        "scope": "Package, native objects, notes and planned coverage. Rendered appearance and scientific accuracy require visual and source review.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("presentation", type=Path)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = check(args.presentation, args.plan)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
