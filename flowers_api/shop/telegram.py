import html
import logging

import requests
from django.conf import settings
from django.core.signing import TimestampSigner

log = logging.getLogger(__name__)
API = "https://api.telegram.org/bot{token}/{method}"

_sign_confirm = TimestampSigner(salt="order-confirm")
_sign_cancel = TimestampSigner(salt="order-cancel")
_sign_rate = TimestampSigner(salt="order-rate")
_sign_repeat = TimestampSigner(salt="order-repeat")
_sign_call = TimestampSigner(salt="order-call")
_sign_address = TimestampSigner(salt="order-address")
_sign_photo = TimestampSigner(salt="order-photo")


def _enabled():
    return bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID)


def _chat_ids():
    raw = str(settings.TELEGRAM_CHAT_ID or "").strip()
    return [cid.strip() for cid in raw.split(",") if cid.strip()]


def _send(text: str, reply_markup: dict | None = None):
    if not _enabled():
        return False
    ok = True
    for cid in _chat_ids():
        try:
            payload = {
                "chat_id": cid,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup
            requests.post(
                API.format(token=settings.TELEGRAM_BOT_TOKEN, method="sendMessage"),
                json=payload,
                timeout=10,
            )
        except Exception as exc:
            ok = False
            log.exception("Telegram send failed: %s", exc)
    return ok


def _fmt_money(value: int) -> str:
    return f"{value:,}".replace(",", " ") + " ₸"


def _site():
    return getattr(settings, "SITE_URL", "http://127.0.0.1:8000")


def _item_lines(order):
    lines = []
    for item in order.items.select_related("product"):
        product = item.product
        lines.append(
            f"• <b>{html.escape(product.name)}</b> × {item.qty} — {_fmt_money(item.price_at_purchase * item.qty)}"
        )
    return "\n".join(lines)


def confirm_url(order):
    return f"{_site()}/api/orders/confirm/{_sign_confirm.sign(str(order.id))}/"


def cancel_url(order):
    return f"{_site()}/api/orders/cancel/{_sign_cancel.sign(str(order.id))}/"


def rate_url(order):
    return f"{_site()}/api/orders/rate/{_sign_rate.sign(str(order.id))}/"


def repeat_url(order):
    return f"{_site()}/api/orders/repeat/{_sign_repeat.sign(str(order.id))}/"


def call_url(order):
    return f"{_site()}/api/orders/call/{_sign_call.sign(str(order.id))}/"


def change_address_url(order):
    return f"{_site()}/api/orders/change-address/{_sign_address.sign(str(order.id))}/"


def photo_url(order):
    return f"{_site()}/api/orders/photo/{_sign_photo.sign(str(order.id))}/"


def kb_order_actions(order):
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Завершить", "url": confirm_url(order)},
                {"text": "🚫 Отменить", "url": cancel_url(order)},
            ],
            [
                {"text": "🔁 Повторить", "url": repeat_url(order)},
                {"text": "📞 Позвоните мне", "url": call_url(order)},
            ],
            [
                {"text": "🏠 Изменить адрес", "url": change_address_url(order)},
                {"text": "📷 Фото доставки", "url": photo_url(order)},
            ],
        ]
    }


def notify_order_created(order):
    text = (
        f"🌸 <b>Новый заказ #{order.id}</b>\n"
        f"Клиент: {html.escape(order.customer_name)}\n"
        f"Email: {html.escape(order.email)}\n"
        f"Адрес: {html.escape(order.address)}\n"
        f"Сумма: <b>{_fmt_money(order.total)}</b>\n\n{_item_lines(order)}"
    )
    _send(text, reply_markup=kb_order_actions(order))


def notify_delivery_requested(order):
    when = (
        order.delivery_datetime.strftime("%d.%m.%Y %H:%M")
        if order.delivery_datetime
        else order.delivery_slot or "уточнить"
    )
    addr = order.delivery_address or order.address
    text = (
        f"🚚 <b>Назначена доставка #{order.id}</b>\n"
        f"Адрес: {html.escape(addr)}\n"
        f"Когда: {when}\n"
        f"Комментарий: {html.escape(order.delivery_comment or 'не указан')}\n"
        f"Статус доставки: <b>{order.delivery_status}</b>"
    )
    _send(text, reply_markup=kb_order_actions(order))


def notify_status_changed(order, old, new):
    text = (
        f"🔔 <b>Статус заказа #{order.id} обновлён</b>\n"
        f"{html.escape(old)} → <b>{html.escape(new)}</b>\n"
        f"Сумма: {_fmt_money(order.total)}"
    )
    markup = kb_order_actions(order) if new in ("processing", "delivering") else None
    _send(text, reply_markup=markup)


def notify_delivery_status_changed(order, old, new):
    text = (
        f"📦 <b>Доставка заказа #{order.id}</b>\n"
        f"{html.escape(old)} → <b>{html.escape(new)}</b>"
    )
    markup = kb_order_actions(order) if new in ("scheduled", "out_for_delivery") else None
    _send(text, reply_markup=markup)


def notify_rating(order):
    stars = "⭐" * int(order.rating or 0) + "☆" * (5 - int(order.rating or 0))
    text = (
        f"📝 <b>Оценка заказа #{order.id}</b>\n"
        f"Оценка: {stars}\n"
        f"Комментарий: {html.escape(order.rating_comment or 'без комментария')}"
    )
    _send(text)


def rate_token(order_id: int):
    return _sign_rate.sign(str(order_id))
