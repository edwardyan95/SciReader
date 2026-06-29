from __future__ import annotations

from .common import *


def parse_biorxiv_url(url: str) -> tuple[str, str | None]:
    parsed = urllib.parse.urlparse(url)
    if not parsed.path.startswith("/content/"):
        raise ValueError("bioRxiv URLs should look like https://www.biorxiv.org/content/<DOI>v<version>.")
    path = parsed.path.split("/content/", 1)[1].strip("/")
    path = re.sub(r"\.(?:full|abstract)(?:\.pdf)?$", "", path)
    parts = path.split("/")
    if len(parts) < 2:
        raise ValueError("Could not read a bioRxiv DOI from this URL.")
    tail = parts[-1]
    version = None
    version_match = re.match(r"(.+?)v(\d+)$", tail)
    if version_match:
        tail = version_match.group(1)
        version = version_match.group(2)
    doi = "/".join(parts[:-1] + [tail])
    return urllib.parse.unquote(doi), version


def fetch_biorxiv_metadata(doi: str, requested_version: str | None = None) -> dict:
    encoded_doi = urllib.parse.quote(doi, safe="/")
    data = json.loads(fetch_text(f"https://api.biorxiv.org/details/biorxiv/{encoded_doi}"))
    records = data.get("collection") or []
    if not records:
        raise ValueError(f"No bioRxiv metadata found for DOI {doi}.")
    if requested_version:
        for record in records:
            if str(record.get("version", "")) == str(requested_version):
                return record
    return max(records, key=lambda record: int(record.get("version") or 0))


def biorxiv_reader_url(doi: str, version: str) -> str:
    encoded_doi = urllib.parse.quote(doi, safe="/")
    return f"https://www.biorxiv.org/content/{encoded_doi}v{version}.full"


def is_biorxiv_panel_caption_line(value: str) -> bool:
    return bool(
        re.match(r"^\*\*\(?[a-z](?:\)|[,\s]|\*\*)", value, re.I)
        or re.match(r"^[A-Z](?:[,-][A-Z])?\.\s+\S", value)
    )


def parse_biorxiv_figure_label(value: str) -> tuple[str, int] | None:
    match = re.search(r"\bExtended\s+Data\s+(?:Fig\.?\s*)?(\d+)", value, re.I)
    if match:
        return "ext", int(match.group(1))
    match = re.search(r"\bSupplementary\s+Figure\s+(\d+)", value, re.I)
    if match:
        return "supp", int(match.group(1))
    match = re.search(r"\b(?:Fig\.?|Figure)\s+(\d+)", value, re.I)
    if match:
        return "fig", int(match.group(1))
    return None


def parse_biorxiv_caption_heading_label(value: str) -> tuple[str, int] | None:
    match = re.match(r"^Extended\s+Data\s+(?:Fig\.?\s*)?(\d+)(?:\.|:|\s|$)", value, re.I)
    if match:
        return "ext", int(match.group(1))
    match = re.match(r"^Supplementary\s+Figure\s+(\d+)(?:\.|:|\s|$)", value, re.I)
    if match:
        return "supp", int(match.group(1))
    match = re.match(r"^(?:Fig\.?|Figure)\s+(\d+)(?:\.|:|\s|$)", value, re.I)
    if match:
        return "fig", int(match.group(1))
    return None


def strip_biorxiv_caption_heading(value: str, figure_kind: str, number: int) -> str:
    if figure_kind == "ext":
        pattern = rf"^Extended\s+Data\s+(?:Fig\.?\s*)?{number}\s*[\.:]?\s*"
    elif figure_kind == "supp":
        pattern = rf"^Supplementary\s+Figure\s+{number}\s*[\.:]?\s*"
    else:
        pattern = rf"^(?:Fig\.?|Figure)\s+{number}\s*[\.:]?\s*"
    return re.sub(pattern, "", value, count=1, flags=re.I)


def short_biorxiv_figure_title(value: str) -> str:
    text = markdown_link_text(value).strip()
    panel_match = re.search(r"\s+\([A-Za-z]\)|\s+[A-Za-z]\)", text)
    sentence_match = re.match(r"(.+?\.)\s+(?=[A-Z][A-Za-z])", text)
    stops = []
    if panel_match:
        stops.append(panel_match.start())
    if sentence_match:
        stops.append(sentence_match.end(1))
    if stops:
        text = text[: min(stops)].strip()
    return text.rstrip(".")


def normalize_biorxiv_caption_text(value: str) -> str:
    return re.sub(
        r"^((?:Extended\s+Data\s+(?:Fig\.?\s*)?|Supplementary\s+Figure\s+|Fig\.?\s+|Figure\s+)\d+):(?=\S)",
        r"\1: ",
        value,
        count=1,
        flags=re.I,
    )


def extract_biorxiv_markdown_figure_blocks(lines: list[str], source_url: str) -> tuple[list[dict], set[int]]:
    figures = []
    skip_lines: set[int] = set()
    image_re = re.compile(
        r"^\[!\[(?P<alt>[^\]]*(?:(?:Extended\s+Data\s+)?Fig\.?|(?:Supplementary\s+)?Figure)\s+\d+[^\]]*)\]\((?P<thumb>[^)]+)\)\]\((?P<large>[^)\s]+)(?:\s+\"(?P<title>[^\"]+)\")?\)",
        re.I,
    )

    index = 0
    seen = set()
    while index < len(lines):
        value = lines[index].strip()
        image_match = image_re.match(value)
        if not image_match:
            index += 1
            continue

        label = parse_biorxiv_figure_label(image_match.group("alt"))
        if not label:
            index += 1
            continue
        figure_kind, number = label
        figure_id = f"{figure_kind}-{number}"
        if figure_id in seen:
            index += 1
            continue
        seen.add(figure_id)

        image_url = absolute_url(image_match.group("large"), source_url)
        asset_match = re.search(r"/F(\d+)\.large", image_url, re.I)
        source_anchor = f"F{asset_match.group(1)}" if asset_match else f"F{number}"
        image_title = markdown_link_text(image_match.group("title") or "")
        title = short_biorxiv_figure_title(image_title) or f"Figure {number}"
        caption_parts = []
        skip_start = index
        cursor = index + 1
        saw_figure_title = False
        consumed_caption_body = False
        while cursor < len(lines):
            current = lines[cursor].strip()
            if not current:
                cursor += 1
                continue
            if current.startswith("[![") or current.startswith("## "):
                break
            if current.startswith("*   [Download figure") or current.startswith("*   [Open in new tab"):
                cursor += 1
                continue
            title_label = parse_biorxiv_caption_heading_label(current)
            if title_label and title_label == (figure_kind, number):
                saw_figure_title = True
                stripped_heading = strip_biorxiv_caption_heading(current, figure_kind, number)
                if not stripped_heading and cursor + 1 < len(lines):
                    next_line = lines[cursor + 1].strip()
                    if (
                        next_line
                        and not next_line.startswith(("[![", "*   [Download figure", "*   [Open in new tab", "## "))
                    ):
                        stripped_heading = next_line
                        cursor += 1
                title_text = short_biorxiv_figure_title(stripped_heading)
                if title_text:
                    title = title_text
                caption_parts.append(normalize_biorxiv_caption_text(markdown_link_text(current)))
                if stripped_heading and stripped_heading != current:
                    caption_parts.append(markdown_link_text(stripped_heading))
                cursor += 1
                continue
            if is_biorxiv_panel_caption_line(current):
                caption_parts.append(markdown_link_text(current))
                cursor += 1
                continue
            if saw_figure_title and not consumed_caption_body and not re.search(r"\b(?:Figure|Fig\.?|Table)\s+\d+", current):
                caption_parts.append(markdown_link_text(current))
                consumed_caption_body = True
                cursor += 1
                continue
            break

        for line_number in range(skip_start, cursor):
            skip_lines.add(line_number)

        figures.append(
            {
                "id": figure_id,
                "label": (
                    f"Extended Data Fig. {number}"
                    if figure_kind == "ext"
                    else f"Supplementary Fig. {number}"
                    if figure_kind == "supp"
                    else f"Fig. {number}"
                ),
                "type": (
                    "Extended data"
                    if figure_kind == "ext"
                    else "Supplementary figure"
                    if figure_kind == "supp"
                    else "Main figure"
                ),
                "title": title,
                "image": image_url,
                "sourceUrl": f"{source_url}#{source_anchor}",
                "caption": clean_text(" ".join(caption_parts) or image_title or title)[:1800],
            }
        )
        index = cursor

    return sorted(
        figures,
        key=lambda figure: (
            0 if figure["id"].startswith("fig-") else 1 if figure["id"].startswith("ext-") else 2,
            int(re.search(r"(\d+)", figure["id"]).group(1)),
        ),
    ), skip_lines


def extract_biorxiv_markdown_table_blocks(lines: list[str], source_url: str) -> tuple[list[dict], set[int]]:
    tables = []
    skip_lines: set[int] = set()
    seen = set()
    for index, line in enumerate(lines):
        value = line.strip()
        match = re.match(r"^Table\s+(\d+)\.?\s*(.*)", value, re.I)
        if not match:
            continue
        number = int(match.group(1))
        table_id = f"table-{number}"
        if table_id in seen:
            skip_lines.add(index)
            continue
        seen.add(table_id)
        title = markdown_link_text(match.group(2)).strip() or f"Table {number}"
        caption_parts = [markdown_link_text(value)]
        cursor = index + 1
        while cursor < len(lines):
            current = lines[cursor].strip()
            if not current:
                cursor += 1
                continue
            if current.startswith("|"):
                caption_parts.append(markdown_link_text(current))
                cursor += 1
                continue
            break
        for line_number in range(index, cursor):
            skip_lines.add(line_number)
        tables.append(
            {
                "id": table_id,
                "label": f"Table {number}",
                "type": "Table",
                "title": title,
                "image": "",
                "sourceUrl": f"{source_url}#T{number}",
                "caption": clean_text(" ".join(caption_parts))[:1800],
            }
        )
    return tables, skip_lines


def biorxiv_asset_base(figures: list[dict]) -> str:
    for figure in figures:
        image = figure.get("image", "")
        match = re.match(r"(.*/F)\d+\.large\.jpg", image)
        if match:
            return match.group(1)
    return ""


def synthesize_biorxiv_missing_extended_figures(
    lines: list[str],
    source_url: str,
    figures: list[dict],
) -> list[dict]:
    existing_ids = {figure["id"] for figure in figures}
    asset_base = biorxiv_asset_base(figures)
    synthesized = []
    for line in lines:
        for match in re.finditer(
            r"\[?(Extended\s+Data\s+(?:Fig\.?\s*)?(?P<ext>\d+))[^\]]*?\]\([^)]*#F(?P<asset>\d+)\)",
            line,
            re.I,
        ):
            ext_number = int(match.group("ext"))
            figure_id = f"ext-{ext_number}"
            if figure_id in existing_ids:
                continue
            asset_number = int(match.group("asset"))
            synthesized.append(
                {
                    "id": figure_id,
                    "label": f"Extended Data Fig. {ext_number}",
                    "type": "Extended data",
                    "title": f"Extended Data Fig. {ext_number}",
                    "image": f"{asset_base}{asset_number}.large.jpg?width=800&height=600&carousel=1" if asset_base else "",
                    "sourceUrl": f"{source_url}#F{asset_number}",
                    "caption": "Extended data figure referenced in the text. The reader snapshot did not expose the full legend block for this item.",
                }
            )
            existing_ids.add(figure_id)
    return synthesized


BIORXIV_SKIP_SECTIONS = {
    "Competing Interest Statement",
    "Author Declarations",
    "Footnotes",
}


def parse_biorxiv_markdown_sections(
    lines: list[str],
    skip_lines: set[int],
    main_figure_count: int,
    anchor_map: dict[str, str],
    source_url: str,
) -> list[dict]:
    sections = []
    counter = [0]
    current = None
    current_skip = True
    article_started = False

    for index, line in enumerate(lines):
        value = line.strip()
        heading = re.match(r"^(#{2,4})\s+(.+)", value)
        if heading:
            title = markdown_link_text(heading.group(2))
            title_key = title.lower()
            if title_key == "references":
                break
            if not article_started and title_key not in {"abstract", "introduction", "results"}:
                current = None
                current_skip = True
                continue
            article_started = True
            current_skip = title in BIORXIV_SKIP_SECTIONS
            if current_skip:
                current = None
                continue
            section_id = slugify(title, "section")
            existing = {section["id"] for section in sections}
            suffix = 2
            base = section_id
            while section_id in existing:
                section_id = f"{base}-{suffix}"
                suffix += 1
            current = {"id": section_id, "title": title, "paragraphs": []}
            sections.append(current)
            continue

        formula_line = is_biorxiv_formula_image(value)
        if (
            not current
            or current_skip
            or index in skip_lines
            or not value
            or (value.startswith("[![") and not formula_line)
            or value.startswith(("*   [Download figure", "*   [Open in new tab", "|"))
        ):
            continue

        text = markdown_link_text(convert_biorxiv_formula_images(value, source_url))
        if not text:
            continue
        if formula_line and value.startswith(("![", "[![")) and current["paragraphs"]:
            current["paragraphs"][-1]["text"] = clean_text(f"{current['paragraphs'][-1]['text']} {text}")
            continue
        figures = []
        for figure_id in biorxiv_markdown_media_ids(value, anchor_map):
            add_unique(figures, figure_id)
        for figure_id in text_figure_ids(text, main_figure_count):
            add_unique(figures, figure_id)
        for figure_id in text_table_ids(text):
            add_unique(figures, figure_id)
        counter[0] += 1
        current["paragraphs"].append(
            {
                "id": f"p-{counter[0]}",
                "text": text,
                "figures": figures,
                "citations": paragraph_citations(text),
            }
        )

    return [section for section in sections if section["paragraphs"]]


def parse_biorxiv_markdown_references(lines: list[str]) -> dict[str, str]:
    references: dict[str, str] = {}
    try:
        start = next(index for index, line in enumerate(lines) if line.strip().lower() == "## references") + 1
    except StopIteration:
        return references

    for line in lines[start:]:
        value = line.strip()
        if value.startswith("## "):
            break
        match = re.match(r"^(\d+)\.\s+(.*)", value)
        if not match:
            continue
        number, raw_reference = match.groups()
        raw_reference = re.sub(rf"^{number}\.\s*", "", raw_reference)
        reference = markdown_link_text(raw_reference)
        if reference:
            references[number] = reference
    return references


def parse_biorxiv_article(url: str, assets_dir: str | Path = "assets") -> dict:
    doi, requested_version = parse_biorxiv_url(url)
    metadata = fetch_biorxiv_metadata(doi, requested_version)
    version = str(metadata.get("version") or requested_version or "1")
    source_url = biorxiv_reader_url(doi, version)
    cache_key = biorxiv_cache_key(url, doi, version)
    cache_dir = Path(assets_dir) / "imports" / cache_key
    cache_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = cache_dir / "article.md"
    if markdown_path.exists():
        markdown = markdown_path.read_text(encoding="utf-8")
        reader_url = "Jina Reader markdown snapshot"
        if is_blocked_biorxiv_markdown(markdown):
            markdown, reader_url = fetch_biorxiv_reader_markdown(source_url)
            markdown_path.write_text(markdown, encoding="utf-8")
    else:
        markdown, reader_url = fetch_biorxiv_reader_markdown(source_url)
        markdown_path.write_text(markdown, encoding="utf-8")

    lines = markdown.splitlines()
    figures, skip_lines = extract_biorxiv_markdown_figure_blocks(lines, source_url)
    figures.extend(synthesize_biorxiv_missing_extended_figures(lines, source_url, figures))
    tables, table_skip_lines = extract_biorxiv_markdown_table_blocks(lines, source_url)
    skip_lines.update(table_skip_lines)
    figures.extend(tables)
    anchor_map = {}
    for item in figures:
        anchor_match = re.search(r"#(F\d+|T\d+)$", item.get("sourceUrl", ""), re.I)
        if anchor_match:
            anchor_map[anchor_match.group(1).upper()] = item["id"]
    main_figure_count = sum(1 for figure in figures if figure["id"].startswith("fig-"))
    return {
        "sourceUrl": source_url,
        "sourceMirrorUrl": reader_url,
        "title": metadata.get("title") or "Untitled bioRxiv preprint",
        "journal": "bioRxiv",
        "published": metadata.get("date", ""),
        "doi": doi,
        "authors": metadata.get("authors", ""),
        "sections": parse_biorxiv_markdown_sections(lines, skip_lines, main_figure_count, anchor_map, source_url),
        "figures": sorted(
            figures,
            key=lambda figure: (
                0
                if figure["id"].startswith("fig-")
                else 1
                if figure["id"].startswith("ext-")
                else 2
                if figure["id"].startswith("supp-")
                else 3,
                int(re.search(r"(\d+)", figure["id"]).group(1)),
            ),
        ),
        "references": parse_biorxiv_markdown_references(lines),
        "cacheKey": cache_key,
        "sourceFamily": "biorxiv-direct",
    }
