"""Check the self-contained PPTX and its planned main-figure coverage."""

import argparse
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as E


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}
UNWANTED_NOTES = re.compile(
    r"https?://|doi\.org|[A-Z]:[\\/]|(?:^|\s)/(?:home|Users|tmp)/|"
    r"\.(?:pdf|pptx|png|jpg)\b|Fig\.\s*\d|看图|左边|右边|可以看到|图中|这张图|这里展示",
    re.IGNORECASE,
)


def check(presentation, plan_path):
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    findings = []
    images = 0
    text_shapes = 0
    with zipfile.ZipFile(presentation) as package:
        if package.testzip():
            findings.append("A ZIP member failed its CRC check.")
        slides = [name for name in package.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)]
        if len(slides) != len(plan["slides"]):
            findings.append("Slide count does not match the plan.")
        for name in package.namelist():
            if name.endswith(".rels"):
                for relationship in E.fromstring(package.read(name)):
                    if relationship.get("TargetMode") == "External":
                        findings.append(f"External relationship in {name}.")
        for number, item in enumerate(plan["slides"], 1):
            name = f"ppt/slides/slide{number}.xml"
            if name not in package.namelist():
                continue
            root = E.fromstring(package.read(name))
            for shape in root.findall(".//p:sp", NS):
                body = shape.find("p:txBody", NS)
                if body is None:
                    continue
                text_shapes += 1
                properties = shape.find("p:nvSpPr/p:cNvSpPr", NS)
                geometry = shape.find("p:spPr/a:prstGeom", NS)
                if properties is not None and properties.get("txBox") in ("1", "true"):
                    findings.append(f"Slide {number} contains a textbox.")
                if geometry is None or geometry.get("prst") != "rect":
                    findings.append(f"Slide {number} has a text object outside a rectangular shape.")
                shape_name = shape.find("p:nvSpPr/p:cNvPr", NS).get("name")
                if shape_name == "Summary body":
                    paragraphs = body.findall("a:p", NS)
                    expected_items = item.get("items", [])
                    if len(paragraphs) != len(expected_items):
                        findings.append(f"Slide {number} summary paragraph count changed.")
                    for paragraph, expected_item in zip(paragraphs, expected_items):
                        spacing = paragraph.find("a:pPr/a:lnSpc/a:spcPct", NS)
                        if spacing is None or spacing.get("val") != "150000":
                            findings.append(f"Slide {number} summary line spacing is not 1.5.")
                        expected_color = expected_item.get("color", "#000000").lstrip("#").upper()
                        for run in paragraph.findall("a:r", NS):
                            run_properties = run.find("a:rPr", NS)
                            fill = run.find("a:rPr/a:solidFill/a:srgbClr", NS)
                            if run_properties is None or run_properties.get("sz") != "1800":
                                findings.append(f"Slide {number} summary font size changed.")
                            if fill is None or fill.get("val") != expected_color:
                                findings.append(f"Slide {number} summary emphasis color changed.")
            for picture in root.findall(".//p:pic", NS):
                images += 1
                blip = picture.find("p:blipFill/a:blip", NS)
                if blip is None or not blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"):
                    findings.append(f"Slide {number} contains an unembedded picture.")
            note_name = f"ppt/notesSlides/notesSlide{number}.xml"
            if note_name not in package.namelist():
                findings.append(f"Slide {number} has no notes part.")
                continue
            notes_root = E.fromstring(package.read(note_name))
            notes = "".join(
                text.text or ""
                for shape in notes_root.findall(".//p:sp", NS)
                if shape.find("p:nvSpPr/p:nvPr/p:ph", NS) is not None
                and shape.find("p:nvSpPr/p:nvPr/p:ph", NS).get("type") == "body"
                for text in shape.findall(".//a:t", NS)
            )
            if notes != item.get("notes") or not notes.strip():
                findings.append(f"Slide {number} notes do not match the formal script.")
            if UNWANTED_NOTES.search(notes):
                findings.append(f"Slide {number} notes contain a citation, path or visual-direction phrase.")
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
