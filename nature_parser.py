from __future__ import annotations

import hashlib
import html
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup


ARTICLE_URL_RE = re.compile(r"^https://www\.nature\.com/articles/[^/?#]+")
CELL_URL_RE = re.compile(r"^https://www\.cell\.com/(?P<journal>[^/]+)/(?:fulltext|abstract)/(?P<pii>[^/?#]+)")
BIORXIV_URL_RE = re.compile(r"^https://www\.biorxiv\.org/content/")
ELIFE_URL_RE = re.compile(r"^https://elifesciences\.org/(?:articles|reviewed-preprints)/\d+(?:v\d+)?")
SCIENCE_URL_RE = re.compile(r"^https://www\.science\.org/doi/(?:full/)?(?P<doi>10\.\d{4,9}/[^?#]+)")
CELL_PMC_FALLBACKS = {
    "S0896-6273(26)00216-3": "https://pmc.ncbi.nlm.nih.gov/articles/PMC13124079/",
}
NCBI_TOOL = "SciReaderPrototype"
USER_AGENT = "SciReaderPrototype/0.1 (+local research reader)"


def clean_text(text: str) -> str:
    text = re.sub(r"[\ud800-\udfff]", "?", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:)])", r"\1", text)
    text = re.sub(r"([(])\s+", r"\1", text)
    return text


def slugify(value: str, fallback: str = "item") -> str:
    value = value.lower().replace("–", "-")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:80] or fallback


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=35) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read()
    if b"POW_CHALLENGE" not in body:
        return body

    page = body.decode("utf-8", errors="replace")
    challenge_match = re.search(r'POW_CHALLENGE\s*=\s*"([^"]+)"', page)
    difficulty_match = re.search(r'POW_DIFFICULTY\s*=\s*"(\d+)"', page)
    cookie_match = re.search(r'POW_COOKIE_NAME\s*=\s*"([^"]+)"', page)
    if not challenge_match:
        return body

    challenge = challenge_match.group(1)
    difficulty = int(difficulty_match.group(1)) if difficulty_match else 4
    cookie_name = cookie_match.group(1) if cookie_match else "cloudpmc-viewer-pow"
    target_prefix = "0" * difficulty
    nonce = 0
    while True:
        candidate = f"{challenge}{nonce}"
        digest = hashlib.sha256(candidate.encode("utf-8")).hexdigest()
        if digest.startswith(target_prefix):
            break
        nonce += 1

    cookie_value = urllib.parse.quote(f"{challenge},{nonce}", safe=":")
    retry = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Cookie": f"{cookie_name}={cookie_value}"},
    )
    with urllib.request.urlopen(retry, timeout=180) as response:
        return response.read()


def article_cache_key(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    slug = parsed.path.rstrip("/").split("/")[-1] or "nature-article"
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    return f"{slug}-{digest}"


def cell_cache_key(url: str, pii: str) -> str:
    digest = hashlib.sha1(canonical_cell_url(url, pii).encode("utf-8")).hexdigest()[:10]
    return f"cell-{slugify(pii)}-{digest}"


def canonical_cell_url(url: str, pii: str) -> str:
    match = CELL_URL_RE.match(url)
    if match:
        return f"https://www.cell.com/{match.group('journal')}/fulltext/{urllib.parse.quote(pii, safe='()-')}"
    parsed = urllib.parse.urlparse(url)
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def biorxiv_cache_key(url: str, doi: str, version: str) -> str:
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    suffix = f"v{version}" if version else "latest"
    return f"biorxiv-{slugify(doi)}-{suffix}-{digest}"


def canonical_science_url(url: str) -> str:
    match = SCIENCE_URL_RE.match(url)
    if not match:
        return url
    doi = urllib.parse.unquote(match.group("doi")).rstrip("/")
    return f"https://www.science.org/doi/{urllib.parse.quote(doi, safe='/.-_')}"


def science_cache_key(url: str) -> str:
    canonical = canonical_science_url(url)
    match = SCIENCE_URL_RE.match(canonical)
    doi = urllib.parse.unquote(match.group("doi")) if match else canonical
    digest = hashlib.sha1(canonical.encode("utf-8")).hexdigest()[:10]
    return f"science-{slugify(doi)}-{digest}"


def absolute_url(url: str, base: str = "https://www.nature.com") -> str:
    if not url:
        return ""
    if url.startswith("//"):
        return "https:" + url
    return urllib.parse.urljoin(base, url)


def paragraph_text(p) -> str:
    clone = BeautifulSoup(str(p), "html.parser")
    for sup in clone.select("sup"):
        nums = [a.get_text("", strip=True) for a in sup.select("a")]
        nums = [n for n in nums if n]
        sup.replace_with(f"[{','.join(nums)}]" if nums else "")
    return clean_text(clone.get_text(" ", strip=True))


def figure_id_from_href(href: str | None, main_figure_count: int) -> str | None:
    if not href:
        return None
    match = re.search(r"#Fig(\d+)$", href)
    if not match:
        return None
    number = int(match.group(1))
    if 1 <= number <= main_figure_count:
        return f"fig-{number}"
    if number > main_figure_count:
        return f"ext-{number - main_figure_count}"
    return None


def add_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def text_figure_ids(text: str, main_figure_count: int) -> list[str]:
    ids: list[str] = []
    for match in re.finditer(r"Extended\s+Data\s+(?:Fig\.?\s*)?(\d+)", text, re.I):
        add_unique(ids, f"ext-{int(match.group(1))}")
    for match in re.finditer(r"(?:Supplementary|Supp\.?)\s*Fig(?:ure)?\.?\s*(\d+)", text, re.I):
        add_unique(ids, f"supp-{int(match.group(1))}")
    for match in re.finditer(r"\b(?:Fig\.?|Figure)\s*S(\d+)", text, re.I):
        add_unique(ids, f"supp-{int(match.group(1))}")
    for group in re.finditer(
        r"\bFigures?\s+((?:S?\d+[a-z]?(?:\s*[â€“–-]\s*(?:S?\d+)?[a-z]?)?)(?:\s*(?:,|and)\s*S?\d+[a-z]?(?:\s*[â€“–-]\s*(?:S?\d+)?[a-z]?)?)*)",
        text,
        re.I,
    ):
        prefix = text[max(0, group.start() - 24) : group.start()].lower()
        is_supplement_group = bool(re.search(r"(supplementary|supp\.?)\s*$", prefix))
        for item in re.finditer(r"S?\d+", group.group(1), re.I):
            token = item.group(0)
            number = int(re.search(r"\d+", token).group(0))
            if is_supplement_group or token.lower().startswith("s"):
                add_unique(ids, f"supp-{number}")
            elif 1 <= number <= main_figure_count:
                add_unique(ids, f"fig-{number}")
    for group in re.finditer(
        r"\bFigs\.\s*((?:\d+[a-z]?(?:\s*[–-]\s*[a-z])?)(?:\s*(?:,|and)\s*\d+[a-z]?(?:\s*[–-]\s*[a-z])?)*)",
        text,
        re.I,
    ):
        for item in re.finditer(r"\d+", group.group(1)):
            number = int(item.group(0))
            if 1 <= number <= main_figure_count:
                add_unique(ids, f"fig-{number}")
    for match in re.finditer(r"Fig\.?\s*(\d+)", text, re.I):
        prefix = text[max(0, match.start() - 24) : match.start()].lower()
        if re.search(r"(extended\s+data|supplementary|supp\.?)\s*$", prefix):
            continue
        number = int(match.group(1))
        if 1 <= number <= main_figure_count:
            add_unique(ids, f"fig-{number}")
    for match in re.finditer(r"\bFigure\s*(\d+)", text, re.I):
        prefix = text[max(0, match.start() - 24) : match.start()].lower()
        if re.search(r"(extended\s+data|supplementary|supp\.?)\s*$", prefix):
            continue
        number = int(match.group(1))
        if 1 <= number <= main_figure_count:
            add_unique(ids, f"fig-{number}")
    return ids


def text_table_ids(text: str) -> list[str]:
    ids: list[str] = []
    for match in re.finditer(r"\bTables?\s+(\d+)", text, re.I):
        add_unique(ids, f"table-{int(match.group(1))}")
    return ids


def paragraph_figures(p, text: str, main_figure_count: int) -> list[str]:
    ids: list[str] = []
    for link in p.select('a[data-track-action="figure anchor"]'):
        figure_id = figure_id_from_href(link.get("href"), main_figure_count)
        if figure_id:
            add_unique(ids, figure_id)

    for figure_id in text_figure_ids(text, main_figure_count):
        add_unique(ids, figure_id)
    return ids


def paragraph_citations(text: str) -> list[str]:
    citations: list[str] = []
    for group in re.findall(r"\[([0-9,]+)\]", text):
        citations.extend(group.split(","))
    return citations


CELL_URLISH_TOKEN_RE = re.compile(r"(?:https?://|www\.|doi\.org|figshare\.|[A-Za-z0-9_.+-]+@[A-Za-z0-9_.+-]+)")


def recover_cell_browser_citations(value: str) -> str:
    """Recover Cell superscript citations that browser innerText glues to words."""

    def replace_token(match: re.Match) -> str:
        token = match.group(0)
        if CELL_URLISH_TOKEN_RE.search(token):
            return token
        citation_match = re.match(
            r"(?P<prefix>.+?)(?P<cites>\d{1,3}(?:,\d{1,3})*)(?P<trail>[\]),.;:]*)$",
            token,
        )
        if not citation_match:
            return token
        prefix = citation_match.group("prefix")
        cites = citation_match.group("cites")
        trail = citation_match.group("trail")
        if not re.search(r"[A-Za-z)]", prefix):
            return token
        if prefix.endswith(".") and not re.search(r"[A-Za-z)]\.$", prefix):
            return token
        if re.search(r"(?:^|[^A-Za-z])(?:S|Fig|Figs|Figure|Figures|Table|Tables)\.?$", prefix, re.I):
            return token
        if re.search(r"(?:https?://|www\.|/|\.[A-Za-z]{2,}\.?)", prefix, re.I):
            return token
        return f"{prefix}[{cites}]{trail}"

    return re.sub(r"\S+", replace_token, value)


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


def trim_whitespace(image_path: Path) -> None:
    from PIL import Image, ImageChops

    image = Image.open(image_path).convert("RGB")
    background = Image.new("RGB", image.size, (255, 255, 255))
    bbox = ImageChops.difference(image, background).getbbox()
    if bbox:
        image.crop(bbox).save(image_path)


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


def meta_content(soup: BeautifulSoup, name: str) -> str:
    tag = soup.select_one(f'meta[name="{name}"]')
    return clean_text(tag.get("content", "")) if tag else ""


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


def fetch_crossref_metadata(doi: str) -> dict:
    if not doi:
        return {}
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='')}"
    data = json.loads(fetch_text(url))
    return data.get("message", {})


def fetch_crossref_metadata_by_pii(compact_pii: str) -> dict:
    if not compact_pii:
        return {}
    query = urllib.parse.urlencode({"filter": f"alternative-id:{compact_pii}", "rows": "1"})
    data = json.loads(fetch_text(f"https://api.crossref.org/works?{query}"))
    items = data.get("message", {}).get("items", [])
    return items[0] if items else {}


def crossref_authors(message: dict) -> str:
    authors = []
    for author in message.get("author", []):
        given = author.get("given", "")
        family = author.get("family", "")
        name = clean_text(f"{given} {family}")
        if name:
            authors.append(name)
    return ", ".join(authors)


def crossref_date(message: dict) -> str:
    for key in ("published-print", "published-online", "published"):
        parts = message.get(key, {}).get("date-parts", [])
        if parts and parts[0]:
            return "-".join(str(part) for part in parts[0])
    return ""


def markdown_link_text(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)

    def link_replacement(match: re.Match) -> str:
        label = match.group(1)
        return f"[{label}]" if re.fullmatch(r"\d+(?:,\d+)*", label) else label

    previous = None
    while previous != text:
        previous = text
        text = re.sub(r"\[([^\]]+)\]\(((?:[^()]+|\([^()]*\))*)\)", link_replacement, text)
    text = text.replace("_", "").replace("**", "").replace("`", "")
    text = re.sub(r"<[^>]+>", "", text)
    return clean_text(html.unescape(text))


def is_biorxiv_formula_image(text: str) -> bool:
    return bool(
        re.search(
            r"!\[[^\]]*(?:Embedded\s+Image|formula|equation)?[^\]]*\]\([^)]*/embed/[^)]*\)",
            text,
            re.I,
        )
    )


def convert_biorxiv_formula_images(text: str, source_url: str) -> str:
    def formula_token(raw_url: str) -> str:
        return f"{{{{formula:{absolute_url(raw_url, source_url)}}}}}"

    def replace_linked_image(match: re.Match) -> str:
        target = match.group("target")
        thumb = match.group("thumb")
        alt = match.group("alt") or ""
        formula_url = target if "/embed/" in target else thumb
        if "/embed/" not in formula_url and not re.search(r"Embedded\s+Image|formula|equation", alt, re.I):
            return match.group(0)
        return formula_token(formula_url)

    def replace_image(match: re.Match) -> str:
        image_url = match.group("src")
        alt = match.group("alt") or ""
        if "/embed/" not in image_url and not re.search(r"Embedded\s+Image|formula|equation", alt, re.I):
            return match.group(0)
        return formula_token(image_url)

    text = re.sub(
        r"\[!\[(?P<alt>[^\]]*)\]\((?P<thumb>[^)]+)\)\]\((?P<target>[^)\s]+)(?:\s+\"[^\"]+\")?\)",
        replace_linked_image,
        text,
    )
    return re.sub(
        r"!\[(?P<alt>[^\]]*)\]\((?P<src>[^)\s]+)(?:\s+\"[^\"]+\")?\)",
        replace_image,
        text,
    )


def is_blocked_biorxiv_markdown(markdown: str) -> bool:
    lowered = markdown[:2000].lower()
    return (
        "performing security verification" in lowered
        or "just a moment..." in lowered
        or "target url returned error 403" in lowered
    )


def fetch_biorxiv_reader_markdown(source_url: str) -> tuple[str, str]:
    http_source_url = source_url.replace("https://", "http://", 1)
    reader_urls = [
        f"https://r.jina.ai/http://r.jina.ai/http://{source_url}",
        f"https://r.jina.ai/http://{http_source_url}",
        f"https://r.jina.ai/http://{source_url}",
    ]
    last_markdown = ""
    last_reader_url = reader_urls[0]
    for reader_url in reader_urls:
        markdown = fetch_text(reader_url)
        last_markdown = markdown
        last_reader_url = reader_url
        if not is_blocked_biorxiv_markdown(markdown):
            return markdown, reader_url
    return last_markdown, last_reader_url


def markdown_figure_ids(text: str) -> list[str]:
    ids: list[str] = []
    for href in re.findall(r"#(figs?\d+|fig\d+|F\d+|mmc\d+)", text, re.I):
        match = re.match(r"figs(\d+)", href, re.I)
        if match:
            add_unique(ids, f"supp-{int(match.group(1))}")
            continue
        match = re.match(r"fig(\d+)", href, re.I)
        if match:
            add_unique(ids, f"fig-{int(match.group(1))}")
            continue
        match = re.match(r"F(\d+)", href, re.I)
        if match:
            add_unique(ids, f"fig-{int(match.group(1))}")
    return ids


def biorxiv_markdown_media_ids(text: str, anchor_map: dict[str, str]) -> list[str]:
    ids: list[str] = []
    for href in re.findall(r"#(F\d+|T\d+)", text, re.I):
        mapped = anchor_map.get(href.upper())
        if mapped:
            add_unique(ids, mapped)
            continue
        match = re.match(r"F(\d+)", href, re.I)
        if match:
            add_unique(ids, f"fig-{int(match.group(1))}")
            continue
        match = re.match(r"T(\d+)", href, re.I)
        if match:
            add_unique(ids, f"table-{int(match.group(1))}")
    return ids


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
    equation_html_blocks, math_styles = extract_cell_mathjax(body_path.parent / "browser-page.html")
    figures, skip_lines = browser_text_figure_blocks(lines, compact_pii, url)
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


PARSER_REGISTRY = (
    ("Nature", ARTICLE_URL_RE, parse_nature_article),
    ("Cell Press", CELL_URL_RE, parse_cell_article),
    ("bioRxiv", BIORXIV_URL_RE, parse_biorxiv_article),
    ("eLife", ELIFE_URL_RE, parse_elife_article),
    ("Science", SCIENCE_URL_RE, parse_science_article),
)


def parse_article(url: str, assets_dir: str | Path = "assets") -> dict:
    for _name, pattern, parser in PARSER_REGISTRY:
        if pattern.match(url):
            return parser(url, assets_dir)
    supported = ", ".join(name for name, _pattern, _parser in PARSER_REGISTRY)
    raise ValueError(f"Supported URLs right now: {supported}.")


if __name__ == "__main__":
    import sys

    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.nature.com/articles/s41593-026-02258-4"
    print(json.dumps(parse_article(target_url), ensure_ascii=False, indent=2))
