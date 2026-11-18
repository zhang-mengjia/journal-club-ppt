"""Inspect original PDFs, article XML or images, and crop original figure panels."""

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as E


def inspect_file(source):
    data = {"file": source.name, "bytes": source.stat().st_size, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    if source.suffix.lower() == ".xml":
        root = E.parse(source).getroot()
        title = root.find(".//article-title")
        data["title"] = "".join(title.itertext()) if title is not None else ""
        data["article_ids"] = {item.get("pub-id-type"): item.text for item in root.findall(".//article-id")}
        data["sections"] = [
            {"id": section.get("id"), "text": " ".join("".join(section.itertext()).split())}
            for section in root.findall(".//body/sec")
        ]
        data["figures"] = [
            {"id": figure.get("id"), "text": " ".join("".join(figure.itertext()).split())}
            for figure in root.findall(".//fig")
        ]
    elif source.suffix.lower() == ".pdf":
        import fitz
        with fitz.open(source) as document:
            data["pages"] = [
                {"page": number + 1, "width": page.rect.width, "height": page.rect.height, "text": page.get_text()}
                for number, page in enumerate(document)
            ]
    else:
        from PIL import Image
        with Image.open(source) as image:
            image.verify()
        with Image.open(source) as image:
            data.update({"width": image.width, "height": image.height, "format": image.format})
    return data


def crop(source, box, output, page_number, scale):
    if source.suffix.lower() == ".pdf":
        import fitz
        with fitz.open(source) as document:
            if not 1 <= page_number <= len(document):
                raise ValueError("PDF page is out of range.")
            page = document[page_number - 1]
            clip = fitz.Rect(box) if box else page.rect
            if clip.is_empty or not page.rect.contains(clip):
                raise ValueError("PDF crop is outside the page.")
            page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip).save(output)
    else:
        from PIL import Image
        with Image.open(source) as image:
            if box:
                if not 0 <= box[0] < box[2] <= image.width or not 0 <= box[1] < box[3] <= image.height:
                    raise ValueError("Image crop is outside the original image.")
                image = image.crop(tuple(int(value) for value in box))
            image.convert("RGB").save(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("source", type=Path)
    inspect_parser.add_argument("--output", type=Path)
    crop_parser = subparsers.add_parser("crop")
    crop_parser.add_argument("source", type=Path)
    crop_parser.add_argument("--box", type=float, nargs=4, metavar=("X0", "Y0", "X1", "Y1"))
    crop_parser.add_argument("--page", type=int, default=1)
    crop_parser.add_argument("--scale", type=float, default=3)
    crop_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output and args.output.resolve() == args.source.resolve():
        raise ValueError("The output path must differ from the original material.")
    if args.command == "inspect":
        result = json.dumps(inspect_file(args.source), ensure_ascii=False, indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(result, encoding="utf-8")
        else:
            print(result)
    else:
        if args.output.exists():
            raise FileExistsError(args.output)
        if args.scale <= 0:
            raise ValueError("Scale must be positive.")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        crop(args.source, args.box, args.output, args.page, args.scale)
        print(json.dumps(inspect_file(args.output), ensure_ascii=False))


if __name__ == "__main__":
    main()
