from __future__ import annotations

from .common import *


SCIENCE_BODY_START_TITLES = {
    "Abstract",
    "Introduction",
    "Results",
    "Discussion",
    "Materials and Methods",
    "Materials and methods",
}
SCIENCE_BODY_STOP_TITLES = {
    "References and Notes",
    "References",
    "Acknowledgments",
    "Supplementary Materials",
    "Supplementary Material",
    "Funding",
    "Author contributions",
    "Competing interests",
}


def science_meta_content(soup: BeautifulSoup, name: str) -> str:
    tag = soup.find("meta", attrs={"name": name}) or soup.find("meta", attrs={"property": name})
    return clean_text(tag.get("content", "")) if tag else ""


def science_doi_from_url(url: str) -> str:
    match = SCIENCE_URL_RE.match(url)
    return urllib.parse.unquote(match.group("doi")).rstrip("/") if match else ""


def parse_science_metadata(soup: BeautifulSoup, url: str) -> dict:
    authors = [
        clean_text(tag.get("content", ""))
        for tag in soup.select('meta[name="citation_author"]')
        if tag.get("content")
    ]
    if not authors:
        authors = [
            clean_text(link.get_text(" ", strip=True))
            for link in soup.select('.authors [property="author"] a[href^="#con"], .contributors [property="author"] a[href^="#con"]')
            if clean_text(link.get_text(" ", strip=True))
        ]
    if not authors:
        author_text = clean_text((soup.select_one(".contributors, .authors") or BeautifulSoup("", "html.parser")).get_text(" ", strip=True))
        author_text = re.sub(r"https?://orcid\.org/\S+", "", author_text)
        author_text = re.sub(r"\[\s*\.\.\.\s*\]", "", author_text)
        authors = [
            clean_text(part)
            for part in re.split(r"\s*,\s*|\s+\band\b\s+", author_text)
            if clean_text(part) and not re.search(r"Authors Info|Affiliations|Expand All", part, re.I)
        ]
    return {
        "sourceUrl": canonical_science_url(url),
        "sourceMirrorUrl": "Browser-visible local page cache",
        "title": science_meta_content(soup, "citation_title")
        or science_meta_content(soup, "og:title")
        or clean_text((soup.select_one("h1") or soup.title).get_text(" ", strip=True)),
        "journal": science_meta_content(soup, "citation_journal_title") or "Science",
        "published": science_meta_content(soup, "citation_publication_date"),
        "doi": science_meta_content(soup, "citation_doi") or science_doi_from_url(url),
        "authors": ", ".join(dict.fromkeys(authors)),
    }


def science_figure_id(raw_id: str, label: str = "") -> str | None:
    value = raw_id or label
    match = re.search(r"(?:fig|f|F)(?:ure)?[-_ ]?S?(\d+)$", value)
    if match and re.search(r"S\d+", value, re.I):
        return f"supp-{int(match.group(1))}"
    match = re.search(r"(?:fig|f|F)(?:ure)?[-_ ]?(\d+)$", value)
    if match:
        return f"fig-{int(match.group(1))}"
    match = re.search(r"\bFig(?:ure)?\.?\s*S(\d+)", label, re.I)
    if match:
        return f"supp-{int(match.group(1))}"
    match = re.search(r"\bFig(?:ure)?\.?\s*(\d+)", label, re.I)
    if match:
        return f"fig-{int(match.group(1))}"
    return None


def science_image_url(node, base_url: str) -> str:
    for selector, attr in (
        ("img[data-src]", "data-src"),
        ("img[data-original]", "data-original"),
        ("img[src]", "src"),
        ("source[srcset]", "srcset"),
        ("img[srcset]", "srcset"),
    ):
        tag = node.select_one(selector)
        if not tag:
            continue
        value = tag.get(attr, "")
        if not value:
            continue
        if attr == "srcset":
            value = value.split(",")[-1].strip().split(" ")[0]
        return absolute_url(value, base_url)
    return ""


def science_local_figure_image(cache_dir: Path, figure_id: str) -> str:
    number_match = re.search(r"(\d+)", figure_id)
    variants = [figure_id]
    if number_match:
        number = int(number_match.group(1))
        variants.extend([f"F{number}", f"fig{number}", f"figure-{number}"])
    for extension in ("jpg", "jpeg", "png", "webp"):
        for stem in variants:
            path = cache_dir / f"{stem}.{extension}"
            if path.exists():
                return "./" + path.as_posix()
    return ""


def parse_science_figures(soup: BeautifulSoup, url: str, cache_dir: Path | None = None) -> list[dict]:
    figures = []
    seen = set()
    candidates = soup.select("figure[id], div.figure[id], div.fig[id], div[id^='F'], div[id^='fig']")
    for node in candidates:
        if node.find_parent(["figcaption"]):
            continue
        caption_node = node.select_one("figcaption, .caption, .figure__caption, .fig-caption, .figure-caption")
        label_node = node.select_one(".figure__label, .caption__label, .fig-label, .figure-label, strong")
        label = clean_text(label_node.get_text(" ", strip=True)) if label_node else ""
        text = clean_text((caption_node or node).get_text(" ", strip=True))
        if not label:
            label_match = re.match(r"((?:Fig\.?|Figure)\s+S?\d+\.?)", text, re.I)
            label = clean_text(label_match.group(1)) if label_match else node.get("id", "")
        figure_id = science_figure_id(node.get("id", ""), label)
        if not figure_id or figure_id in seen:
            continue
        image = science_image_url(node, url)
        if cache_dir:
            image = science_local_figure_image(cache_dir, figure_id) or image
        if not image and not caption_node:
            continue
        title = text
        title = re.sub(rf"^{re.escape(label)}\s*", "", title, flags=re.I).strip()
        title = title.split(". ")[0].strip()[:180] or label
        figures.append(
            {
                "id": figure_id,
                "label": label.rstrip(".") or ("Figure " + figure_id.split("-")[1]),
                "type": "Supplementary figure" if figure_id.startswith("supp-") else "Main figure",
                "title": title,
                "image": image,
                "sourceUrl": f"{canonical_science_url(url)}#{node.get('id', '')}",
                "caption": text[:1800],
            }
        )
        seen.add(figure_id)
    return sorted(
        figures,
        key=lambda figure: (
            0 if figure["id"].startswith("fig-") else 1,
            int(re.search(r"\d+", figure["id"]).group(0)),
        ),
    )


def science_paragraph_text(node) -> str:
    clone = BeautifulSoup(str(node), "html.parser")
    for sup in clone.select("sup"):
        numbers = []
        for link in sup.select("a[href]"):
            value = clean_text(link.get_text(" ", strip=True))
            if re.fullmatch(r"\d+(?:[-,\u2013]\d+)?", value):
                numbers.append(value)
        if numbers:
            sup.replace_with(f"[{','.join(numbers)}]")
    for link in clone.select("a[href]"):
        href = link.get("href", "")
        value = clean_text(link.get_text(" ", strip=True))
        if re.search(r"#(?:core-)?(?:ref|R|B|bib)\d+$", href, re.I) and re.fullmatch(r"\d+", value):
            link.replace_with(f"[{value}]")
    return clean_text(clone.get_text(" ", strip=True))


def science_paragraph_citations(node, text: str) -> list:
    citations: list = []
    for citation in science_text_citation_ranges(text):
        if citation not in citations:
            citations.append(citation)
    for citation in paragraph_citations(text):
        add_unique(citations, citation)
    for link in node.select("a[href]"):
        href = link.get("href", "")
        match = re.search(r"#(?:core-)?(?:ref|R|B|bib)(\d+)$", href, re.I)
        if match:
            add_unique(citations, match.group(1))
    return citations


def science_text_citation_ranges(text: str) -> list[dict[str, str]]:
    citations = []
    for match in re.finditer(r"\(((?:\d+\s*(?:,|and|\u2013|-)?\s*){1,8})\)", text):
        raw_numbers = match.group(1)
        if not re.fullmatch(r"\d+(?:\s*(?:,|and|\u2013|-)\s*\d+)*", raw_numbers):
            continue
        numbers = []
        parts = re.split(r"\s*(?:,|and)\s*", raw_numbers)
        for part in parts:
            range_match = re.fullmatch(r"(\d+)\s*(?:\u2013|-)\s*(\d+)", part)
            if range_match:
                start, end = int(range_match.group(1)), int(range_match.group(2))
                if 0 < start <= end <= start + 12:
                    numbers.extend(str(number) for number in range(start, end + 1))
                continue
            if re.fullmatch(r"\d+", part):
                numbers.append(str(int(part)))
        if not numbers:
            continue
        citation = {"key": ",".join(numbers), "text": match.group(0)}
        if citation not in citations:
            citations.append(citation)
    return citations


def science_heading_text(node) -> str:
    title = clean_text(node.get_text(" ", strip=True))
    title = re.sub(r"^Section\s+", "", title, flags=re.I)
    return title


def parse_science_sections(soup: BeautifulSoup, main_figure_count: int, body_text: str = "") -> list[dict]:
    if body_text:
        browser_sections = parse_science_browser_text_sections(body_text.splitlines(), main_figure_count)
        if sum(len(section["paragraphs"]) for section in browser_sections) >= 4:
            return browser_sections

    root = (
        soup.select_one("article")
        or soup.select_one(".article__body")
        or soup.select_one(".hlFld-Fulltext")
        or soup.select_one("main")
        or soup
    )
    sections = []
    current = None
    counter = [0]
    started = False

    def start_section(title: str) -> None:
        nonlocal current, started
        started = True
        section_id = slugify(title, "section")
        existing = {section["id"] for section in sections}
        base = section_id
        suffix = 2
        while section_id in existing:
            section_id = f"{base}-{suffix}"
            suffix += 1
        current = {"id": section_id, "title": title, "paragraphs": []}
        sections.append(current)

    for node in root.find_all(["h1", "h2", "h3", "p"], recursive=True):
        if node.find_parent(["figure", "figcaption", "table", "nav"]):
            continue
        if node.name in {"h1", "h2", "h3"}:
            title = science_heading_text(node)
            if not title or len(title) > 180:
                continue
            if title in SCIENCE_BODY_STOP_TITLES:
                break
            if not started and title not in SCIENCE_BODY_START_TITLES:
                continue
            start_section(title)
            continue
        if node.name != "p":
            continue
        text = science_paragraph_text(node)
        if not text or len(text) < 30:
            continue
        if not started:
            start_section("Abstract")
        if not current:
            continue
        counter[0] += 1
        figures = []
        for figure_id in text_figure_ids(text, main_figure_count):
            add_unique(figures, figure_id)
        for figure_id in text_table_ids(text):
            add_unique(figures, figure_id)
        current["paragraphs"].append(
            {
                "id": f"p-{counter[0]}",
                "text": text,
                "figures": figures,
                "citations": science_paragraph_citations(node, text),
            }
        )

    sections = [section for section in sections if section["paragraphs"]]
    if sections:
        return sections
    return parse_science_browser_text_sections(body_text.splitlines(), main_figure_count)


def parse_science_browser_text_sections(lines: list[str], main_figure_count: int) -> list[dict]:
    sections = []
    current = None
    counter = [0]
    started = False
    skipping_figure_caption = False
    start_index = 0
    for index, line in enumerate(lines):
        value = clean_text(line)
        if value not in SCIENCE_BODY_START_TITLES:
            continue
        next_value = ""
        for lookahead in lines[index + 1 : index + 6]:
            next_value = clean_text(lookahead)
            if next_value:
                break
        if len(next_value) > 120:
            start_index = index
            break

    for index, line in enumerate(lines[start_index:], start_index):
        value = clean_text(line)
        if not value:
            continue
        if started and value in SCIENCE_BODY_STOP_TITLES:
            break
        next_value = ""
        for lookahead in lines[index + 1 : index + 5]:
            next_value = clean_text(lookahead)
            if next_value:
                break
        is_heading = value in SCIENCE_BODY_START_TITLES or (
            started
            and len(value) < 120
            and bool(next_value)
            and len(next_value) > 100
            and not value.endswith((".", ",", ";", ":"))
            and value not in {"OPEN IN VIEWER", "Expand for more", "DOWNLOAD", "SIGN UP"}
            and not re.fullmatch(r"[\W_]+", value)
        )
        if is_heading:
            skipping_figure_caption = False
            started = True
            section_id = slugify(value, "section")
            existing = {section["id"] for section in sections}
            base = section_id
            suffix = 2
            while section_id in existing:
                section_id = f"{base}-{suffix}"
                suffix += 1
            current = {"id": section_id, "title": value, "paragraphs": []}
            sections.append(current)
            continue
        if value == "OPEN IN VIEWER":
            skipping_figure_caption = True
            continue
        if skipping_figure_caption:
            if value == "Expand for more":
                skipping_figure_caption = False
                continue
            continue
        if value in {
            "SIGN UP",
            "SIGN UP FOR THE SCIENCE eTOC",
            "Get the latest table of contents from Science delivered right to you!",
        }:
            continue
        if not started or not current or len(value) < 45:
            continue
        if value.startswith(("Fig. ", "Figure ", "Table ", "Supplementary")) or value in {"OPEN IN VIEWER", "Expand for more"}:
            continue
        if current["title"] == "Abstract" and current["paragraphs"] and len(value) > 200:
            section_id = "introduction"
            existing = {section["id"] for section in sections}
            suffix = 2
            while section_id in existing:
                section_id = f"introduction-{suffix}"
                suffix += 1
            current = {"id": section_id, "title": "Introduction", "paragraphs": []}
            sections.append(current)
        counter[0] += 1
        current["paragraphs"].append(
            {
                "id": f"p-{counter[0]}",
                "text": value,
                "figures": text_figure_ids(value, main_figure_count),
                "citations": science_text_citation_ranges(value),
            }
        )
    return [section for section in sections if section["paragraphs"]]


def parse_science_references(soup: BeautifulSoup, body_text: str = "") -> dict[str, str]:
    references = {}
    candidates = soup.select(
        "li[id^='core-R'], li[id^='ref'], li[id^='R'], li[id^='B'], "
        ".ref-list li, .references li, ol.citation-list li, div.citations[id^='R']"
    )
    for index, item in enumerate(candidates, start=1):
        raw_id = item.get("id", "")
        match = re.search(r"(\d+)$", raw_id)
        key = match.group(1) if match else str(index)
        content = item.select_one(".citation-content") or item
        text = clean_text(content.get_text(" ", strip=True))
        if text and key not in references:
            references[key] = text
    if references:
        return references

    lines = body_text.splitlines()
    starts = [
        index
        for index, line in enumerate(lines)
        if clean_text(line) in {"References and Notes", "References"}
        and any(re.fullmatch(r"\d+\.?", clean_text(item)) for item in lines[index + 1 : index + 8])
    ]
    if not starts:
        return references
    start = starts[-1] + 1
    current_key = None
    parts = []
    for line in lines[start:]:
        value = clean_text(line)
        if value in {"Acknowledgments", "Supplementary Materials", "Metrics"}:
            break
        match = re.match(r"^(\d+)\.?\s*(.*)", value)
        if match:
            if current_key and parts:
                references[current_key] = clean_text(" ".join(parts))
            current_key = match.group(1)
            parts = [match.group(2)] if match.group(2) else []
        elif current_key and value:
            parts.append(value)
    if current_key and parts:
        references[current_key] = clean_text(" ".join(parts))
    return references


def science_supplement_pdf_candidates(cache_dir: Path) -> list[Path]:
    pdfs = sorted(cache_dir.glob("*_sm.pdf")) + sorted(cache_dir.glob("*supp*.pdf"))
    pdfs.extend(
        path
        for path in sorted(cache_dir.glob("*.pdf"))
        if path not in pdfs and "mdar" not in path.name.lower() and path.read_bytes()[:4] == b"%PDF"
    )
    return [path for path in dict.fromkeys(pdfs) if path.exists() and path.read_bytes()[:4] == b"%PDF"]


def science_supplement_pdf_url(cache_dir: Path) -> str:
    links_path = cache_dir / "browser-links.json"
    if not links_path.exists():
        return ""
    try:
        links = json.loads(links_path.read_text(encoding="utf-8"))
    except Exception:
        return ""
    for link in links:
        href = link.get("href") or ""
        combined = f"{link.get('text', '')} {href}"
        if href.lower().endswith(".pdf") and (
            "_sm.pdf" in href.lower()
            or re.search(r"supplement(?:ary|al)?|supporting\s+information", combined, re.I)
        ):
            return href
    return ""


def science_supplement_clean_line(line: str) -> str:
    value = clean_text(line)
    if not value:
        return ""
    if value in {"Submitted Manuscript: Confidential"}:
        return ""
    if value.startswith("Template revised"):
        return ""
    if re.fullmatch(r"\d+", value):
        return ""
    return value


def science_supplement_methods_stop(value: str) -> bool:
    return bool(
        re.match(r"^(?:Fig\.?\s*S\d+|Figs\.?\s*S\d+|Table\s*S\d+|Supplementary Text|References(?: and Notes)?)\b", value, re.I)
        or re.match(r"^table\s*S\d+\b", value, re.I)
    )


def science_supplement_heading(value: str) -> bool:
    if not value or len(value) > 110:
        return False
    if value.endswith((".", ",", ";", ":", ")")):
        return False
    if re.search(r"\d", value):
        return False
    if not re.search(r"[A-Za-z]", value):
        return False
    words = value.split()
    return 1 <= len(words) <= 9 and not value[0].islower()


def extract_science_supplement_methods(
    cache_dir: Path,
    main_figure_count: int,
    paragraph_start: int,
) -> dict | None:
    try:
        import fitz
    except Exception:
        return None

    pdfs = science_supplement_pdf_candidates(cache_dir)
    if not pdfs:
        return None

    doc = fitz.open(pdfs[0])
    started = False
    heading = ""
    current: list[str] = []
    paragraphs = []
    paragraph_number = paragraph_start

    def flush() -> None:
        nonlocal heading, current, paragraph_number
        text = clean_text(" ".join(current))
        if not text:
            return
        if heading:
            text = f"{heading}. {text}"
        if len(text) < 45:
            heading = ""
            current = []
            return
        paragraph_number += 1
        figures = []
        for figure_id in text_figure_ids(text, main_figure_count):
            add_unique(figures, figure_id)
        for figure_id in text_table_ids(text):
            add_unique(figures, figure_id)
        paragraphs.append(
            {
                "id": f"p-{paragraph_number}",
                "text": text,
                "figures": figures,
                "citations": science_text_citation_ranges(text),
            }
        )
        heading = ""
        current = []

    for page_index, page in enumerate(doc):
        page_text = page.get_text("text")
        is_listing_page = page_index == 0 and re.search(r"The PDF file includes", page_text, re.I)
        blocks = sorted(page.get_text("blocks"), key=lambda item: (item[1], item[0]))
        for block in blocks:
            for raw_line in str(block[4]).splitlines():
                value = science_supplement_clean_line(raw_line)
                if not value:
                    continue
                if not started:
                    if value == "Materials and Methods" and not is_listing_page:
                        started = True
                    continue
                if science_supplement_methods_stop(value):
                    flush()
                    doc.close()
                    if not paragraphs:
                        return None
                    return {
                        "id": "supplementary-materials-and-methods",
                        "title": "Supplementary Materials and Methods",
                        "paragraphs": paragraphs,
                    }
                if value == "Materials and Methods":
                    continue
                if science_supplement_heading(value):
                    flush()
                    heading = value
                    current = []
                    continue
                current.append(value)
    flush()
    doc.close()
    if not paragraphs:
        return None
    return {
        "id": "supplementary-materials-and-methods",
        "title": "Supplementary Materials and Methods",
        "paragraphs": paragraphs,
    }


def discover_science_supplement_pdf_numbers(pdf_path: Path) -> list[int]:
    try:
        import fitz
    except Exception:
        return []
    numbers = set()
    doc = fitz.open(pdf_path)
    for page in doc:
        for number in re.findall(r"\bFig\.?\s*S\s*(\d+)\b", page.get_text("text"), re.I):
            numbers.add(int(number))
    doc.close()
    return sorted(numbers)


def science_supplement_page_map(pdf_path: Path) -> dict[int, int]:
    try:
        import fitz
    except Exception:
        return {}
    page_map = {}
    doc = fitz.open(pdf_path)
    for index, page in enumerate(doc):
        text = page.get_text("text")
        for line in text.splitlines():
            match = re.match(r"\s*Fig\.?\s*S\s*(\d+)\b", line, re.I)
            if match:
                page_map.setdefault(int(match.group(1)), index)
    doc.close()
    return page_map


def extract_science_supplement_caption(page_text: str, number: int) -> str:
    match = re.search(
        rf"(Fig\.?\s*S\s*{number}\b.*?)(?=\n\s*Fig\.?\s*S\s*\d+\b|\Z)",
        page_text,
        re.I | re.S,
    )
    return clean_text(match.group(1)) if match else clean_text(page_text)[:900]


def render_science_supplementary_pdf(
    pdf_path: Path,
    cache_dir: Path,
    source_url: str,
    requested_numbers: list[int] | None = None,
) -> list[dict]:
    try:
        import fitz
    except Exception:
        return []

    page_map = science_supplement_page_map(pdf_path)
    numbers = sorted(set(requested_numbers or []) | set(page_map))
    if not numbers:
        numbers = discover_science_supplement_pdf_numbers(pdf_path)
    if not numbers:
        return []

    doc = fitz.open(pdf_path)
    figures = []
    for offset, number in enumerate(numbers):
        page_index = page_map.get(number)
        if page_index is None:
            continue
        next_page = min(
            [page for other, page in page_map.items() if other > number and page > page_index],
            default=page_index + 1,
        )
        end_page = min(max(page_index + 1, next_page), len(doc))
        image_path = cache_dir / f"science-figure-s{number}.png"
        if not image_path.exists():
            pixmaps = [
                doc[index].get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False)
                for index in range(page_index, end_page)
            ]
            if not pixmaps:
                continue
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

        page_text = "\n".join(doc[index].get_text("text") for index in range(page_index, end_page))
        caption = extract_science_supplement_caption(page_text, number)
        title = re.sub(rf"^Fig\.?\s*S\s*{number}\s*[:.]?\s*", "", caption, flags=re.I)
        title = title.split(". ")[0].strip()[:180] or f"Fig. S{number}"
        figures.append(
            {
                "id": f"supp-{number}",
                "label": f"Fig. S{number}",
                "type": "Supplementary figure",
                "title": title,
                "image": "./" + image_path.as_posix(),
                "sourceUrl": source_url,
                "caption": caption[:1400],
            }
        )
    doc.close()
    return figures


def science_supplementary_figures(
    cache_dir: Path,
    sections: list[dict],
) -> list[dict]:
    mentioned_numbers = sorted(
        {
            int(match.group(1))
            for section in sections
            for paragraph in section.get("paragraphs", [])
            for figure_id in paragraph.get("figures", [])
            for match in [re.match(r"supp-(\d+)$", figure_id)]
            if match
        }
    )
    pdfs = science_supplement_pdf_candidates(cache_dir)
    if pdfs:
        rendered = render_science_supplementary_pdf(
            pdfs[0],
            cache_dir,
            "./" + pdfs[0].as_posix(),
            mentioned_numbers,
        )
        if rendered:
            return rendered

    source_url = science_supplement_pdf_url(cache_dir)
    return [
        {
            "id": f"supp-{number}",
            "label": f"Fig. S{number}",
            "type": "Supplementary figure",
            "title": f"Supplementary figure {number}",
            "image": "",
            "sourceUrl": source_url,
            "caption": "Supplementary figure detected from the text. Recapture this article with the reloaded Chrome extension to cache and render the supplementary PDF.",
        }
        for number in mentioned_numbers
    ]


def parse_science_snapshot_article(url: str, cache_dir: Path) -> dict:
    page_path = cache_dir / "browser-page.html"
    body_path = cache_dir / "browser-body.txt"
    article_path = cache_dir / "article.html"
    html_path = page_path if page_path.exists() else article_path
    html = html_path.read_text(encoding="utf-8", errors="replace") if html_path.exists() else ""
    body_text = body_path.read_text(encoding="utf-8", errors="replace") if body_path.exists() else ""
    soup = BeautifulSoup(html, "html.parser") if html else BeautifulSoup("", "html.parser")
    article = parse_science_metadata(soup, url) if html else {
        "sourceUrl": canonical_science_url(url),
        "sourceMirrorUrl": "Browser-visible local text cache",
        "title": "Untitled Science article",
        "journal": "Science",
        "published": "",
        "doi": science_doi_from_url(url),
        "authors": "",
    }
    figures = parse_science_figures(soup, url, cache_dir)
    main_figure_count = sum(1 for figure in figures if figure["id"].startswith("fig-"))
    article["sections"] = parse_science_sections(soup, main_figure_count, body_text) if html else parse_science_browser_text_sections(body_text.splitlines(), main_figure_count)
    paragraph_start = max(
        (
            int(match.group(1))
            for section in article["sections"]
            for paragraph in section.get("paragraphs", [])
            for match in [re.match(r"p-(\d+)$", paragraph.get("id", ""))]
            if match
        ),
        default=0,
    )
    supplement_methods = extract_science_supplement_methods(cache_dir, main_figure_count, paragraph_start)
    if supplement_methods and not any(section.get("id") == supplement_methods["id"] for section in article["sections"]):
        article["sections"].append(supplement_methods)
    existing_ids = {figure["id"] for figure in figures}
    for figure in science_supplementary_figures(cache_dir, article["sections"]):
        if figure["id"] not in existing_ids:
            figures.append(figure)
            existing_ids.add(figure["id"])
    article["figures"] = figures
    article["references"] = parse_science_references(soup, body_text)
    article["cacheKey"] = cache_dir.name
    article["sourceFamily"] = "science-browser-cache" if page_path.exists() else "science-direct"
    return article


def parse_science_article(url: str, assets_dir: str | Path = "assets") -> dict:
    if not SCIENCE_URL_RE.match(url):
        raise ValueError("Science URLs should look like https://www.science.org/doi/<DOI>.")
    source_url = canonical_science_url(url)
    cache_key = science_cache_key(source_url)
    cache_dir = Path(assets_dir) / "imports" / cache_key
    cache_dir.mkdir(parents=True, exist_ok=True)
    if (cache_dir / "browser-page.html").exists() or (cache_dir / "browser-body.txt").exists():
        return parse_science_snapshot_article(source_url, cache_dir)
    html_path = cache_dir / "article.html"
    try:
        html = html_path.read_text(encoding="utf-8") if html_path.exists() else fetch_text(source_url)
    except Exception as error:
        raise ValueError(
            "Science.org blocked direct import for this article. Open it in the authenticated browser, "
            "capture it with the SciReader extension, then load the same URL here."
        ) from error
    if not html_path.exists():
        html_path.write_text(html, encoding="utf-8")
    return parse_science_snapshot_article(source_url, cache_dir)
