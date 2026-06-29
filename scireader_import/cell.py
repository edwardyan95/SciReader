from __future__ import annotations

from .common import *
def resolve_cell_pmc_url(pii: str) -> str | None:
    if pii in CELL_PMC_FALLBACKS:
        return CELL_PMC_FALLBACKS[pii]

    search_params = urllib.parse.urlencode(
        {
            "db": "pubmed",
            "retmode": "json",
            "retmax": "1",
            "tool": NCBI_TOOL,
            "term": pii,
        }
    )
    search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{search_params}"
    search = json.loads(fetch_text(search_url))
    pmids = search.get("esearchresult", {}).get("idlist", [])
    if not pmids:
        return None

    convert_params = urllib.parse.urlencode(
        {
            "ids": pmids[0],
            "format": "json",
            "tool": NCBI_TOOL,
        }
    )
    convert_url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?{convert_params}"
    converted = json.loads(fetch_text(convert_url))
    for record in converted.get("records", []):
        pmcid = record.get("pmcid")
        if pmcid:
            return f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"
    return None


def parse_pmc_metadata(soup: BeautifulSoup, source_url: str, pmc_url: str) -> dict:
    authors = [
        clean_text(tag.get("content", ""))
        for tag in soup.select('meta[name="citation_author"]')
        if tag.get("content")
    ]
    return {
        "sourceUrl": source_url,
        "sourceMirrorUrl": pmc_url,
        "title": meta_content(soup, "citation_title")
        or clean_text(soup.title.get_text(" ", strip=True)),
        "journal": meta_content(soup, "citation_journal_title") or "Cell Press",
        "published": meta_content(soup, "citation_publication_date"),
        "doi": meta_content(soup, "citation_doi"),
        "authors": ", ".join(authors),
    }


def pmc_figure_id_from_href(href: str | None) -> str | None:
    if not href:
        return None
    main_match = re.search(r"#(?:F|fig)(\d+)$", href, re.I)
    if main_match:
        return f"fig-{int(main_match.group(1))}"
    return None


def pmc_paragraph_figures(p, text: str, main_figure_count: int) -> list[str]:
    ids: list[str] = []
    for link in p.select('a[href^="#F"]'):
        figure_id = pmc_figure_id_from_href(link.get("href"))
        if figure_id:
            add_unique(ids, figure_id)
    for link in p.select('a[href^="#SD"]'):
        for match in re.finditer(r"\b(?:Figure|Fig\.?)\s*S(\d+)", link.get_text(" ", strip=True), re.I):
            add_unique(ids, f"supp-{int(match.group(1))}")
    for figure_id in text_figure_ids(text, main_figure_count):
        add_unique(ids, figure_id)
    return ids


def add_pmc_section(
    sections: list[dict],
    title: str,
    paragraphs: list,
    counter: list[int],
    main_figure_count: int,
) -> None:
    usable = []
    for p in paragraphs:
        if p.find_parent(["figure", "table"]):
            continue
        text = paragraph_text(p)
        if not text:
            continue
        counter[0] += 1
        usable.append(
            {
                "id": f"p-{counter[0]}",
                "text": text,
                "figures": pmc_paragraph_figures(p, text, main_figure_count),
                "citations": paragraph_citations(text),
            }
        )

    if not usable:
        return

    base = slugify(title, "section")
    existing = {section["id"] for section in sections}
    section_id = base
    suffix = 2
    while section_id in existing:
        section_id = f"{base}-{suffix}"
        suffix += 1
    sections.append({"id": section_id, "title": title, "paragraphs": usable})


PMC_NON_BODY_SECTION_TITLES = {
    "Supplementary Material",
    "Supplementary Materials",
    "Supplemental information",
    "Acknowledgements",
    "Footnotes",
    "References",
    "Associated Data",
    "Data Availability Statement",
}


def direct_paragraphs(section) -> list:
    return [
        child
        for child in section.find_all("p", recursive=False)
        if not child.find_parent(["figure", "table"])
    ]


def parse_pmc_sections(soup: BeautifulSoup, main_figure_count: int) -> list[dict]:
    sections: list[dict] = []
    counter = [0]
    seen = set()

    for heading in soup.select("h2.pmc_sec_title"):
        title = clean_text(heading.get_text(" ", strip=True))
        section = heading.find_parent("section")
        if not section or id(section) in seen or title in PMC_NON_BODY_SECTION_TITLES:
            continue
        seen.add(id(section))

        child_sections = section.find_all("section", recursive=False)
        if child_sections:
            add_pmc_section(sections, title, direct_paragraphs(section), counter, main_figure_count)
            for child_section in child_sections:
                child_heading = child_section.select_one("h3.pmc_sec_title, h4.pmc_sec_title")
                child_title = clean_text(child_heading.get_text(" ", strip=True)) if child_heading else title
                add_pmc_section(
                    sections,
                    child_title,
                    direct_paragraphs(child_section),
                    counter,
                    main_figure_count,
                )
        else:
            add_pmc_section(sections, title, direct_paragraphs(section), counter, main_figure_count)

    return sections


def parse_pmc_main_figures(soup: BeautifulSoup, pmc_url: str) -> list[dict]:
    figures = []
    for figure in soup.select("figure.fig"):
        match = re.match(r"(?:F|fig)(\d+)$", figure.get("id", ""), re.I)
        if not match:
            continue
        number = int(match.group(1))
        heading = figure.select_one(".obj_head")
        raw_title = clean_text(heading.get_text(" ", strip=True)) if heading else f"Figure {number}"
        title = re.sub(rf"^Figure\s*{number}\s*[:.]?\s*", "", raw_title, flags=re.I).strip()
        image = figure.select_one("img.graphic")
        caption = figure.select_one("figcaption")
        caption_title = ""
        if caption:
            caption_title_node = caption.select_one("p")
            caption_title = clean_text(caption_title_node.get_text(" ", strip=True)) if caption_title_node else ""
        if not title:
            title = caption_title
        figure_anchor = figure.get("id")
        figures.append(
            {
                "id": f"fig-{number}",
                "label": f"Fig. {number}",
                "type": "Main figure",
                "title": title or raw_title,
                "image": absolute_url(image.get("src") if image else "", pmc_url),
                "sourceUrl": absolute_url(f"figure/{figure_anchor}/", pmc_url),
                "caption": clean_text(caption.get_text(" ", strip=True)) if caption else raw_title,
            }
        )
    return sorted(figures, key=lambda figure: int(figure["id"].split("-")[1]))


def pmc_supplement_numbers(soup: BeautifulSoup) -> list[int]:
    numbers = set()
    for item in soup.select("section.sm, #SM1 p, #app2 p, #app2 span"):
        value = clean_text(item.get_text(" ", strip=True))
        for start, end in re.findall(r"Figures?\s*S\s*(\d+)\s*(?:\u2013|-|to)\s*S?\s*(\d+)", value, re.I):
            numbers.update(range(int(start), int(end) + 1))
        for number in re.findall(r"Figures?\s*S\s*(\d+)", value, re.I):
            numbers.add(int(number))
    return sorted(numbers)


def find_pmc_supplement_pdf_link(soup: BeautifulSoup):
    for item in soup.select("section.sm"):
        caption = clean_text(item.get_text(" ", strip=True))
        link = item.select_one('a[href$=".pdf"]')
        if link and re.search(r"Figures?\s*S", caption, re.I):
            return link
    return soup.select_one('#SD2 a[href$=".pdf"]') or soup.select_one('a[href$=".pdf"]')


def extract_supplement_caption(page_text: str, number: int) -> str:
    match = re.search(
        rf"(Figure\s+S{number}\b.*?)(?=\n\s*Figure\s+S\d+\b|\Z)",
        page_text,
        re.I | re.S,
    )
    return clean_text(match.group(1)) if match else clean_text(page_text)[:700]


def discover_cell_supplement_pdf_numbers(pdf_path: Path) -> list[int]:
    try:
        import fitz
    except Exception:
        return []

    numbers = set()
    doc = fitz.open(pdf_path)
    for index in range(len(doc)):
        text = doc[index].get_text("text")
        for number in re.findall(r"\bFigure\s+S\s*(\d+)\b", text, re.I):
            numbers.add(int(number))
    doc.close()
    return sorted(numbers)


def pdf_caption_heading_y(page, number: int) -> float | None:
    pattern = re.compile(rf"\bFigure\s+S\s*{number}\b", re.I)
    page_dict = page.get_text("dict")
    for block in page_dict.get("blocks", []):
        lines = []
        for line in block.get("lines", []):
            text = "".join(span.get("text", "") for span in line.get("spans", []))
            if text:
                lines.append(text)
        if pattern.search(" ".join(lines)):
            return float(block["bbox"][1])
    return None


def render_cell_supplementary_pdf(
    pdf_path: Path,
    numbers: list[int],
    cache_dir: Path,
    source_url: str,
    image_prefix: str = "figure-s",
    image_page_offset: int = -1,
    stitch_page_ranges: bool = False,
    crop_caption_heading: bool = False,
) -> list[dict]:
    try:
        import fitz
    except Exception:
        return [
            {
                "id": f"supp-{number}",
                "label": f"Figure S{number}",
                "type": "Supplementary figure",
                "title": f"Figure S{number}",
                "image": "",
                "sourceUrl": "./" + pdf_path.as_posix(),
                "caption": "Document S1 was captured, but PDF rendering is unavailable.",
            }
            for number in numbers
        ]

    figures = []
    doc = fitz.open(pdf_path)
    if not numbers:
        numbers = discover_cell_supplement_pdf_numbers(pdf_path)

    caption_pages: dict[int, int] = {}
    for number in numbers:
        pattern = re.compile(rf"\bFigure\s+S\s*{number}\b", re.I)
        for index in range(len(doc)):
            if pattern.search(doc[index].get_text()):
                caption_pages[number] = index
                break
    use_sequential_pages = not caption_pages and len(doc) >= len(numbers)

    for offset, number in enumerate(numbers):
        if use_sequential_pages:
            image_page = min(offset, len(doc) - 1)
            image_pages = [image_page]
            page_text = doc[image_page].get_text()
        else:
            caption_page = caption_pages.get(number)
            if caption_page is None:
                continue
            next_caption_page = min(
                [page for other, page in caption_pages.items() if other > number],
                default=len(doc) + 1,
            )
            image_page = min(max(0, caption_page + image_page_offset), len(doc) - 1)
            if stitch_page_ranges:
                end_page = max(image_page + 1, min(next_caption_page, len(doc)))
                image_pages = list(range(image_page, end_page))
            else:
                image_pages = [image_page]
            caption_y = pdf_caption_heading_y(doc[caption_page], number) if crop_caption_heading else None
            if caption_y is not None and image_page == caption_page:
                image_pages = [(image_page, fitz.Rect(0, 0, doc[image_page].rect.width, max(1, caption_y - 4)))]
            caption_stop = max(caption_page + 1, next_caption_page - 1)
            page_text = "\n".join(
                doc[index].get_text() for index in range(caption_page, min(caption_stop, len(doc)))
            )

        image_path = cache_dir / f"{image_prefix}{number}.png"
        if not image_path.exists():
            pixmaps = []
            for page_item in image_pages:
                if isinstance(page_item, tuple):
                    page_index, clip = page_item
                    pixmaps.append(doc[page_index].get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False, clip=clip))
                else:
                    pixmaps.append(doc[page_item].get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False))
            if len(pixmaps) == 1:
                pixmaps[0].save(image_path)
            else:
                from PIL import Image

                images = [Image.frombytes("RGB", [pix.width, pix.height], pix.samples) for pix in pixmaps]
                width = max(image.width for image in images)
                height = sum(image.height for image in images)
                stitched = Image.new("RGB", (width, height), (255, 255, 255))
                top = 0
                for image in images:
                    stitched.paste(image, ((width - image.width) // 2, top))
                    top += image.height
                stitched.save(image_path)
            try:
                trim_whitespace(image_path)
            except Exception:
                pass

        caption = extract_supplement_caption(page_text, number)
        title = re.sub(rf"^Figure\s+S\s*{number}\s*[:.]?\s*", "", caption, flags=re.I)
        title = title.split(". ")[0].strip()[:180] or f"Figure S{number}"
        if use_sequential_pages:
            title = f"Figure S{number}"
            caption = (
                f"Figure S{number} rendered from captured Document S1. The PDF text layer does not "
                "expose the figure legend cleanly for this supplement."
            )
        figures.append(
            {
                "id": f"supp-{number}",
                "label": f"Figure S{number}",
                "type": "Supplementary figure",
                "title": title,
                "image": "./" + image_path.as_posix(),
                "sourceUrl": "./" + pdf_path.as_posix(),
                "caption": caption[:1200],
            }
        )
    doc.close()
    return figures


def render_cell_supplementary_figures(
    soup: BeautifulSoup, cache_key: str, assets_dir: Path, pmc_url: str
) -> list[dict]:
    numbers = pmc_supplement_numbers(soup)
    if not numbers:
        return []

    pdf_link = find_pmc_supplement_pdf_link(soup)
    if not pdf_link:
        return [
            {
                "id": f"supp-{number}",
                "label": f"Figure S{number}",
                "type": "Supplementary figure",
                "title": f"Figure S{number}",
                "image": "",
                "sourceUrl": pmc_url,
                "caption": "Supplementary figure referenced, but no PDF link was found.",
            }
            for number in numbers
        ]

    pdf_url = absolute_url(pdf_link.get("href"), pmc_url)
    cache_dir = assets_dir / "imports" / cache_key
    cache_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = cache_dir / "document-s1.pdf"
    if not pdf_path.exists() or pdf_path.read_bytes()[:4] != b"%PDF":
        pdf_path.write_bytes(fetch_bytes(pdf_url))

    return render_cell_supplementary_pdf(pdf_path, numbers, cache_dir, pmc_url)


def parse_pmc_references(soup: BeautifulSoup) -> dict[str, str]:
    references = {}
    for item in soup.select('li[id^="R"], li[id^="bib"]'):
        match = re.match(r"(?:R|bib)(\d+)$", item.get("id", ""), re.I)
        if not match:
            continue
        cite = item.select_one("cite") or item
        references[match.group(1)] = clean_text(cite.get_text(" ", strip=True))
    return references



CELL_DIRECT_SKIP_LINES = {
    "Show full caption",
    "Open table in a new tab",
}


def is_markdown_video_link(value: str) -> bool:
    return bool(re.match(r"^\[Video\s+\([^)]+\)\]\(", value, re.I))


def is_cell_media_title(value: str) -> bool:
    return bool(re.match(r"^(?:Video|Table|File)\s+S?\d+\b", value, re.I))


def is_jwt_like_line(value: str) -> bool:
    return (
        len(value) > 220
        and value.count(".") == 2
        and bool(re.fullmatch(r"[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+){2}", value))
    )


def is_cell_markdown_noise_line(value: str) -> bool:
    return (
        value in CELL_DIRECT_SKIP_LINES
        or is_markdown_video_link(value)
        or is_cell_media_title(value)
        or is_jwt_like_line(value)
    )


def is_cell_panel_caption_line(value: str) -> bool:
    return bool(re.match(r"^\([A-Z](?:\)|\s|,|-|\u2010|\u2011|\u2012|\u2013|\u2014|\u2015)", value))


def extract_markdown_media_blocks(lines: list[str]) -> set[int]:
    skip_lines: set[int] = set()

    for index, line in enumerate(lines):
        value = line.strip()
        if is_jwt_like_line(value):
            skip_lines.add(index)
            continue
        if not is_markdown_video_link(value):
            continue

        skip_lines.add(index)
        cursor = index + 1
        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1

        title_index = cursor
        if title_index < len(lines) and is_cell_media_title(lines[title_index].strip()):
            skip_lines.add(title_index)
            cursor = title_index + 1
            while cursor < len(lines) and not lines[cursor].strip():
                cursor += 1

            if cursor < len(lines):
                caption = lines[cursor].strip()
                if (
                    caption
                    and not caption.startswith(("#", "[!["))
                    and not re.match(r"^Figure\s+S?\d+\b", caption, re.I)
                    and not is_markdown_video_link(caption)
                ):
                    skip_lines.add(cursor)

    return skip_lines


def extract_markdown_figure_blocks(lines: list[str], source_url: str) -> tuple[list[dict], set[int]]:
    figures = []
    skip_lines: set[int] = set()
    image_re = re.compile(r"^\[!\[[^\]]*\]\((?P<thumb>[^)]+)\)\]\((?P<large>[^)\s]+)(?:\s+\"[^\"]+\")?\)")

    index = 0
    while index < len(lines):
        image_match = image_re.match(lines[index].strip())
        if not image_match:
            index += 1
            continue

        label_index = index + 1
        while label_index < len(lines) and not lines[label_index].strip():
            label_index += 1
        if label_index >= len(lines):
            break

        label_line = lines[label_index].strip()
        label_match = re.match(r"Figure\s+(S?)(\d+)\s+(.+)", label_line, re.I)
        if not label_match:
            index += 1
            continue

        prefix, number_text, raw_title = label_match.groups()
        number = int(number_text)
        is_supplement = bool(prefix)
        figure_id = f"supp-{number}" if is_supplement else f"fig-{number}"
        label = f"Figure S{number}" if is_supplement else f"Fig. {number}"
        title = markdown_link_text(raw_title)
        image_url = absolute_url(image_match.group("large"), source_url)

        caption_parts = [markdown_link_text(label_line)]
        skip_start = index
        cursor = label_index + 1
        while cursor < len(lines):
            value = lines[cursor].strip()
            if not value:
                cursor += 1
                continue
            if value in CELL_DIRECT_SKIP_LINES:
                cursor += 1
                continue
            if value.startswith("[![") or value.startswith("##"):
                break
            if is_markdown_video_link(value) or is_cell_media_title(value) or is_jwt_like_line(value):
                break
            if not (is_cell_panel_caption_line(value) or re.match(r"^See also\b", value, re.I)):
                break
            caption_parts.append(markdown_link_text(value))
            cursor += 1

        for line_number in range(skip_start, cursor):
            skip_lines.add(line_number)

        figures.append(
            {
                "id": figure_id,
                "label": label,
                "type": "Supplementary figure" if is_supplement else "Main figure",
                "title": title,
                "image": image_url,
                "sourceUrl": f"{source_url}#figs{number}" if is_supplement else f"{source_url}#fig{number}",
                "caption": clean_text(" ".join(caption_parts))[:1800],
            }
        )
        index = cursor

    return figures, skip_lines


CELL_DIRECT_SKIP_SECTIONS = {
    "Highlights",
    "Graphical abstract",
    "Keywords",
}
CELL_DIRECT_START_TITLES = {
    "Summary",
    "Abstract",
    "Introduction",
    "Results",
}
CELL_DIRECT_STOP_SECTIONS = {
    "References",
}
CELL_BROWSER_STOP_SECTIONS = {
    "References",
    "Article metrics",
    "Related Articles",
}
CELL_BROWSER_SKIP_LINES = {
    *CELL_DIRECT_SKIP_LINES,
    "Google Scholar",
    "Download all",
}


def is_cell_browser_skip_line(value: str) -> bool:
    return value in CELL_BROWSER_SKIP_LINES or value.startswith("Show full caption")


def parse_markdown_references(lines: list[str]) -> dict[str, str]:
    references: dict[str, str] = {}
    start = None
    for index, line in enumerate(lines):
        if line.strip().lower() == "## references":
            start = index + 1
            break
    if start is None:
        return references

    current_number = None
    current_parts: list[str] = []
    for line in lines[start:]:
        value = line.strip()
        if value.startswith("## "):
            break
        match = re.match(r"^(\d+)\.$", value)
        if match:
            if current_number and current_parts:
                references[current_number] = markdown_link_text(" ".join(current_parts))
            current_number = match.group(1)
            current_parts = []
            continue
        if current_number and value:
            current_parts.append(value)
    if current_number and current_parts:
        references[current_number] = markdown_link_text(" ".join(current_parts))
    return references


def is_cell_security_markdown(markdown: str) -> bool:
    lowered = markdown.lower()
    return (
        "just a moment" in lowered
        or "performing security verification" in lowered
        or "enable javascript and cookies" in lowered
        or "are you a robot" in lowered
    )


def parse_browser_text_references(lines: list[str]) -> dict[str, str]:
    references: dict[str, str] = {}
    try:
        start = next(index for index, line in enumerate(lines) if line.strip() == "References") + 1
    except StopIteration:
        return references

    current_number = None
    current_parts: list[str] = []
    for line in lines[start:]:
        value = clean_text(line)
        if value in CELL_BROWSER_STOP_SECTIONS - {"References"}:
            break
        match = re.match(r"^(\d+)\.$", value)
        if match:
            if current_number and current_parts:
                references[current_number] = clean_text(" ".join(current_parts))
            current_number = match.group(1)
            current_parts = []
            continue
        if current_number and value and not is_cell_browser_skip_line(value):
            current_parts.append(value)
    if current_number and current_parts:
        references[current_number] = clean_text(" ".join(current_parts))
    return references


def browser_text_figure_blocks(lines: list[str], compact_pii: str, source_url: str) -> tuple[list[dict], set[int]]:
    figures = []
    skip_lines: set[int] = set()
    seen = set()
    in_article = False
    for index, line in enumerate(lines):
        value = clean_text(line)
        if value in CELL_DIRECT_START_TITLES:
            in_article = True
        if value in CELL_BROWSER_STOP_SECTIONS:
            break
        if not in_article:
            continue

        match = re.match(r"^Figure\s+(S?)(\d+)\s+(.+)", value, re.I)
        if not match:
            continue
        prefix, number_text, raw_title = match.groups()
        number = int(number_text)
        is_supplement = bool(prefix)
        figure_id = f"supp-{number}" if is_supplement else f"fig-{number}"
        if figure_id in seen:
            continue
        seen.add(figure_id)
        asset_name = f"figs{number}" if is_supplement else f"gr{number}"
        label = f"Figure S{number}" if is_supplement else f"Fig. {number}"
        figures.append(
            {
                "id": figure_id,
                "label": label,
                "type": "Supplementary figure" if is_supplement else "Main figure",
                "title": raw_title,
                "image": f"https://ars.els-cdn.com/content/image/1-s2.0-{compact_pii}-{asset_name}_lrg.jpg",
                "sourceUrl": f"{source_url}#figs{number}" if is_supplement else f"{source_url}#fig{number}",
                "caption": value,
            }
        )
        skip_lines.add(index)
        if index + 1 < len(lines) and is_cell_browser_skip_line(clean_text(lines[index + 1])):
            skip_lines.add(index + 1)

    return figures, skip_lines


def cell_local_figure_image(cache_dir: Path, figure_id: str) -> str:
    number_match = re.search(r"(\d+)", figure_id)
    variants = [figure_id]
    if number_match:
        number = int(number_match.group(1))
        variants.extend([f"fig{number}", f"gr{number}", f"figure-{number}", f"Figure{number}"])
    for extension in ("jpg", "jpeg", "png", "webp"):
        for stem in dict.fromkeys(variants):
            path = cache_dir / f"{stem}.{extension}"
            if path.exists():
                return "./" + path.as_posix()
    return ""


def cell_html_image_url(node, source_url: str) -> str:
    for selector, attr in (
        ("a.icon-full-screen[href]", "href"),
        ("img[data-viewer-src]", "data-viewer-src"),
        ("img[data-original]", "data-original"),
        ("img[data-src]", "data-src"),
        ("source[srcset]", "srcset"),
        ("img[srcset]", "srcset"),
        ("img[src]", "src"),
    ):
        tag = node.select_one(selector)
        if not tag:
            continue
        value = tag.get(attr, "")
        if not value:
            continue
        if attr == "srcset":
            value = value.split(",")[-1].strip().split(" ")[0]
        return absolute_url(value, source_url)
    return ""


def clean_cell_html_caption_node(node) -> str:
    if not node:
        return ""
    fragment = BeautifulSoup(str(node), "html.parser")
    for tag in fragment.select(
        "script, style, svg, button, .accordion__control, .figure__open__ctrl, "
        ".dropBlock__holder, .dropBlock__body__outer, .dropBlock__body, .citation, .external-links"
    ):
        tag.decompose()
    return clean_text(fragment.get_text(" ", strip=True))


def cell_html_figure_blocks(page_path: Path, source_url: str) -> dict[str, dict]:
    if not page_path.exists():
        return {}
    try:
        soup = BeautifulSoup(page_path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    except Exception:
        return {}

    figures: dict[str, dict] = {}
    for node in soup.select("figure[id], div.figure[id], div.fig[id], div[data-test='figure'][id]"):
        if node.find_parent(["figcaption"]):
            continue
        raw_id = node.get("id") or ""
        label_node = node.select_one(".figure__label, .caption__label, .fig-label, .figure-label")
        label_text = clean_cell_html_caption_node(label_node)
        match = re.match(r"fig(?:ure)?(\d+)$", raw_id, re.I) or re.match(
            r"(?:Fig\.?|Figure)\s+(\d+)\b", label_text, re.I
        )
        if not match:
            continue

        number = int(match.group(1))
        figure_id = f"fig-{number}"
        title_node = node.select_one(".figure__title__text")
        title = clean_cell_html_caption_node(title_node)
        content_node = node.select_one(".figure__caption__text__content")
        content = clean_cell_html_caption_node(content_node)
        if not content:
            caption_node = node.select_one("figcaption, .caption, .figure__caption, .fig-caption, .figure-caption")
            content = clean_cell_html_caption_node(caption_node)
            content = re.sub(rf"^Figure\s+{number}\s+{re.escape(title)}\s*", "", content, flags=re.I).strip()
            content = re.sub(r"^Show full caption\s+Figure viewer\s*", "", content, flags=re.I).strip()

        caption = clean_text(" ".join(part for part in [f"Figure {number} {title}".strip(), content] if part))
        figures[figure_id] = {
            "id": figure_id,
            "label": f"Fig. {number}",
            "type": "Main figure",
            "title": title,
            "image": cell_local_figure_image(page_path.parent, figure_id) or cell_html_image_url(node, source_url),
            "sourceUrl": f"{source_url}#fig{number}",
            "caption": caption[:10000],
        }
    return figures


def merge_cell_html_figure_blocks(figures: list[dict], page_path: Path, source_url: str) -> list[dict]:
    html_figures = cell_html_figure_blocks(page_path, source_url)
    if not html_figures:
        return figures

    merged = []
    seen = set()
    for figure in figures:
        replacement = html_figures.get(figure.get("id", ""))
        if replacement:
            updated = {**figure}
            for key in ("title", "image", "sourceUrl", "caption"):
                if replacement.get(key):
                    updated[key] = replacement[key]
            merged.append(updated)
            seen.add(updated["id"])
        else:
            merged.append(figure)
            seen.add(figure.get("id"))
    merged.extend(figure for figure_id, figure in html_figures.items() if figure_id not in seen)
    return merged


def is_browser_heading(value: str, next_value: str) -> bool:
    if value in {
        "Summary",
        "Introduction",
        "Results",
        "Discussion",
        "Limitations of the study",
        "Resource availability",
        "Lead contact",
        "Materials availability",
        "Data and code availability",
        "Acknowledgments",
        "Author contributions",
        "Declaration of interests",
        "STAR★Methods",
        "STAR Methods",
        "Key resources table",
        "Experimental model and study participant details",
        "Method details",
        "Quantification and statistical analysis",
    }:
        return True
    if not value or len(value) > 170:
        return False
    if is_cell_browser_skip_line(value) or value.startswith(("Figure ", "Video ", "Table ", "File ")):
        return False
    if "\t" in value or value.endswith((".", ",", ";", ":")):
        return False
    if re.match(r"^\d+\.$", value):
        return False
    if is_cell_browser_skip_line(next_value):
        return False
    return bool(next_value) and len(next_value) > 120


def is_cell_equation_line(value: str) -> bool:
    if not value or len(value) > 240:
        return False
    math_chars = re.findall(r"[\U0001D400-\U0001D7FF\u2200-\u22FF\u2300-\u23FF\u27E6-\u27EF\u2190-\u21FF]", value)
    if value in {"=", "+", "-", "−", "⎡", "⎢", "⎣", "⎤", "⎥", "⎦"}:
        return True
    if not math_chars:
        return False
    word_count = len(re.findall(r"[A-Za-z]{3,}", value))
    return word_count <= 2


def extract_cell_mathjax(page_path: Path) -> tuple[list[str], str]:
    if not page_path.exists():
        return [], ""
    try:
        soup = BeautifulSoup(page_path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    except Exception:
        return [], ""
    for tag in soup.select("script, mjx-menu"):
        tag.decompose()
    style = soup.select_one("style#MJX-CHTML-styles")
    equations = []
    for container in soup.select("mjx-container"):
        for attr in ("tabindex", "ctxtmenu_counter"):
            if container.has_attr(attr):
                del container[attr]
        equations.append(str(container))
    return equations, (style.string or "") if style else ""


def parse_browser_text_sections(
    lines: list[str],
    skip_lines: set[int],
    main_figure_count: int,
    equation_html_blocks: list[str] | None = None,
) -> list[dict]:
    sections = []
    counter = [0]
    current = None
    article_started = False
    previous_was_heading = False
    pending_equation: list[str] = []
    equation_html_blocks = equation_html_blocks or []
    equation_html_index = [0]

    def push_equation() -> None:
        nonlocal pending_equation
        if not current or not pending_equation:
            pending_equation = []
            return
        text = "\n".join(pending_equation)
        counter[0] += 1
        paragraph = {
            "id": f"p-{counter[0]}",
            "text": text,
            "kind": "equation",
            "figures": [],
            "citations": [],
        }
        if equation_html_index[0] < len(equation_html_blocks):
            paragraph["html"] = equation_html_blocks[equation_html_index[0]]
            equation_html_index[0] += 1
        current["paragraphs"].append(paragraph)
        pending_equation = []

    for index, line in enumerate(lines):
        value = clean_text(line)
        if not value or index in skip_lines or is_cell_browser_skip_line(value):
            push_equation()
            continue
        if value in CELL_BROWSER_STOP_SECTIONS:
            push_equation()
            break
        if not article_started and value not in CELL_DIRECT_START_TITLES:
            continue

        next_value = ""
        for lookahead in lines[index + 1 : index + 6]:
            next_value = clean_text(lookahead)
            if next_value:
                break

        if is_browser_heading(value, next_value):
            push_equation()
            article_started = True
            base = slugify(value, "section")
            existing = {section["id"] for section in sections}
            section_id = base
            suffix = 2
            while section_id in existing:
                section_id = f"{base}-{suffix}"
                suffix += 1
            current = {"id": section_id, "title": value, "paragraphs": []}
            sections.append(current)
            previous_was_heading = True
            continue

        if not current or value.startswith(("•", "ADVERTISEMENT", "SCROLL TO CONTINUE")):
            push_equation()
            continue
        if value.startswith(("Figure ", "Video ", "Table ", "File ")):
            push_equation()
            continue
        if "\t" in value and previous_was_heading:
            push_equation()
            continue
        if is_cell_equation_line(value):
            pending_equation.append(line.strip())
            previous_was_heading = False
            continue

        push_equation()
        text = recover_cell_browser_citations(value)
        counter[0] += 1
        current["paragraphs"].append(
            {
                "id": f"p-{counter[0]}",
                "text": text,
                "figures": text_figure_ids(text, main_figure_count),
                "citations": paragraph_citations(text),
            }
        )
        previous_was_heading = False

    push_equation()
    return [section for section in sections if section["paragraphs"]]


def synthesize_cell_supplementary_figures_from_mentions(
    sections: list[dict],
    figures: list[dict],
    compact_pii: str,
    source_url: str,
) -> list[dict]:
    existing_ids = {figure["id"] for figure in figures}
    mentioned_numbers = sorted(
        {
            int(match.group(1))
            for section in sections
            for paragraph in section.get("paragraphs", [])
            for figure_id in paragraph.get("figures", [])
            for match in [re.match(r"supp-(\d+)$", figure_id)]
            if match and figure_id not in existing_ids
        }
    )
    return [
        {
            "id": f"supp-{number}",
            "label": f"Figure S{number}",
            "type": "Supplementary figure",
            "title": f"Supplementary figure {number}",
            "image": f"https://ars.els-cdn.com/content/image/1-s2.0-{compact_pii}-figs{number}_lrg.jpg",
            "sourceUrl": f"{source_url}#figs{number}",
            "caption": "Supplementary figure detected from in-text mentions.",
        }
        for number in mentioned_numbers
    ]


def captured_cell_supplementary_figures(
    cache_key: str,
    figures: list[dict],
    assets_dir: str | Path = "assets",
) -> list[dict]:
    cache_dir = Path(assets_dir) / "imports" / cache_key
    if not cache_dir.exists():
        return []

    numbers = sorted(
        {
            int(match.group(1))
            for figure in figures
            if figure.get("id", "").startswith("supp-")
            for match in [re.search(r"(\d+)", figure["id"])]
            if match
        }
    )
    pdfs = sorted(cache_dir.glob("document-s*.pdf")) + sorted(cache_dir.glob("mmc*.pdf"))
    for candidate in sorted(cache_dir.iterdir()):
        if candidate.is_file() and candidate not in pdfs and candidate.read_bytes()[:4] == b"%PDF":
            pdfs.append(candidate)
    pdfs = sorted(dict.fromkeys(pdfs), key=lambda path: (0 if path.name == "document-s1.pdf" else 1, path.stat().st_size))
    rendered: dict[str, dict] = {}
    for pdf_path in pdfs:
        if not pdf_path.exists() or pdf_path.read_bytes()[:4] != b"%PDF":
            continue
        pdf_numbers = discover_cell_supplement_pdf_numbers(pdf_path)
        if not pdf_numbers:
            continue
        render_numbers = sorted(set(numbers) | set(pdf_numbers))
        for figure in render_cell_supplementary_pdf(
            pdf_path,
            render_numbers,
            cache_dir,
            "./" + pdf_path.as_posix(),
            "captured-figure-s",
            image_page_offset=0,
            stitch_page_ranges=False,
            crop_caption_heading=True,
        ):
            rendered.setdefault(figure["id"], figure)
        if rendered:
            break
    return list(rendered.values())


def parse_cell_browser_text_article(
    url: str,
    pii: str,
    body_path: Path,
    crossref_message: dict | None = None,
) -> dict:
    compact_pii = re.sub(r"[^A-Za-z0-9]", "", pii)
    cache_key = cell_cache_key(url, pii)
    meta_path = body_path.parent / "browser-meta.json"
    browser_meta = {}
    if meta_path.exists():
        try:
            browser_meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            browser_meta = {}
    if not browser_meta.get("title"):
        page_path = body_path.parent / "browser-page.html"
        if page_path.exists():
            try:
                page_soup = BeautifulSoup(page_path.read_text(encoding="utf-8", errors="replace"), "html.parser")
                browser_meta["title"] = (
                    page_soup.select_one('meta[name="citation_title"]') or {}
                ).get("content", "")
                browser_meta["journal"] = (
                    page_soup.select_one('meta[name="citation_journal_title"]') or {}
                ).get("content", "")
                browser_meta["doi"] = (
                    page_soup.select_one('meta[name="citation_doi"]') or {}
                ).get("content", "")
                browser_meta["authors"] = ", ".join(
                    meta.get("content", "")
                    for meta in page_soup.select('meta[name="citation_author"]')
                    if meta.get("content")
                )
            except Exception:
                browser_meta = {}
    if crossref_message is None:
        try:
            crossref_message = fetch_crossref_metadata_by_pii(compact_pii)
        except Exception:
            crossref_message = {}
    crossref_message = crossref_message or {}
    lines = body_path.read_text(encoding="utf-8", errors="replace").splitlines()

    title = (crossref_message.get("title") or [browser_meta.get("title") or "Untitled Cell Press article"])[0]
    page_path = body_path.parent / "browser-page.html"
    equation_html_blocks, math_styles = extract_cell_mathjax(page_path)
    figures, skip_lines = browser_text_figure_blocks(lines, compact_pii, url)
    figures = merge_cell_html_figure_blocks(figures, page_path, url)
    main_figure_count = sum(1 for figure in figures if figure["id"].startswith("fig-"))
    sections = parse_browser_text_sections(lines, skip_lines, main_figure_count, equation_html_blocks)
    figures.extend(synthesize_cell_supplementary_figures_from_mentions(sections, figures, compact_pii, url))
    rendered_supplements = captured_cell_supplementary_figures(cache_key, figures)
    if rendered_supplements:
        replacements = {figure["id"]: figure for figure in rendered_supplements}
        existing_figure_ids = {figure["id"] for figure in figures}
        figures = [replacements.get(figure["id"], figure) for figure in figures]
        figures.extend(figure for figure in rendered_supplements if figure["id"] not in existing_figure_ids)
    return {
        "sourceUrl": url,
        "sourceMirrorUrl": "Browser-visible local text cache",
        "title": title,
        "journal": (crossref_message.get("container-title") or [browser_meta.get("journal") or "Cell Press"])[0],
        "published": crossref_date(crossref_message),
        "doi": crossref_message.get("DOI", "") or browser_meta.get("doi", ""),
        "authors": crossref_authors(crossref_message) or browser_meta.get("authors", ""),
        "sections": sections,
        "figures": sorted(
            figures,
            key=lambda figure: (
                0 if figure["id"].startswith("fig-") else 1,
                int(re.search(r"(\d+)", figure["id"]).group(1)),
            ),
        ),
        "references": parse_browser_text_references(lines),
        "cacheKey": cache_key,
        "sourceFamily": "cell-browser-cache",
        "mathStyles": math_styles,
    }


def parse_markdown_sections(lines: list[str], skip_lines: set[int], main_figure_count: int) -> list[dict]:
    sections = []
    counter = [0]
    current = None
    current_skip = True
    article_started = False
    stop = False

    def push_paragraph(raw_text: str) -> None:
        if not current or current_skip:
            return
        raw_value = raw_text.strip()
        if is_cell_markdown_noise_line(raw_value):
            return
        text = markdown_link_text(raw_text)
        if not text or text == "•" or text.startswith("|"):
            return
        counter[0] += 1
        figures = []
        for figure_id in markdown_figure_ids(raw_text):
            add_unique(figures, figure_id)
        for figure_id in text_figure_ids(text, main_figure_count):
            add_unique(figures, figure_id)
        current["paragraphs"].append(
            {
                "id": f"p-{counter[0]}",
                "text": text,
                "figures": figures,
                "citations": paragraph_citations(text),
            }
        )

    for index, line in enumerate(lines):
        value = line.strip()
        heading = re.match(r"^(#{2,4})\s+(.+)", value)
        if heading:
            title = markdown_link_text(heading.group(2))
            if not article_started:
                if title in CELL_DIRECT_START_TITLES:
                    article_started = True
                else:
                    current = None
                    current_skip = True
                    continue
            if title in CELL_DIRECT_STOP_SECTIONS:
                stop = True
                current = None
                continue
            if stop:
                continue
            current_skip = title in CELL_DIRECT_SKIP_SECTIONS or title.startswith("Supplemental information")
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

        if (
            stop
            or index in skip_lines
            or not value
            or value.startswith("[![")
            or value.startswith("|")
            or is_cell_markdown_noise_line(value)
        ):
            continue
        push_paragraph(value)

    return [section for section in sections if section["paragraphs"]]


def parse_cell_direct_article(
    url: str,
    pii: str,
    assets_dir: str | Path = "assets",
    crossref_message: dict | None = None,
) -> dict:
    assets_path = Path(assets_dir)
    cache_key = cell_cache_key(url, pii)
    cache_dir = assets_path / "imports" / cache_key
    cache_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = cache_dir / "article.md"
    browser_body_path = cache_dir / "browser-body.txt"

    if browser_body_path.exists():
        browser_text = browser_body_path.read_text(encoding="utf-8", errors="replace")
        if any(clean_text(line) in CELL_DIRECT_START_TITLES for line in browser_text.splitlines()):
            compact_pii = re.sub(r"[^A-Za-z0-9]", "", pii)
            crossref_message = crossref_message or {}
            if not crossref_message:
                try:
                    crossref_message = fetch_crossref_metadata_by_pii(compact_pii)
                except Exception:
                    crossref_message = {}
            return parse_cell_browser_text_article(url, pii, browser_body_path, crossref_message)

    if markdown_path.exists():
        markdown = markdown_path.read_text(encoding="utf-8")
    else:
        reader_url = f"https://r.jina.ai/http://r.jina.ai/http://{url}"
        markdown = fetch_text(reader_url)
        markdown_path.write_text(markdown, encoding="utf-8")

    compact_pii = re.sub(r"[^A-Za-z0-9]", "", pii)
    crossref_message = crossref_message or {}
    if not crossref_message:
        try:
            crossref_message = fetch_crossref_metadata_by_pii(compact_pii)
        except Exception:
            crossref_message = {}
    if is_cell_security_markdown(markdown):
        if browser_body_path.exists():
            return parse_cell_browser_text_article(url, pii, browser_body_path, crossref_message)
        raise ValueError(
            "Cell.com security verification blocked the text snapshot for this paper. "
            "Open the article in the browser first, then capture a browser-visible text cache."
        )

    lines = markdown.splitlines()
    plain_text_snapshot = not re.search(r"^#{2,4}\s+", markdown, re.M) and any(
        clean_text(line) in CELL_DIRECT_START_TITLES for line in lines
    )
    if plain_text_snapshot:
        return parse_cell_browser_text_article(url, pii, markdown_path, crossref_message)

    title_match = re.search(r"^Title:\s*(.+)$", markdown, re.M)
    title = markdown_link_text(title_match.group(1)) if title_match else "Untitled Cell Press article"
    doi_match = re.search(r"https://www\.cell\.com/cms/(10\.1016/[^/]+)/", markdown)
    doi = doi_match.group(1) if doi_match else (crossref_message or {}).get("DOI", "")

    if doi and not crossref_message:
        try:
            crossref_message = fetch_crossref_metadata(doi)
        except Exception:
            crossref_message = {}
    figures, skip_lines = extract_markdown_figure_blocks(lines, url)
    skip_lines.update(extract_markdown_media_blocks(lines))
    for figure in figures:
        asset_match = re.search(r"/main\.assets/((?:gr|figs)\d+)_lrg\.jpg", figure["image"], re.I)
        if asset_match:
            figure["image"] = (
                f"https://ars.els-cdn.com/content/image/1-s2.0-{compact_pii}-"
                f"{asset_match.group(1).lower()}_lrg.jpg"
            )
    main_figure_count = sum(1 for figure in figures if figure["id"].startswith("fig-"))
    sections = parse_markdown_sections(lines, skip_lines, main_figure_count)
    figures.extend(synthesize_cell_supplementary_figures_from_mentions(sections, figures, compact_pii, url))

    article = {
        "sourceUrl": url,
        "sourceMirrorUrl": "Jina Reader markdown snapshot",
        "title": title,
        "journal": (crossref_message.get("container-title") or ["Cell"])[0],
        "published": crossref_date(crossref_message),
        "doi": doi,
        "authors": crossref_authors(crossref_message),
        "sections": sections,
        "figures": sorted(
            figures,
            key=lambda figure: (
                0 if figure["id"].startswith("fig-") else 1,
                int(re.search(r"(\d+)", figure["id"]).group(1)),
            ),
        ),
        "references": parse_markdown_references(lines),
        "cacheKey": cache_key,
        "sourceFamily": "cell-direct",
    }
    return article



def parse_cell_article(url: str, assets_dir: str | Path = "assets") -> dict:
    match = CELL_URL_RE.match(url)
    if not match:
        raise ValueError("Cell Press URLs should look like https://www.cell.com/.../fulltext/<PII>.")

    pii = urllib.parse.unquote(match.group("pii"))
    url = canonical_cell_url(url, pii)
    assets_path = Path(assets_dir)
    cache_key = cell_cache_key(url, pii)
    browser_body_path = assets_path / "imports" / cache_key / "browser-body.txt"
    if browser_body_path.exists():
        return parse_cell_browser_text_article(url, pii, browser_body_path)

    pmc_url = resolve_cell_pmc_url(pii)
    if not pmc_url:
        return parse_cell_direct_article(url, pii, assets_dir)

    cache_dir = assets_path / "imports" / cache_key
    cache_dir.mkdir(parents=True, exist_ok=True)
    html_path = cache_dir / "pmc.html"
    if html_path.exists():
        html = html_path.read_text(encoding="utf-8")
    else:
        html = fetch_text(pmc_url)
        html_path.write_text(html, encoding="utf-8")

    soup = BeautifulSoup(html, "html.parser")
    article = parse_pmc_metadata(soup, url, pmc_url)

    figures = parse_pmc_main_figures(soup, pmc_url)
    main_figure_count = len(figures)
    article["sections"] = parse_pmc_sections(soup, main_figure_count)

    existing_ids = {figure["id"] for figure in figures}
    for figure in render_cell_supplementary_figures(soup, cache_key, assets_path, pmc_url):
        if figure["id"] not in existing_ids:
            figures.append(figure)
            existing_ids.add(figure["id"])

    article["figures"] = sorted(
        figures,
        key=lambda figure: (
            0 if figure["id"].startswith("fig-") else 1,
            int(re.search(r"(\d+)", figure["id"]).group(1)),
        ),
    )
    article["references"] = parse_pmc_references(soup)
    article["cacheKey"] = cache_key
    article["sourceFamily"] = "cell-pmc"
    return article
