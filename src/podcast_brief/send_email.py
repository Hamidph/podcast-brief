#!/usr/bin/env python3
"""
Send the daily briefing email via Resend.

Usage:
  echo '{"subject":"...","html":"...","to":"...","from":"..."}' | python -m podcast_brief.send_email

Requires RESEND_API_KEY environment variable.
Output (stdout): JSON with delivery status.
"""

import json
import os
import sys

import resend


def send_briefing_email(subject: str, html: str, to: str, from_addr: str) -> dict:
    resend.api_key = os.environ["RESEND_API_KEY"]

    try:
        result = resend.Emails.send({
            "from": from_addr,
            "to": [to],
            "subject": subject,
            "html": html,
        })
        return {"status": "ok", "id": result.get("id")}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def main():
    payload = json.load(sys.stdin)
    result = send_briefing_email(
        subject=payload["subject"],
        html=payload["html"],
        to=payload["to"],
        from_addr=payload["from"],
    )
    print(json.dumps(result))
    if result["status"] == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
