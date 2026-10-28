import httpx

from app.core.config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)


def telegram_is_configured() -> bool:
    return bool(
        TELEGRAM_BOT_TOKEN
        and TELEGRAM_CHAT_ID
    )


def send_telegram_message(
    message: str,
) -> dict:
    """
    Envía una notificación a Telegram.

    IMPORTANTE:
    - Telegram es opcional.
    - Si no está configurado, CyberShield continúa.
    - Si Telegram falla, CyberShield continúa.
    - Nunca lanza una excepción hacia FastAPI.
    """

    if not telegram_is_configured():
        return {
            "success": False,
            "sent": False,
            "reason": "telegram_not_configured",
        }

    url = (
        "https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
    }

    try:
        with httpx.Client(
            timeout=5.0
        ) as client:
            response = client.post(
                url,
                json=payload,
            )

        response.raise_for_status()

        return {
            "success": True,
            "sent": True,
            "status_code": response.status_code,
        }

    except Exception as exc:
        # Telegram jamás debe detener CyberShield.
        return {
            "success": False,
            "sent": False,
            "reason": str(exc),
        }