"""keep-alive 결과를 Gmail(SMTP)로 알린다. .github/workflows/keep-alive.yml 에서 실행.

필요한 값
- MAIL_USERNAME: 보내는 Gmail 주소 (Actions secret)
- MAIL_APP_PASSWORD: 그 계정의 Google '앱 비밀번호' 16자리 (Actions secret)
- ALERT_EMAILS: 받는 주소들, 쉼표로 구분 (Actions variable). 비어 있으면 보내는 주소로만 보낸다.
- EVENT: 'down' 또는 'recovered', RUN_URL / APP_URL: 메일 본문에 넣을 링크
"""

from __future__ import annotations

import os
import smtplib
import ssl
import sys
from email.message import EmailMessage
from pathlib import Path

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
LOG_FILE = Path("keep-alive.log")
LOG_TAIL_LINES = 40


def recipients(raw: str, fallback: str) -> list[str]:
    found = [part.strip() for part in raw.replace(";", ",").split(",") if part.strip()]
    return found or [fallback]


def build_message(event: str, sender: str, to: list[str], app_url: str, run_url: str, log: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = ", ".join(to)
    if event == "down":
        msg["Subject"] = "[스터디룸] 🚨 앱 장애 감지"
        lines = [
            "keep-alive 자동 접속에서 스터디룸 앱 화면을 확인하지 못했습니다.",
            "",
            f"앱 주소: {app_url}",
            f"실행 기록(로그·스크린샷): {run_url}",
            "",
            "확인 순서",
            "1. 앱 주소로 직접 접속해 보기",
            "2. Streamlit → Manage app → 로그 확인",
            "3. Supabase 대시보드에서 프로젝트가 일시정지(Paused)됐는지 확인",
            "",
            "장애가 이어지는 동안에는 메일을 다시 보내지 않고, 복구되면 한 번 더 알려 드립니다.",
        ]
        if log:
            lines += ["", "---- 마지막 로그 ----", log]
    else:
        msg["Subject"] = "[스터디룸] ✅ 앱 정상 복구"
        lines = [
            "스터디룸 앱이 다시 정상으로 확인되었습니다.",
            "",
            f"앱 주소: {app_url}",
            f"실행 기록: {run_url}",
        ]
    msg.set_content("\n".join(lines))
    return msg


def main() -> int:
    sender = os.environ["MAIL_USERNAME"].strip()
    password = os.environ["MAIL_APP_PASSWORD"].replace(" ", "")
    event = os.environ.get("EVENT", "down")
    to = recipients(os.environ.get("ALERT_EMAILS", ""), sender)
    log = ""
    if LOG_FILE.exists():
        log = "\n".join(LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()[-LOG_TAIL_LINES:])

    msg = build_message(event, sender, to, os.environ.get("APP_URL", ""), os.environ.get("RUN_URL", ""), log)
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ssl.create_default_context()) as smtp:
        smtp.login(sender, password)
        smtp.send_message(msg)
    print(f"알림 메일({event})을 {len(to)}명에게 보냈습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
