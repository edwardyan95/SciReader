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


def trim_whitespace(image_path: Path) -> None:
    from PIL import Image, ImageChops

    image = Image.open(image_path).convert("RGB")
    background = Image.new("RGB", image.size, (255, 255, 255))
    bbox = ImageChops.difference(image, background).getbbox()
    if bbox:
        image.crop(bbox).save(image_path)



def meta_content(soup: BeautifulSoup, name: str) -> str:
    tag = soup.select_one(f'meta[name="{name}"]')
    return clean_text(tag.get("content", "")) if tag else ""


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
