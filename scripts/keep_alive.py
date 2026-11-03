"""Streamlit Community Cloud 앱이 잠들지 않도록 실제 브라우저로 접속한다.

GitHub Actions(.github/workflows/keep-alive.yml)가 몇 시간마다 실행한다.
앱이 이미 잠들어 있으면 'Yes, get this app back up!' 버튼을 눌러 깨운다.
"""

from __future__ import annotations

import os
import re
import sys
import time

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

WAKE_BUTTON = re.compile(r"get this app back up", re.IGNORECASE)
READY_TEXT = "스터디룸 예약"  # 로그인 화면 제목
READY_TIMEOUT_SECONDS = 180


def app_is_ready(page) -> bool:
    for frame in page.frames:  # Community Cloud 는 앱을 iframe 안에 띄운다
        try:
            if frame.get_by_text(READY_TEXT).count():
                return True
        except Exception:
            continue
    return False


def main() -> int:
    url = os.environ.get("APP_URL", "").strip()
    if not url:
        print("APP_URL 이 비어 있습니다. 저장소 Settings → Secrets and variables → Actions → "
              "Variables 에 STREAMLIT_APP_URL 을 추가하세요.")
        return 1

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=90_000)

        try:
            button = page.get_by_role("button", name=WAKE_BUTTON)
            button.wait_for(timeout=15_000)
            button.click()
            print("앱이 잠들어 있어서 깨웠습니다.")
        except PlaywrightTimeout:
            print("앱이 깨어 있습니다.")

        deadline = time.monotonic() + READY_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if app_is_ready(page):
                print("앱 정상 동작 확인.")
                browser.close()
                return 0
            page.wait_for_timeout(5_000)

        page.screenshot(path="keep-alive-failure.png", full_page=True)
        browser.close()
    print(f"{READY_TIMEOUT_SECONDS}초 안에 앱 화면을 확인하지 못했습니다. 앱 상태를 확인하세요.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
