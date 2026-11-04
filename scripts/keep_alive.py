"""Streamlit Community Cloud 앱이 잠들지 않도록 실제 브라우저로 접속한다.

GitHub Actions(.github/workflows/keep-alive.yml)가 몇 시간마다 실행한다.
앱이 이미 잠들어 있으면 'Yes, get this app back up!' 버튼을 눌러 깨운다.
로그인 화면은 공지를 DB에서 읽으므로, 이 접속은 Supabase 도 함께 사용한다.
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
READY_TIMEOUT_SECONDS = 150
# 'HeadlessChrome' 이 들어간 기본 UA 로는 Community Cloud 앱이 로딩 화면에서 멈출 수 있다.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def app_is_ready(page) -> bool:
    for frame in page.frames:  # Community Cloud 는 앱을 iframe 안에 띄운다
        try:
            if frame.get_by_text(READY_TEXT).count():
                return True
        except Exception:
            continue
    return False


def wait_until_ready(page, seconds: int) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if app_is_ready(page):
            return True
        page.wait_for_timeout(5_000)
    return False


def describe(page, label: str) -> None:
    """실패 원인을 Actions 로그에서 바로 볼 수 있도록 현재 화면 정보를 출력한다."""
    print(f"--- {label}")
    print(f"주소: {page.url}")
    try:
        print(f"제목: {page.title()}")
    except Exception:
        pass
    for frame in page.frames:
        try:
            text = " ".join(frame.locator("body").inner_text(timeout=3_000).split())
        except Exception:
            text = "(읽을 수 없음)"
        print(f"프레임 {frame.url[:120]} : {text[:300]}")


def main() -> int:
    url = os.environ.get("APP_URL", "").strip().rstrip("/")
    if not url:
        print("APP_URL 이 비어 있습니다. 저장소 Settings → Secrets and variables → Actions → "
              "Variables 에 STREAMLIT_APP_URL 을 추가하세요.")
        return 1

    with sync_playwright() as pw:
        # channel="chromium" 은 일반 Chrome 과 같은 새 headless 모드로 실행한다.
        browser = pw.chromium.launch(channel="chromium")
        context = browser.new_context(user_agent=USER_AGENT, viewport={"width": 1280, "height": 900}, locale="ko-KR")
        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=90_000)

        try:
            button = page.get_by_role("button", name=WAKE_BUTTON)
            button.wait_for(timeout=15_000)
            button.click()
            print("앱이 잠들어 있어서 깨웠습니다.")
        except PlaywrightTimeout:
            print("깨우기 버튼이 없습니다(잠들어 있지 않음).")

        if wait_until_ready(page, READY_TIMEOUT_SECONDS // 2):
            print("앱 정상 동작 확인.")
            browser.close()
            return 0
        describe(page, "바깥 페이지에서 앱 화면을 찾지 못함")

        # 앱 본체 주소로 직접 접속해 한 번 더 확인한다.
        direct = page.context.new_page()
        direct.goto(f"{url}/~/+/", wait_until="domcontentloaded", timeout=90_000)
        if wait_until_ready(direct, READY_TIMEOUT_SECONDS // 2):
            print("앱 본체 주소에서 정상 동작 확인.")
            browser.close()
            return 0
        describe(direct, "앱 본체 주소에서도 앱 화면을 찾지 못함")

        direct.screenshot(path="keep-alive-failure.png", full_page=True)
        browser.close()
    print(f"{READY_TIMEOUT_SECONDS}초 안에 앱 화면을 확인하지 못했습니다. 위 로그와 스크린샷으로 앱 상태를 확인하세요.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
