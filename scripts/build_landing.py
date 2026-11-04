"""landing/index.html 에 앱 주소를 넣어 GitHub Pages 용 _site/ 를 만든다. (.github/workflows/pages.yml)"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

URL_PATTERN = re.compile(r"^https://[A-Za-z0-9.-]+(/[A-Za-z0-9._~/-]*)?$")


def build(app_url: str, src: Path, out_dir: Path) -> Path:
    app_url = app_url.strip().rstrip("/")
    if not URL_PATTERN.match(app_url):
        raise ValueError(f"STREAMLIT_APP_URL 이 올바른 https 주소가 아닙니다: {app_url!r}")
    html = src.read_text(encoding="utf-8")
    if "__APP_URL__" not in html:
        raise ValueError("landing/index.html 에 __APP_URL__ 자리표시자가 없습니다.")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "index.html"
    out.write_text(html.replace("__APP_URL__", app_url), encoding="utf-8")
    return out


def main() -> int:
    url = os.environ.get("APP_URL", "")
    if not url:
        print("::error::저장소 Variables 에 STREAMLIT_APP_URL 을 먼저 설정하세요.")
        return 1
    try:
        out = build(url, Path("landing/index.html"), Path("_site"))
    except ValueError as exc:
        print(f"::error::{exc}")
        return 1
    print(f"{out} 생성 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
