from __future__ import annotations

import json

from scireader_import import *


if __name__ == "__main__":
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.nature.com/articles/s41593-026-02258-4"
    print(json.dumps(parse_article(target_url), ensure_ascii=False, indent=2))
