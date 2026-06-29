from __future__ import annotations

from .common import *


def canonical_elife_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    match = re.search(r"/(articles|reviewed-preprints)/(\d+(?:v\d+)?)", parsed.path)
    if not match:
        return url
    return f"https://elifesciences.org/{match.group(1)}/{match.group(2)}"


def elife_cache_key(url: str) -> str:
    article_url = canonical_elife_url(url)
    article_id = article_url.rstrip("/").split("/")[-1]
    digest = hashlib.sha1(article_url.encode("utf-8")).hexdigest()[:10]
    return f"elife-{article_id}-{digest}"


def elife_meta_content(soup: BeautifulSoup, name: str) -> str:
    tag = soup.select_one(f'meta[name="{name}"]') or soup.select_one(f'meta[property="{name}"]')
    return clean_text(tag.get("content", "")) if tag else ""


def parse_elife_metadata(soup: BeautifulSoup, url: str) -> dict:
    authors = [
        clean_text(tag.get_text(" ", strip=True))
        for tag in soup.select(".author_list .author_link, .authors .author_link")
    ]
    doi = elife_meta_content(soup, "dc.identifier")
    doi = re.sub(r"^doi:\s*", "", doi, flags=re.I)
    return {
        "sourceUrl": canonical_elife_url(url),
        "sourceMirrorUrl": canonical_elife_url(url),
        "title": elife_meta_content(soup, "dc.title")
        or elife_meta_content(soup, "og:title")
        or clean_text((soup.select_one("h1") or soup.title).get_text(" ", strip=True)),
        "journal": "eLife",
        "published": elife_meta_content(soup, "dc.date") or elife_meta_content(soup, "citation_publication_date"),
        "doi": doi,
        "authors": ", ".join(dict.fromkeys(authors)),
    }


def elife_figure_id(raw_id: str, label: str = "") -> str | None:
    value = raw_id or slugify(label, "")
    match = re.match(r"figs(\d+)$", value, re.I)
    if match:
        return f"supp-{int(match.group(1))}"
    match = re.match(r"fig(\d+)s(\d+)$", value, re.I)
    if match:
        return f"supp-{int(match.group(1))}-{int(match.group(2))}"
    match = re.match(r"fig(\d+)$", value, re.I)
    if match:
        return f"fig-{int(match.group(1))}"
    match = re.match(r"table(\d+)$", value, re.I)
    if match:
        return f"table-{int(match.group(1))}"
    return None


def elife_figure_id_from_href(href: str | None) -> str | None:
    if not href:
        return None
    parsed = urllib.parse.urlparse(href)
    anchor = parsed.fragment or href.lstrip("#")
    return elife_figure_id(anchor)


def elife_figure_sort_key(figure: dict) -> tuple:
    ids = [int(number) for number in re.findall(r"\d+", figure.get("id", ""))]
    order = 0
    if figure.get("id", "").startswith("supp-"):
        order = 1
    elif figure.get("id", "").startswith("table-"):
        order = 2
    return (order, ids or [999])


def parse_elife_figures(article_soup: BeautifulSoup, figures_soup: BeautifulSoup, url: str) -> list[dict]:
    figures = []
    seen = set()
    for asset in figures_soup.select(".asset-viewer-inline[id], .asset-viewer-inline"):
        raw_id = asset.get("id") or ""
        label_node = asset.select_one(".asset-viewer-inline__header_text__prominent")
        label = clean_text(label_node.get_text(" ", strip=True)) if label_node else raw_id
        figure_id = elife_figure_id(raw_id, label)
        if not figure_id or figure_id in seen:
            continue
        if raw_id.lower().startswith("sa"):
            continue
        heading = asset.select_one(".caption-text__heading")
        title = clean_text(heading.get_text(" ", strip=True)) if heading else label
        caption_node = asset.select_one(".caption-text__body")
        caption = clean_text(caption_node.get_text(" ", strip=True)) if caption_node else title
        image = (
            asset.get("data-asset-viewer-uri")
            or (asset.select_one(".asset-viewer-inline__open_link[href]") or {}).get("href", "")
            or (asset.select_one("img[src]") or {}).get("src", "")
        )
        figure_type = "Table" if figure_id.startswith("table-") else "Supplementary figure" if figure_id.startswith("supp-") else "Main figure"
        figures.append(
            {
                "id": figure_id,
                "label": label,
                "type": figure_type,
                "title": title,
                "image": absolute_url(image, url),
                "sourceUrl": f"{canonical_elife_url(url)}/figures#{raw_id}" if raw_id else canonical_elife_url(url),
                "caption": caption,
            }
        )
        seen.add(figure_id)

    if figures:
        return sorted(figures, key=elife_figure_sort_key)

    for asset in article_soup.select(".asset-viewer-inline[id]"):
        raw_id = asset.get("id") or ""
        if not elife_figure_id(raw_id):
            continue
        fallback = parse_elife_figures(article_soup, article_soup, url)
        return fallback
    return []


def elife_text_figure_ids(text: str, main_figure_count: int) -> list[str]:
    ids: list[str] = []
    for match in re.finditer(r"\bFigure\s+(\d+)\s*[\u2013\u2014-]\s*figure\s+supplement\s+(\d+)", text, re.I):
        add_unique(ids, f"supp-{int(match.group(1))}-{int(match.group(2))}")
    scrubbed = re.sub(
        r"\bFigure\s+\d+\s*[\u2013\u2014-]\s*figure\s+supplement\s+\d+[a-z]?",
        "",
        text,
        flags=re.I,
    )
    for figure_id in text_figure_ids(scrubbed, main_figure_count):
        add_unique(ids, figure_id)
    for table_id in text_table_ids(text):
        add_unique(ids, table_id)
    return ids


def elife_paragraph_text(node) -> str:
    clone = BeautifulSoup(str(node), "html.parser")
    for math in clone.select("math"):
        value = clean_text(math.get_text(" ", strip=True))
        if value:
            math.replace_with(f" {value} ")
    return clean_text(clone.get_text(" ", strip=True))


def elife_paragraph_citations(node) -> list[dict[str, str]]:
    citations = []
    for link in node.select("a[href]"):
        href = link.get("href") or ""
        match = re.search(r"#(?:bib|c)(\d+)$", href, re.I)
        if not match:
            continue
        text = clean_text(link.get_text(" ", strip=True))
        if not text:
            continue
        citation = {"key": match.group(1), "text": text}
        if citation not in citations:
            citations.append(citation)
    return citations


def elife_paragraph_figures(node, text: str, main_figure_count: int) -> list[str]:
    ids: list[str] = []
    for link in node.select("a[href]"):
        figure_id = elife_figure_id_from_href(link.get("href"))
        if figure_id:
            add_unique(ids, figure_id)
    for figure_id in elife_text_figure_ids(text, main_figure_count):
        add_unique(ids, figure_id)
    return ids


ELIFE_NON_BODY_SECTION_TITLES = {
    "eLife Assessment",
    "Editor's evaluation",
    "Public Reviews",
    "Recommendations for the authors",
    "References",
    "Acknowledgements",
    "Funding",
    "Author contributions",
    "Competing interests",
    "Metrics",
    "Decision letter",
    "Author response",
}


def parse_elife_sections(soup: BeautifulSoup, main_figure_count: int) -> list[dict]:
    sections = []
    counter = [0]
    stop = False
    for section in soup.select("section.article-section"):
        if stop:
            break
        heading = section.select_one(":scope > .article-section__header .article-section__header_text")
        title = clean_text(heading.get_text(" ", strip=True)) if heading else ""
        if not title:
            continue
        if title == "References":
            stop = True
            continue
        if title in ELIFE_NON_BODY_SECTION_TITLES:
            continue
        body = section.find("div", class_="article-section__body", recursive=False)
        if not body:
            continue
        paragraphs = []
        for child in body.find_all(recursive=False):
            if child.name == "p" and "paragraph" in child.get("class", []):
                text = elife_paragraph_text(child)
                kind = None
            elif "math-block" in child.get("class", []):
                text = elife_paragraph_text(child)
                kind = "equation"
            else:
                continue
            if not text:
                continue
            counter[0] += 1
            paragraph = {
                "id": f"p-{counter[0]}",
                "text": text,
                "figures": elife_paragraph_figures(child, text, main_figure_count),
                "citations": elife_paragraph_citations(child),
            }
            if kind:
                paragraph["kind"] = kind
            paragraphs.append(paragraph)
        if not paragraphs:
            continue
        base = slugify(title, "section")
        section_id = base
        suffix = 2
        existing = {item["id"] for item in sections}
        while section_id in existing:
            section_id = f"{base}-{suffix}"
            suffix += 1
        sections.append({"id": section_id, "title": title, "paragraphs": paragraphs})
    return sections


def parse_elife_references(soup: BeautifulSoup) -> dict[str, str]:
    references = {}
    for index, item in enumerate(soup.select("ol.reference-list > li.reference-list__item"), start=1):
        ref = item.select_one(".reference") or item
        item_id = ref.get("id") or item.get("id") or ""
        match = re.search(r"bib(\d+)", item_id, re.I)
        key = match.group(1) if match else str(index)
        text = clean_text(ref.get_text(" ", strip=True))
        if text:
            references[key] = text
    return references


def parse_elife_reviewed_metadata(soup: BeautifulSoup, url: str) -> dict:
    authors = [
        clean_text(tag.get("content", ""))
        for tag in soup.select('meta[name="citation_author"]')
        if tag.get("content")
    ]
    published = elife_meta_content(soup, "citation_publication_date").replace("/", "-")
    return {
        "sourceUrl": canonical_elife_url(url),
        "sourceMirrorUrl": canonical_elife_url(url),
        "title": elife_meta_content(soup, "citation_title")
        or elife_meta_content(soup, "og:title")
        or clean_text((soup.select_one("h1.title") or soup.select_one("h1") or soup.title).get_text(" ", strip=True)),
        "journal": "eLife",
        "published": published,
        "doi": elife_meta_content(soup, "citation_doi"),
        "authors": ", ".join(dict.fromkeys(authors)),
    }


def parse_elife_reviewed_figures(soup: BeautifulSoup, url: str) -> list[dict]:
    figures = []
    seen = set()
    for figure in soup.select("figure.figure[id]"):
        raw_id = figure.get("id") or ""
        figure_id = elife_figure_id(raw_id)
        if not figure_id or figure_id in seen:
            continue
        label_node = figure.select_one(".figure__label")
        label = clean_text(label_node.get_text(" ", strip=True)) if label_node else raw_id
        label = label.rstrip(".")
        title_node = figure.select_one("figcaption .heading-4, figcaption h4")
        title = clean_text(title_node.get_text(" ", strip=True)) if title_node else label
        caption_node = figure.select_one("figcaption")
        caption = clean_text(caption_node.get_text(" ", strip=True)) if caption_node else title
        image = (
            (figure.select_one("picture source[srcset]") or {}).get("srcset", "")
            or (figure.select_one("img[src]") or {}).get("src", "")
        )
        if image and "," in image:
            image = image.split(",")[-1].strip().split(" ")[0]
        figures.append(
            {
                "id": figure_id,
                "label": label,
                "type": "Supplementary figure" if figure_id.startswith("supp-") else "Main figure",
                "title": title,
                "image": absolute_url(image, url),
                "sourceUrl": f"{canonical_elife_url(url)}#{raw_id}",
                "caption": caption,
            }
        )
        seen.add(figure_id)
    return sorted(figures, key=elife_figure_sort_key)


def parse_elife_reviewed_sections(soup: BeautifulSoup, main_figure_count: int) -> list[dict]:
    containers = []
    abstract = soup.select_one("section.abstract")
    article = soup.select_one("article.article-body")
    if abstract:
        containers.append(abstract)
    if article:
        containers.extend(article.find_all("section", recursive=False))

    sections = []
    counter = [0]
    current = None
    stop = False

    def flush_section() -> None:
        nonlocal current
        if current and current["paragraphs"]:
            sections.append(current)
        current = None

    for container in containers:
        if stop:
            break
        for child in container.find_all(recursive=False):
            if child.name in {"h1", "h2", "h3"} and (
                child.get("id")
                or any(class_name in {"heading-1", "heading-2", "heading-3"} for class_name in child.get("class", []))
            ):
                title = clean_text(child.get_text(" ", strip=True))
                if title.lower() == "references":
                    flush_section()
                    stop = True
                    break
                if title in ELIFE_NON_BODY_SECTION_TITLES or title == "Supporting information":
                    flush_section()
                    current = None
                    continue
                flush_section()
                section_id = slugify(title, "section")
                existing = {section["id"] for section in sections}
                base = section_id
                suffix = 2
                while section_id in existing:
                    section_id = f"{base}-{suffix}"
                    suffix += 1
                current = {"id": section_id, "title": title, "paragraphs": []}
                continue
            if not current or child.name != "p" or child.find_parent("figcaption"):
                continue
            text = elife_paragraph_text(child)
            if not text:
                continue
            counter[0] += 1
            current["paragraphs"].append(
                {
                    "id": f"p-{counter[0]}",
                    "text": text,
                    "figures": elife_paragraph_figures(child, text, main_figure_count),
                    "citations": elife_paragraph_citations(child),
                }
            )
    flush_section()
    return sections


def parse_elife_reviewed_references(soup: BeautifulSoup) -> dict[str, str]:
    references = {}
    for index, item in enumerate(soup.select("li.reference-list__item"), start=1):
        match = re.match(r"c(\d+)$", item.get("id", ""), re.I)
        key = match.group(1) if match else str(index)
        text = clean_text(item.get_text(" ", strip=True))
        if text:
            references[key] = text
    return references


def parse_elife_reviewed_preprint(url: str, soup: BeautifulSoup, cache_key: str) -> dict:
    figures = parse_elife_reviewed_figures(soup, url)
    main_figure_count = sum(1 for figure in figures if figure["id"].startswith("fig-"))
    article = parse_elife_reviewed_metadata(soup, url)
    article["sections"] = parse_elife_reviewed_sections(soup, main_figure_count)
    article["figures"] = figures
    article["references"] = parse_elife_reviewed_references(soup)
    article["cacheKey"] = cache_key
    article["sourceFamily"] = "elife-reviewed-preprint"
    return article


def parse_elife_article(url: str, assets_dir: str | Path = "assets") -> dict:
    if not ELIFE_URL_RE.match(url):
        raise ValueError("eLife URLs should look like https://elifesciences.org/articles/<article-id> or https://elifesciences.org/reviewed-preprints/<article-id>.")

    source_url = canonical_elife_url(url)
    cache_key = elife_cache_key(source_url)
    cache_dir = Path(assets_dir) / "imports" / cache_key
    cache_dir.mkdir(parents=True, exist_ok=True)

    html_path = cache_dir / "article.html"
    if html_path.exists():
        article_html = html_path.read_text(encoding="utf-8")
    else:
        article_html = fetch_text(source_url)
        html_path.write_text(article_html, encoding="utf-8")

    figures_path = cache_dir / "figures.html"
    figures_url = f"{source_url}/figures"
    if figures_path.exists():
        figures_html = figures_path.read_text(encoding="utf-8")
    else:
        figures_html = fetch_text(figures_url)
        figures_path.write_text(figures_html, encoding="utf-8")

    article_soup = BeautifulSoup(article_html, "html.parser")
    if source_url.startswith("https://elifesciences.org/reviewed-preprints/") or article_soup.select_one("article.article-body"):
        return parse_elife_reviewed_preprint(source_url, article_soup, cache_key)

    figures_soup = BeautifulSoup(figures_html, "html.parser")
    figures = parse_elife_figures(article_soup, figures_soup, source_url)
    main_figure_count = sum(1 for figure in figures if figure["id"].startswith("fig-"))
    article = parse_elife_metadata(article_soup, source_url)
    article["sections"] = parse_elife_sections(article_soup, main_figure_count)
    article["figures"] = figures
    article["references"] = parse_elife_references(article_soup)
    article["cacheKey"] = cache_key
    article["sourceFamily"] = "elife-direct"
    return article
