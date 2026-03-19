import logging
import os

import httpx

log = logging.getLogger(__name__)


async def send_email(to: str, subject: str, text: str) -> dict:
    if os.environ.get("DEV_DELIVERY") == "true":
        log.info("Demo mail: to=%s subject=%s text=%s", to, subject, text)
        return {"ok": True, "demo": True}

    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Email sender not configured. Set DEV_DELIVERY=true or configure RESEND_API_KEY."
        )

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "from": "no-reply@yourdomain.com",
                "to": to,
                "subject": subject,
                "text": text,
            },
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"Email send failed: {resp.text}")

    return {"ok": True}
