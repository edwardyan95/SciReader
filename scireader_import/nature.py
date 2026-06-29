from __future__ import annotations

from .common import *
def add_section(
    sections: list[dict],
    title: str,
    paragraphs: list,
    counter: list[int],
    main_figure_count: int,
) -> None:
    usable = []
    for p in paragraphs:
        text = paragraph_text(p)
        if not text or text.lower() == "source data":
            continue
        counter[0] += 1
        usable.append(
            {
                "id": f"p-{counter[0]}",
                "text": text,
                "figures": paragraph_figures(p, text, main_figure_count),
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


NON_BODY_SECTION_TITLES = {
    "Inline Recommendations",
    "Data availability",
    "Code availability",
    "References",
    "Acknowledgements",
    "Author information",
    "Ethics declarations",
    "Peer review",
    "Additional information",
    "Extended data figures and tables",
    "Supplementary information",
    "Rights and permissions",
    "About this article",
}


def add_split_section(
    sections: list[dict],
    title: str,
    content,
    counter: list[int],
    main_figure_count: int,
) -> None:
    current_title = title
    current_paragraphs = []
    for child in content.find_all(recursive=False):
        if child.name == "h3":
            add_section(sections, current_title, current_paragraphs, counter, main_figure_count)
            current_title = clean_text(child.get_text(" ", strip=True))
            current_paragraphs = []
        elif child.name == "p":
            current_paragraphs.append(child)
    add_section(sections, current_title, current_paragraphs, counter, main_figure_count)


def parse_sections(soup: BeautifulSoup, main_figure_count: int) -> list[dict]:
    sections: list[dict] = []
    counter = [0]

    for section in soup.select("section[data-title]"):
        section_title = clean_text(section.get("data-title") or "")
        if not section_title or section_title in NON_BODY_SECTION_TITLES:
            continue
        content = section.select_one(".c-article-section__content")
        if not content:
            continue
        if section_title in {"Results", "Methods"}:
            add_split_section(sections, section_title, content, counter, main_figure_count)
        else:
            add_section(
                sections,
                section_title,
                content.find_all("p", recursive=False),
                counter,
                main_figure_count,
            )

    return sections


NATURE_BROWSER_STOP_TITLES = NON_BODY_SECTION_TITLES | {
    "Access through your institution",
    "Buy or subscribe",
    "Access options",
    "Similar content being viewed by others",
    "Metrics",
}


def parse_nature_browser_text_sections(lines: list[str], main_figure_count: int) -> list[dict]:
    sections = []
    current = None
    counter = [0]
    started = False
    skipping_figure_caption = False

    def start_section(title: str) -> None:
        nonlocal current, started, skipping_figure_caption
        started = True
        skipping_figure_caption = False
        section_id = slugify(title, "section")
        existing = {section["id"] for section in sections}
        base = section_id
        suffix = 2
        while section_id in existing:
            section_id = f"{base}-{suffix}"
            suffix += 1
        current = {"id": section_id, "title": title, "paragraphs": []}
        sections.append(current)

    cleaned = [clean_text(line) for line in lines]
    for index, value in enumerate(cleaned):
        if not value:
            continue
        if not started:
            if value == "Abstract":
                start_section(value)
            continue
        if value in NATURE_BROWSER_STOP_TITLES:
            if value.startswith("Access") or value in {"Buy or subscribe", "Access options"}:
                break
            if value in NON_BODY_SECTION_TITLES or value == "Similar content being viewed by others":
                break
            continue
        if re.match(r"^(?:Fig\.?|Extended Data Fig\.?|Supplementary Fig\.?)\s*\d+", value, re.I):
            skipping_figure_caption = True
            continue
        if value == "The alternative text for this image may have been generated using AI.":
            continue
        if skipping_figure_caption:
            if len(value) < 120 and not value.endswith((".", ",", ";", ":")):
                skipping_figure_caption = False
            else:
                continue
        next_value = next((item for item in cleaned[index + 1 : index + 6] if item), "")
        is_heading = (
            len(value) < 120
            and next_value
            and len(next_value) > 80
            and not value.endswith((".", ",", ";", ":"))
            and not re.search(r"^(?:Published|Cite this article|Subjects|Download PDF|Article)$", value)
            and not re.fullmatch(r"[\W\d_]+", value)
        )
        if is_heading:
            start_section(value)
            continue
        if not current or len(value) < 45:
            continue
        counter[0] += 1
        current["paragraphs"].append(
            {
                "id": f"p-{counter[0]}",
                "text": value,
                "figures": text_figure_ids(value, main_figure_count),
                "citations": paragraph_citations(value),
            }
        )

    return [section for section in sections if section["paragraphs"]]


def parse_metadata(soup: BeautifulSoup, url: str) -> dict:
    ld_json = soup.select_one('script[type="application/ld+json"]')
    entity = {}
    if ld_json:
        try:
            data = json.loads(ld_json.string or "{}")
            entity = data.get("mainEntity") or data
        except json.JSONDecodeError:
            entity = {}

    authors = entity.get("author") or []
    author_names = []
    if isinstance(authors, list):
        author_names = [author.get("name", "") for author in authors if isinstance(author, dict)]

    return {
        "sourceUrl": url,
        "title": entity.get("headline") or clean_text(soup.title.get_text(" ", strip=True)),
        "journal": (entity.get("isPartOf") or {}).get("name", "Nature"),
        "published": (entity.get("datePublished") or "")[:10],
        "doi": (entity.get("sameAs") or "").replace("https://doi.org/", ""),
        "authors": ", ".join(author_names),
    }


def nature_local_figure_image(cache_dir: Path, figure_id: str, raw_number: int | None = None) -> str:
    number_match = re.search(r"(\d+)", figure_id)
    variants = [figure_id]
    if number_match:
        number = int(number_match.group(1))
        variants.extend([f"figure-{number}", f"fig{number}", f"Fig{number}"])
    if raw_number:
        variants.extend([f"figure-{raw_number}", f"fig{raw_number}", f"Fig{raw_number}"])
    for extension in ("jpg", "jpeg", "png", "webp"):
        for stem in dict.fromkeys(variants):
            path = cache_dir / f"{stem}.{extension}"
            if path.exists():
                return "./" + path.as_posix()
    return ""


def parse_main_figures(soup: BeautifulSoup, url: str, cache_dir: Path | None = None) -> list[dict]:
    figures = []
    for div in soup.select('div[data-test="figure"]'):
        match = re.search(r"figure-(\d+)", div.get("id") or "")
        if not match:
            continue
        number = int(match.group(1))
        img = div.select_one("img")
        caption = div.select_one("figcaption")
        title = clean_text(div.get("data-title") or "")
        figure_id = f"fig-{number}"
        local_image = nature_local_figure_image(cache_dir, figure_id, number) if cache_dir else ""
        figures.append(
            {
                "id": figure_id,
                "label": f"Fig. {number}",
                "type": "Main figure",
                "title": title,
                "image": local_image or absolute_url(img.get("src") if img else ""),
                "sourceUrl": absolute_url(f"/articles/{url.rstrip('/').split('/')[-1]}/figures/{number}"),
                "caption": clean_text(caption.get_text(" ", strip=True)) if caption else title,
            }
        )
    return sorted(figures, key=lambda figure: int(figure["id"].split("-")[1]))


def parse_extended_figures(soup: BeautifulSoup, url: str, main_figure_count: int, cache_dir: Path | None = None) -> list[dict]:
    figures = []
    article_slug = url.rstrip("/").split("/")[-1]
    for item in soup.select('div.c-article-supplementary__item[id^="Fig"]'):
        match = re.match(r"Fig(\d+)$", item.get("id", ""))
        if not match:
            continue
        number = int(match.group(1))
        if number <= main_figure_count:
            continue
        ext_number = number - main_figure_count
        link = item.select_one("a[data-supp-info-image]")
        title = clean_text(link.get_text(" ", strip=True)) if link else f"Extended Data Fig. {ext_number}"
        title = re.sub(r"^Extended Data Fig\.\s*\d+\s*", "", title).strip()
        description = item.select_one(".c-article-supplementary__description")
        figure_id = f"ext-{ext_number}"
        local_image = nature_local_figure_image(cache_dir, figure_id, number) if cache_dir else ""
        figures.append(
            {
                "id": figure_id,
                "label": f"Extended Data Fig. {ext_number}",
                "type": "Extended data",
                "title": title,
                "image": local_image or absolute_url(link.get("data-supp-info-image") if link else ""),
                "sourceUrl": absolute_url(f"/articles/{article_slug}/figures/{number}"),
                "caption": clean_text(description.get_text(" ", strip=True)) if description else title,
            }
        )
    return sorted(figures, key=lambda figure: int(figure["id"].split("-")[1]))



def render_supplementary_figures(
    soup: BeautifulSoup, cache_key: str, assets_dir: Path
) -> list[dict]:
    figures = []
    supp_items = soup.select('div.c-article-supplementary__item[id^="MOESM"]')
    for item in supp_items:
        description = clean_text(item.get_text(" ", strip=True))
        matches = sorted({int(number) for number in re.findall(r"Supplementary\s+Fig(?:ure)?\.?\s*(\d+)", description, re.I)})
        if not matches:
            continue
        link = item.select_one('a[href$=".pdf"]')
        if not link:
            continue
        source_url = absolute_url(link.get("href"))
        pdf_dir = assets_dir / "imports" / cache_key
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = pdf_dir / "supplementary.pdf"
        if not pdf_path.exists():
            cached_pdf = next(
                (
                    path
                    for path in sorted(pdf_dir.glob("*.pdf"))
                    if path.read_bytes()[:4] == b"%PDF"
                ),
                None,
            )
            if cached_pdf:
                pdf_path = cached_pdf
            else:
                pdf_path.write_bytes(fetch_bytes(source_url))

        try:
            import fitz
        except Exception:
            for number in matches:
                figures.append(
                    {
                        "id": f"supp-{number}",
                        "label": f"Supplementary Fig. {number}",
                        "type": "Supplementary figure",
                        "title": f"Supplementary Fig. {number}",
                        "image": "",
                        "sourceUrl": str(pdf_path).replace("\\", "/"),
                        "caption": "Supplementary figure PDF detected, but PDF rendering is unavailable.",
                    }
                )
            continue

        doc = fitz.open(pdf_path)
        for number in matches:
            page_index = None
            page_text = ""
            pattern = re.compile(rf"Supplementary\s+Fig(?:ure)?\.?\s*{number}\b", re.I)
            for index in range(len(doc)):
                text = doc[index].get_text()
                if pattern.search(text):
                    page_index = index
                    page_text = text
                    break
            if page_index is None:
                continue
            image_path = pdf_dir / f"supplementary-fig-{number}.png"
            if not image_path.exists():
                pix = doc[page_index].get_pixmap(matrix=fitz.Matrix(2.5, 2.5), alpha=False)
                pix.save(image_path)
                try:
                    trim_whitespace(image_path)
                except Exception:
                    pass
            rel_image = "./" + image_path.as_posix()
            title_match = re.search(
                rf"Supplementary\s+Fig(?:ure)?\.?\s*{number}\s*:?\s*([^\n.]+\.?)",
                page_text,
                re.I,
            )
            figures.append(
                {
                    "id": f"supp-{number}",
                    "label": f"Supplementary Fig. {number}",
                    "type": "Supplementary figure",
                    "title": clean_text(title_match.group(1)) if title_match else f"Supplementary Fig. {number}",
                    "image": rel_image,
                    "sourceUrl": "./" + pdf_path.as_posix(),
                    "caption": clean_text(page_text)[:700],
                }
            )
    return figures


def parse_references(soup: BeautifulSoup) -> dict[str, str]:
    references = {}
    for item in soup.select("li.c-article-references__item"):
        text_item = item.select_one(".c-article-references__text") or item
        item_id = text_item.get("id") or ""
        counter = item.get("data-counter") or ""
        match = re.search(r"CR(\d+)$", item_id) or re.search(r"(\d+)", counter)
        if not match:
            continue
        references[match.group(1)] = clean_text(text_item.get_text(" ", strip=True))
    return references


def parse_nature_article(url: str, assets_dir: str | Path = "assets") -> dict:
    if not ARTICLE_URL_RE.match(url):
        raise ValueError("Only https://www.nature.com/articles/... URLs are supported right now.")

    assets_path = Path(assets_dir)
    cache_key = article_cache_key(url)
    cache_dir = assets_path / "imports" / cache_key
    cache_dir.mkdir(parents=True, exist_ok=True)
    browser_path = cache_dir / "browser-page.html"
    html_path = browser_path if browser_path.exists() else cache_dir / "article.html"
    if html_path.exists():
        html = html_path.read_text(encoding="utf-8")
    else:
        html = fetch_text(url)
        html_path.write_text(html, encoding="utf-8")

    soup = BeautifulSoup(html, "html.parser")
    article = parse_metadata(soup, url)
    if browser_path.exists():
        article["sourceMirrorUrl"] = "Browser-visible local page cache"

    figures = parse_main_figures(soup, url, cache_dir)
    main_figure_count = len(figures)
    article["sections"] = parse_sections(soup, main_figure_count)
    body_path = cache_dir / "browser-body.txt"
    if body_path.exists() and sum(len(section["paragraphs"]) for section in article["sections"]) <= 1:
        browser_sections = parse_nature_browser_text_sections(
            body_path.read_text(encoding="utf-8", errors="replace").splitlines(),
            main_figure_count,
        )
        if sum(len(section["paragraphs"]) for section in browser_sections) > sum(len(section["paragraphs"]) for section in article["sections"]):
            article["sections"] = browser_sections

    figures.extend(parse_extended_figures(soup, url, main_figure_count, cache_dir))
    existing_ids = {figure["id"] for figure in figures}
    for figure in render_supplementary_figures(soup, cache_key, assets_path):
        if figure["id"] not in existing_ids:
            figures.append(figure)
            existing_ids.add(figure["id"])

    article["figures"] = sorted(
        figures,
        key=lambda figure: (
            0 if figure["id"].startswith("fig-") else 1 if figure["id"].startswith("ext-") else 2,
            int(re.search(r"(\d+)", figure["id"]).group(1)),
        ),
    )
    article["references"] = parse_references(soup)
    article["cacheKey"] = cache_key
    return article
