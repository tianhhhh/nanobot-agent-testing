"""Send a compact GitLab pipeline result to a Feishu custom bot webhook."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def _read_status(name: str) -> str:
    path = Path("ci-status") / f"{name}.txt"
    if not path.exists():
        return "unknown"
    return path.read_text(encoding="utf-8").strip() or "unknown"


def _display_status(status: str) -> str:
    return {
        "passed": "✅ 通过",
        "failed": "❌ 失败",
        "unknown": "⚠️ 未知",
    }.get(status, f"⚠️ {status}")


def _message() -> str:
    api_status = _read_status("api")
    ui_status = _read_status("ui")
    report_status = _read_status("report")
    overall = "✅ 流水线通过" if {api_status, ui_status, report_status} == {"passed"} else "❌ 流水线异常"
    project = os.getenv("CI_PROJECT_PATH", "nanobot-agent-testing")
    branch = os.getenv("CI_COMMIT_REF_NAME", "unknown")
    commit = os.getenv("CI_COMMIT_SHORT_SHA", "unknown")
    pipeline_url = os.getenv("CI_PIPELINE_URL", "")
    report_url = os.getenv("ALLURE_REPORT_URL", "")
    lines = [
        f"{overall}｜{project}",
        f"分支：{branch}",
        f"提交：{commit}",
        f"API：{_display_status(api_status)}",
        f"UI：{_display_status(ui_status)}",
        f"Allure：{_display_status(report_status)}",
    ]
    if pipeline_url:
        lines.append(f"流水线：{pipeline_url}")
    if report_url:
        lines.append(f"报告：{report_url}")
    return "\n".join(lines)


def main() -> int:
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL", "").strip()
    if not webhook_url:
        print("FEISHU_WEBHOOK_URL 未配置，跳过飞书通知。")
        return 0

    payload = json.dumps(
        {"msg_type": "text", "content": {"text": _message()}},
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            response_body = response.read().decode("utf-8", errors="replace")
            if response.status >= 300:
                print(f"飞书通知失败：HTTP {response.status}", file=sys.stderr)
                return 1
            result = json.loads(response_body)
            if result.get("code", result.get("StatusCode", 0)) != 0:
                print(f"飞书通知失败：{result}", file=sys.stderr)
                return 1
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        print(f"飞书通知失败：{exc}", file=sys.stderr)
        return 1

    print("飞书通知发送成功。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

