import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("build_landing", ROOT / "scripts" / "build_landing.py")
build_landing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_landing)

SRC = ROOT / "landing" / "index.html"


def test_build_inserts_app_url(tmp_path):
    out = build_landing.build("https://studyroom.streamlit.app/", SRC, tmp_path)
    html = out.read_text(encoding="utf-8")
    assert '"https://studyroom.streamlit.app"' in html
    assert "__APP_URL__" not in html


@pytest.mark.parametrize("bad", ["", "http://x.streamlit.app", "https://x.app/\";alert(1)//", "javascript:alert(1)"])
def test_build_rejects_unsafe_urls(tmp_path, bad):
    with pytest.raises(ValueError):
        build_landing.build(bad, SRC, tmp_path)
