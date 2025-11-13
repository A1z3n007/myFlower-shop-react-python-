from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Order
from .telegram import notify_order_created


def _load_order(order_id):
    return (
        Order.objects.select_related("user")
        .prefetch_related("items__product")
        .get(pk=order_id)
    )


@shared_task
def send_order_confirmation_email(order_id):
    order = _load_order(order_id)
    subj = f"Ваш заказ #{order.id} принят ❤️"
    body = (
        f"Привет, {order.customer_name}!\n\n"
        f"Мы получили заказ #{order.id} на сумму {order.total} ₸.\n"
        f"Команда Flower Shop уже собирает букет и пришлёт обновления статуса.\n\n"
        f"Спасибо, что выбираете нас!"
    )
    send_mail(
        subj,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [order.email],
        fail_silently=True,
    )


@shared_task
def notify_order_in_telegram(order_id):
    order = _load_order(order_id)
    try:
        notify_order_created(order)
    except Exception:
        return False
    return True


@shared_task
def auto_close_delivered_orders(hours=24):
    from .models import Order

    cutoff = timezone.now() - timezone.timedelta(hours=hours)
    qs = Order.objects.filter(
        status=Order.Status.DELIVERING,
        delivery_status=Order.DeliveryStatus.DELIVERED,
        updated_at__lte=cutoff,
    )
    for order in qs:
        order.status = Order.Status.COMPLETED
        order.save(update_fields=["status"])
