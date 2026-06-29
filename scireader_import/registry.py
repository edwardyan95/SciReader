from __future__ import annotations

from pathlib import Path

from .common import ARTICLE_URL_RE, BIORXIV_URL_RE, CELL_URL_RE, ELIFE_URL_RE, SCIENCE_URL_RE
from .nature import parse_nature_article
from .cell import parse_cell_article
from .biorxiv import parse_biorxiv_article
from .elife import parse_elife_article
from .science import parse_science_article


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
