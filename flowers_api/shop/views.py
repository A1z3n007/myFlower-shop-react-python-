import io
import json
from collections import defaultdict
from datetime import datetime, timedelta
import requests
import stripe
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.db import transaction

from django.db.models import Sum

from django.http import FileResponse, HttpResponse

from django.utils import timezone

from django.utils.dateparse import parse_datetime

from django.utils.html import escape

from django.utils.text import slugify

from django.views.decorators.csrf import csrf_exempt



from .models import (

    AnalyticsEvent,

    Coupon,

    Favorite,

    Order,

    OrderAuditLog,

    OrderEvent,

    OrderItem,

    Product,

    ProductReview,

    SavedAddress,

)

from .serializers import (

    AnalyticsEventSerializer,

    CouponSerializer,

    DeliveryRequestSerializer,

    FavoriteSerializer,

    OrderSerializer,

    ProductReviewSerializer,

    ProductSerializer,

    SavedAddressSerializer,

)

from .telegram import (

    notify_delivery_requested,

    notify_delivery_status_changed,

    notify_rating,

    notify_status_changed,

    rate_token,

)



stripe.api_key = getattr(settings, "STRIPE_SECRET_KEY", "")



_sign_confirm = TimestampSigner(salt="order-confirm")

_sign_cancel = TimestampSigner(salt="order-cancel")

_sign_rate = TimestampSigner(salt="order-rate")

_sign_repeat = TimestampSigner(salt="order-repeat")

_sign_call = TimestampSigner(salt="order-call")

_sign_address = TimestampSigner(salt="order-address")

_sign_photo = TimestampSigner(salt="order-photo")



DELIVERY_WINDOWS = [

    ("10:00", "12:00"),

    ("12:00", "14:00"),

    ("14:00", "16:00"),

    ("16:00", "18:00"),

    ("18:00", "20:00"),

]



def _page(title, body_html, ok=True):

    return HttpResponse(f"""

    <html><meta charset="utf-8"><body style="background:#0f0a12;color:#fff;font-family:system-ui;display:grid;place-items:center;height:100vh;margin:0">

      <div style="max-width:720px;padding:24px;text-align:center">

        <h2 style="margin:8px 0">{escape(title)}</h2>

        <div style="opacity:.95">{body_html}</div>

      </div>

    </body></html>

    """, status=200 if ok else 400)





def _build_slots():

    now = timezone.now()

    slots = []

    for offset in range(0, 2):

        day = (now + timedelta(days=offset)).date()

        label_day = "ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½" if offset == 0 else "ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½"

        for start, end in DELIVERY_WINDOWS:

            start_dt = timezone.make_aware(

                datetime.combine(day, datetime.strptime(start, "%H:%M").time())

            )

            if start_dt < now:

                continue

            slots.append(

                {

                    "day": str(day),

                    "label_day": label_day,

                    "window": f"{start}-{end}",

                    "value": f"{day.isoformat()}|{start}-{end}",

                }

            )

    return slots





def _generate_invoice_pdf(order: Order):

    buffer = io.BytesIO()

    pdf = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4

    pdf.setTitle(f"invoice-{order.id}")

    pdf.setFont("Helvetica-Bold", 16)

    pdf.drawString(40, height - 60, f"Invoice #{order.id}")

    pdf.setFont("Helvetica", 10)

    pdf.drawString(40, height - 80, f"Customer: {order.customer_name}")

    pdf.drawString(40, height - 95, f"Email: {order.email}")

    pdf.drawString(40, height - 110, f"Address: {order.delivery_address or order.address}")

    pdf.drawString(40, height - 130, f"Created: {order.created_at.strftime('%d.%m.%Y %H:%M')}")



    pdf.setFont("Helvetica-Bold", 12)

    pdf.drawString(40, height - 160, "Items:")

    y = height - 180

    pdf.setFont("Helvetica", 10)

    for item in order.items.select_related("product"):

        pdf.drawString(40, y, f"{item.product_name} x{item.qty}")

        pdf.drawRightString(width - 40, y, f"{item.price_at_purchase * item.qty} â¸")

        y -= 15

        if y < 60:

            pdf.showPage()

            y = height - 60

    y -= 10

    pdf.setFont("Helvetica-Bold", 12)

    pdf.drawRightString(width - 40, y, f"Subtotal: {order.subtotal} â¸")

    y -= 15

    pdf.drawRightString(width - 40, y, f"Discount: -{order.discount_amount} â¸")

    y -= 15

    pdf.drawRightString(width - 40, y, f"Delivery: {order.delivery_fee} â¸")

    y -= 15

    pdf.drawRightString(width - 40, y, f"Total: {order.total} â¸")



    pdf.showPage()

    pdf.save()

    buffer.seek(0)

    return buffer





def _record_event(order: Order, kind: str, payload=None, actor=None, source="api"):

    return OrderEvent.objects.create(

        order=order,

        kind=kind,

        payload=payload or {},

        created_by=actor if isinstance(actor, User) else None,

        created_by_email=getattr(actor, "email", "") if actor else "",

        source=source,

    )





def _audit(order: Order, field: str, old, new, actor=None, note=""):

    return OrderAuditLog.objects.create(

        order=order,

        field_name=field,

        old_value=str(old or ""),

        new_value=str(new or ""),

        actor=actor if isinstance(actor, User) else None,

        actor_email=getattr(actor, "email", "") if actor else "",

        actor_notes=note,

    )



class RegisterView(APIView):

    permission_classes = [AllowAny]

    throttle_scope = "forms"



    def post(self, request):

        email = (request.data.get("email") or "").strip().lower()

        name = (request.data.get("name") or "").strip()

        password = request.data.get("password") or ""

        if not email or not password:

            return Response({"detail":"email and password required"}, status=400)



        u, created = User.objects.get_or_create(username=email, defaults={"email": email})

        u.email = email

        if name:

            u.first_name = name

        u.is_active = True

        u.set_password(password)

        u.save()

        return Response({"ok": True})



class ProductViewSet(viewsets.ModelViewSet):

    queryset = Product.objects.all().order_by("-created_at")

    serializer_class = ProductSerializer

    permission_classes = [AllowAny]



    @action(detail=True, methods=["get"], permission_classes=[AllowAny])

    def similar(self, request, pk=None):

        product = self.get_object()

        qs = Product.objects.exclude(pk=product.pk)

        if product.category:

            qs = qs.filter(category=product.category)

        qs = qs.order_by("-rating_avg", "-created_at")[:8]

        data = ProductSerializer(qs, many=True).data

        return Response({"items": data})



    @action(detail=True, methods=["get"], permission_classes=[AllowAny])

    def bundles(self, request, pk=None):

        product = self.get_object()

        related = (

            OrderItem.objects.filter(order__items__product=product)

            .exclude(product=product)

            .values("product_id")

            .annotate(cnt=Sum("qty"))

            .order_by("-cnt")[:8]

        )

        ids = [row["product_id"] for row in related]

        items = list(Product.objects.filter(id__in=ids))

        items_sorted = sorted(items, key=lambda p: ids.index(p.id))

        return Response({"items": ProductSerializer(items_sorted, many=True).data})



    @action(detail=False, methods=["post"], permission_classes=[AllowAny])

    def compare(self, request):

        ids = request.data.get("ids") or []

        products = Product.objects.filter(id__in=ids)

        return Response({"items": ProductSerializer(products, many=True).data})





class ProductReviewViewSet(mixins.CreateModelMixin,

                           mixins.ListModelMixin,

                           viewsets.GenericViewSet):

    serializer_class = ProductReviewSerializer

    permission_classes = [AllowAny]

    throttle_scope = "forms"



    def get_queryset(self):

        qs = ProductReview.objects.select_related("product").order_by("-created_at")

        product_id = self.request.query_params.get("product")

        if product_id:

            qs = qs.filter(product_id=product_id)

        return qs



    def perform_create(self, serializer):

        product_id = self.request.data.get("product")

        if not product_id:

            raise ValidationError({"product": "product is required"})

        try:

            product = Product.objects.get(pk=product_id)

        except Product.DoesNotExist:

            raise ValidationError({"product": "product not found"})

        user = self.request.user if self.request.user.is_authenticated else None

        email = (self.request.data.get("email") or getattr(user, "email", "") or "").strip()

        serializer.save(product=product, user=user, email=email)





class CouponValidateView(APIView):

    permission_classes = [AllowAny]

    throttle_scope = "forms"



    def post(self, request):

        code = (request.data.get("code") or "").strip()

        subtotal = int(request.data.get("subtotal") or 0)

        if not code:

            return Response({"detail": "coupon required"}, status=400)

        try:

            coupon = Coupon.objects.get(code__iexact=code)

        except Coupon.DoesNotExist:

            return Response({"ok": False, "error": "not_found"}, status=404)

        if not coupon.is_valid():

            return Response({"ok": False, "error": "expired"}, status=400)

        discount = coupon.calculate_discount(subtotal)

        return Response(

            {

                "ok": True,

                "discount": discount,

                "snapshot": {"type": coupon.discount_type, "value": coupon.value},

            }

        )





@api_view(["GET"])

@permission_classes([AllowAny])

def delivery_slots_view(request):

    return Response({"slots": _build_slots()})





class AddressSuggestView(APIView):

    permission_classes = [AllowAny]

    throttle_scope = "forms"



    def get(self, request):

        query = (request.query_params.get("q") or "").strip()

        if not query:

            return Response({"suggestions": []})



        suggestions = []

        token = getattr(settings, "DADATA_API_KEY", "")

        secret = getattr(settings, "DADATA_SECRET", "")

        try:

            if token:

                resp = requests.post(

                    "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address",

                    headers={

                        "Authorization": f"Token {token}",

                        "X-Secret": secret,

                        "Content-Type": "application/json",

                    },

                    json={"query": query, "count": 5},

                    timeout=4,

                )

                data = resp.json()

                suggestions = [

                    {

                        "value": item["value"],

                        "lat": item.get("data", {}).get("geo_lat"),

                        "lon": item.get("data", {}).get("geo_lon"),

                    }

                    for item in data.get("suggestions", [])

                ]

            else:

                resp = requests.get(

                    "https://nominatim.openstreetmap.org/search",

                    params={"q": query, "format": "json", "limit": 5},

                    headers={"User-Agent": "flowershop-demo"},

                    timeout=4,

                )

                data = resp.json()

                suggestions = [

                    {

                        "value": item["display_name"],

                        "lat": item.get("lat"),

                        "lon": item.get("lon"),

                    }

                    for item in data

                ]

        except Exception:

            suggestions = []



        return Response({"suggestions": suggestions})





class SavedAddressView(APIView):

    permission_classes = [IsAuthenticated]

    throttle_scope = "forms"



    def get(self, request):

        qs = SavedAddress.objects.filter(user=request.user).order_by("-created_at")

        return Response({"items": SavedAddressSerializer(qs, many=True).data})



    def post(self, request):

        ser = SavedAddressSerializer(data=request.data)

        ser.is_valid(raise_exception=True)

        addr = SavedAddress.objects.create(user=request.user, **ser.validated_data)

        if addr.is_default:

            SavedAddress.objects.filter(user=request.user).exclude(pk=addr.pk).update(

                is_default=False

            )

        return Response(SavedAddressSerializer(addr).data, status=201)



    def delete(self, request):

        addr_id = request.data.get("id")

        SavedAddress.objects.filter(user=request.user, pk=addr_id).delete()

        return Response({"ok": True})





class OrderViewSet(

    mixins.CreateModelMixin,

    mixins.ListModelMixin,

    mixins.RetrieveModelMixin,

    viewsets.GenericViewSet,

):

    serializer_class = OrderSerializer

    permission_classes = [AllowAny]

    parser_classes = [JSONParser, FormParser, MultiPartParser]

    throttle_scope = "forms"



    def get_serializer_context(self):

        ctx = super().get_serializer_context()

        ctx["request"] = self.request

        return ctx



    def get_queryset(self):

        qs = (

            Order.objects.all()

            .select_related("coupon")

            .prefetch_related("items__product", "events")

            .order_by("-created_at")

        )

        mine = self.request.query_params.get("mine")

        email = self.request.query_params.get("email")

        if mine and self.request.user.is_authenticated:

            qs = qs.filter(user=self.request.user)

        elif email:

            qs = qs.filter(email=email)

        sort = self.request.query_params.get("sort")

        if sort == "rating":

            qs = qs.order_by("-rating", "-created_at")

        return qs



    @action(detail=True, methods=["post"])

    def request_delivery(self, request, pk=None):

        order = self.get_object()

        ser = DeliveryRequestSerializer(data=request.data)

        ser.is_valid(raise_exception=True)

        data = ser.validated_data



        address = data.get("delivery_address") or order.address

        dt = data.get("delivery_datetime")

        if not dt and data.get("delivery_day") and data.get("delivery_slot"):

            start = data["delivery_slot"].split("-")[0].strip()

            slot_time = datetime.strptime(start, "%H:%M").time()

            dt = timezone.make_aware(datetime.combine(data["delivery_day"], slot_time))



        order.delivery_requested = True

        order.delivery_status = Order.DeliveryStatus.SCHEDULED

        order.status = Order.Status.DELIVERING

        order.delivery_address = address

        order.delivery_datetime = dt

        order.delivery_day = data.get("delivery_day")

        order.delivery_slot = data.get("delivery_slot", "")

        order.delivery_comment = data.get("delivery_comment", "")

        order.save(update_fields=[

            "delivery_requested",

            "delivery_status",

            "status",

            "delivery_address",

            "delivery_datetime",

            "delivery_day",

            "delivery_slot",

            "delivery_comment",

        ])

        _record_event(

            order,

            "delivery_requested",

            {"address": order.delivery_address, "slot": order.delivery_slot},

            actor=request.user if request.user.is_authenticated else None,

        )

        _audit(order, "delivery_status", Order.DeliveryStatus.NONE, order.delivery_status, request.user)



        try:

            notify_delivery_requested(order)

        except Exception:

            pass



        return Response(OrderSerializer(order, context={"request": request}).data)



    @action(detail=True, methods=["post"])

    def set_status(self, request, pk=None):

        order = self.get_object()

        new = request.data.get("status")

        if new not in Order.Status.values:

            return Response({"detail": "invalid status"}, status=400)

        if not order.can_transition("status", new):

            return Response({"detail": "transition not allowed"}, status=400)

        old = order.status

        if new != old:

            order.status = new

            order.last_status_changed_at = timezone.now()

            order.save(update_fields=["status", "last_status_changed_at"])

            _record_event(order, "status_changed", {"from": old, "to": new})

            _audit(order, "status", old, new, request.user)

            try:

                notify_status_changed(order, old, new)

            except Exception:

                pass

        return Response(OrderSerializer(order, context={"request": request}).data)



    @action(detail=True, methods=["post"])

    def set_delivery_status(self, request, pk=None):

        order = self.get_object()

        new = request.data.get("delivery_status")

        if new not in Order.DeliveryStatus.values:

            return Response({"detail": "invalid delivery_status"}, status=400)

        if not order.can_transition("delivery_status", new):

            return Response({"detail": "transition not allowed"}, status=400)

        old = order.delivery_status

        if new != old:

            order.delivery_status = new

            order.last_delivery_status_changed_at = timezone.now()

            order.save(update_fields=["delivery_status", "last_delivery_status_changed_at"])

            _record_event(order, "delivery_status_changed", {"from": old, "to": new})

            _audit(order, "delivery_status", old, new, request.user)

            try:

                notify_delivery_status_changed(order, old, new)

            except Exception:

                pass

        return Response(OrderSerializer(order, context={"request": request}).data)



    @action(detail=True, methods=["get"])

    def invoice(self, request, pk=None):

        order = self.get_object()

        pdf_buffer = _generate_invoice_pdf(order)

        filename = f"invoice-{order.id}-{slugify(order.customer_name)}.pdf"

        return FileResponse(pdf_buffer, as_attachment=True, filename=filename)





class QuickOrderView(APIView):

    permission_classes = [AllowAny]

    throttle_scope = "forms"



    def post(self, request):

        product_id = request.data.get("product_id")

        name = (request.data.get("name") or "").strip()

        phone = (request.data.get("phone") or "").strip()

        if not product_id or not phone:

            return Response({"detail": "product_id and phone required"}, status=400)

        product = Product.objects.get(pk=product_id)

        email = request.data.get("email") or f"quick+{timezone.now().timestamp()}@flowers.local"



        with transaction.atomic():

            order = Order.objects.create(

                customer_name=name or "Quick order",

                customer_phone=phone,

                email=email,

                address="Quick order (call to confirm)",

                subtotal=product.price,

                total=product.price,

                quick_order=True,

                quick_order_payload={"name": name, "phone": phone, "product_id": product.id},

            )

            OrderItem.objects.create(

                order=order, product=product, qty=1, price_at_purchase=product.price

            )

            _record_event(order, "quick_order", {"product": product.name}, source="quick_form")



        try:

            notify_order_created(order)

        except Exception:

            pass



        return Response(OrderSerializer(order).data, status=201)





class AnalyticsEventView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "forms"

    def post(self, request):
        ser = AnalyticsEventSerializer(data=request.data)

        ser.is_valid(raise_exception=True)

        payload = ser.validated_data

        AnalyticsEvent.objects.create(

            name=payload["name"],

            session_id=payload.get("session_id", ""),

            payload=payload.get("payload", {}),

            email=request.data.get("email", ""),

            user=request.user if request.user.is_authenticated else None,

        )

        return Response({"ok": True})


class StripeIntentView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "forms"

    def post(self, request):
        if not settings.STRIPE_SECRET_KEY:
            return Response({"detail": "Stripe disabled"}, status=400)
        amount = int(request.data.get("amount") or 0)
        currency = (request.data.get("currency") or "kzt").lower()
        if amount <= 0:
            return Response({"detail": "amount must be greater than zero"}, status=400)
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                automatic_payment_methods={"enabled": True},
            )
        except Exception as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(
            {
                "id": intent.id,
                "client_secret": intent.client_secret,
                "test_mode": settings.STRIPE_TEST_MODE,
            }
        )


class StripeWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "forms"

    def post(self, request):
        payload = request.body
        secret = settings.STRIPE_WEBHOOK_SECRET
        try:
            if secret:
                sig_header = request.headers.get("Stripe-Signature", "")
                event = stripe.Webhook.construct_event(payload, sig_header, secret)
            else:
                event = json.loads(payload.decode("utf-8"))
        except ValueError:
            return Response({"detail": "invalid payload"}, status=400)
        except stripe.error.SignatureVerificationError:
            return Response({"detail": "invalid signature"}, status=400)

        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})

        if event_type == "payment_intent.succeeded":
            intent_id = data.get("id")
            if intent_id:
                Order.objects.filter(
                    stripe_payment_intent=intent_id
                ).update(payment_status=Order.PaymentStatus.PAID)

        return Response({"received": True})
def confirm_received_view(request, token: str):
    try:
        order_id = int(_sign_confirm.unsign(token, max_age=60 * 60 * 24 * 14))
        order = Order.objects.get(pk=order_id)
    except (BadSignature, SignatureExpired, ValueError, Order.DoesNotExist):
        return _page("Ссылка недействительна", "Откройте заказ из свежего письма.", ok=False)

    changed = False
    if order.status != Order.Status.COMPLETED:
        order.status = Order.Status.COMPLETED
        changed = True
    if order.delivery_status != Order.DeliveryStatus.DELIVERED:
        order.delivery_status = Order.DeliveryStatus.DELIVERED
        changed = True
    if changed:
        order.save(update_fields=["status", "delivery_status"])

    rate_t = rate_token(order.id)
    stars = "".join(
        [
            f"<label style='cursor:pointer;font-size:28px'><input type='radio' name='score' value='{i}' style='display:none'>{'⭐' * i}{'☆' * (5 - i)}</label>&nbsp;"
            for i in range(1, 6)
        ]
    )
    html = f"""
    <form method="post" action="/api/orders/rate/{rate_t}/" style="display:grid;gap:12px;max-width:520px;margin:0 auto">
      <div>Как вам заказ #{order.id}?</div>
      <div>{stars}</div>
      <textarea name="comment" rows="3" placeholder="Комментарий (по желанию)" style="border-radius:10px;padding:10px"></textarea>
      <button style="padding:10px 14px;border-radius:10px;background:#16a34a;color:#fff;border:none">Отправить отзыв</button>
    </form>"""
    return _page(f"Заказ #{order.id} доставлен 💐", html)


def cancel_order_view(request, token: str):
    try:
        order_id = int(_sign_cancel.unsign(token, max_age=60 * 60 * 24 * 14))
        order = Order.objects.get(pk=order_id)
    except (BadSignature, SignatureExpired, ValueError, Order.DoesNotExist):
        return _page("Ссылка недействительна", "Откройте заказ из личного кабинета.", ok=False)

    if request.GET.get("confirm") == "1":
        order.status = Order.Status.CANCELED
        if order.delivery_status != Order.DeliveryStatus.DELIVERED:
            order.delivery_status = Order.DeliveryStatus.FAILED
        order.save(update_fields=["status", "delivery_status"])
        return _page(f"Заказ #{order.id} отменён", "Ждём вас снова, чтобы подобрать идеальный букет ❤️.")

    confirm_link = request.build_absolute_uri("?confirm=1")
    body = (
        f"<p>Вы уверены, что хотите отменить заказ #{order.id}?</p>"
        f"<p><a href='{confirm_link}' style='padding:10px 14px;background:#7f1d1d;color:#fff;border-radius:10px;text-decoration:none'>Да, отменить</a></p>"
    )
    return _page("Подтвердите отмену", body)


@csrf_exempt
def rate_order_view(request, token: str):
    try:
        order_id = int(_sign_rate.unsign(token, max_age=60 * 60 * 24 * 30))
        order = Order.objects.get(pk=order_id)
    except (BadSignature, SignatureExpired, ValueError, Order.DoesNotExist):
        return _page("Ссылка недействительна", "Откройте заказ из письма, чтобы оставить отзыв.", ok=False)

    if request.method == "POST":
        score = int(request.POST.get("score", "5"))
        score = max(1, min(5, score))
        comment = (request.POST.get("comment") or "").strip()[:300]
        order.rating = score
        order.rating_comment = comment
        order.save(update_fields=["rating", "rating_comment"])
        try:
            notify_rating(order)
        except Exception:
            pass
        stars = "⭐" * score + "☆" * (5 - score)
        return _page(
            "Спасибо за отзыв!",
            f"<div style='font-size:32px'>{stars}</div><p>{escape(comment) or 'Ваше мнение сохранено.'}</p>",
        )

    return confirm_received_view(request, _sign_confirm.sign(str(order.id)))


class AccountProfileApiView(APIView):
    permission_classes = [AllowAny]

    def get_identity(self, request):
        if request.user.is_authenticated:
            return {"by": "user", "user": request.user}
        email = (request.GET.get("email") or "").strip().lower()
        if email:
            return {"by": "email", "email": email}
        return None

    def get(self, request):
        ident = self.get_identity(request)
        if not ident:
            return Response({"detail": "auth or ?email required"}, status=400)

        qs = Order.objects.all()
        if ident["by"] == "user":
            qs = qs.filter(user=ident["user"])
            email = ident["user"].email or ""
            name = ident["user"].first_name or ""
        else:
            qs = qs.filter(email=ident["email"])
            email = ident["email"]
            name = ""

        qs = qs.order_by("-created_at")
        order_count = qs.count()
        total_spent = qs.aggregate(s=Sum("total"))["s"] or 0
        last_order_at = qs.first().created_at if order_count else None

        cat_counts = defaultdict(int)
        for item in (
            OrderItem.objects.filter(order__in=qs).select_related("product")
        ):
            cat = item.product.category or "other"
            cat_counts[cat] += item.qty
        top_categories = [
            {"category": c, "qty": n}
            for c, n in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        return Response(
            {
                "name": name,
                "email": email,
                "orders_count": order_count,
                "total_spent": total_spent,
                "last_order_at": last_order_at,
                "top_categories": top_categories,
            }
        )


class FavoritesApiView(APIView):
    permission_classes = [AllowAny]

    def get_identity(self, request):
        if request.user.is_authenticated:
            return {"by": "user", "user": request.user}
        email = (
            request.GET.get("email") or request.data.get("email") or ""
        ).strip().lower()
        if email:
            return {"by": "email", "email": email}
        return None

    def get(self, request):
        ident = self.get_identity(request)
        if not ident:
            return Response({"detail": "auth or ?email required"}, status=400)

        fav_filters = {}
        qs_orders = Order.objects.all()
        if ident["by"] == "user":
            qs_orders = qs_orders.filter(user=ident["user"])
            fav_filters["user"] = ident["user"]
        else:
            qs_orders = qs_orders.filter(email=ident["email"])
            fav_filters["email"] = ident["email"]

        favorites_qs = (
            Favorite.objects.filter(**fav_filters)
            .select_related("product")
            .order_by("-created_at")
        )
        favorites_payload = FavoriteSerializer(favorites_qs, many=True).data

        window_days = 45
        since = timezone.now() - timedelta(days=window_days)
        qs_orders = qs_orders.filter(created_at__gte=since)

        items = list(
            OrderItem.objects.filter(order__in=qs_orders)
            .select_related("product", "order")
            .order_by("-order__created_at")
        )

        if not items:
            popular_ids = (
                OrderItem.objects.values("product_id")
                .annotate(cnt=Sum("qty"))
                .order_by("-cnt")
            )
            popular_ids = [row["product_id"] for row in popular_ids[:12]]
            popular = list(Product.objects.filter(id__in=popular_ids))
            popular_sorted = sorted(popular, key=lambda p: popular_ids.index(p.id))
            return Response(
                {
                    "buy_again": [],
                    "recommended": [self._ser_prod(p) for p in popular_sorted],
                    "categories_ranked": [],
                    "stats": {"window_days": window_days, "items_count": 0},
                    "favorites": favorites_payload,
                    "favorites_count": favorites_qs.count(),
                }
            )

        prod_score = defaultdict(float)
        prod_last = {}
        prod_qty = defaultdict(int)
        cat_score = defaultdict(float)

        def weight_by_days(days):
            if days <= 7:
                return 1.0
            if days <= 14:
                return 0.7
            if days <= 30:
                return 0.4
            return 0.2

        now = timezone.now()
        for item in items:
            product = item.product
            days = max(0, (now - item.order.created_at).days)
            weight = weight_by_days(days)
            prod_score[product.id] += item.qty * weight
            prod_last[product.id] = max(
                prod_last.get(product.id, item.order.created_at),
                item.order.created_at,
            )
            prod_qty[product.id] += item.qty
            cat = product.category or "other"
            cat_score[cat] += item.qty * weight

        bought_ids_sorted = sorted(
            prod_last.keys(),
            key=lambda pid: (prod_last[pid], prod_qty[pid]),
            reverse=True,
        )
        buy_again = [Product.objects.get(pk=pid) for pid in bought_ids_sorted[:8]]

        top_cats = [
            c for c, _ in sorted(cat_score.items(), key=lambda x: x[1], reverse=True)
        ]

        purchased_ids = set(prod_score.keys())
        rec_qs = (
            Product.objects.filter(category__in=top_cats)
            .exclude(id__in=purchased_ids)
            .order_by("-created_at")[:24]
        )
        recommended = list(rec_qs)

        if not recommended:
            popular_ids = (
                OrderItem.objects.values("product_id")
                .annotate(cnt=Sum("qty"))
                .order_by("-cnt")
            )
            popular_ids = [
                row["product_id"]
                for row in popular_ids
                if row["product_id"] not in purchased_ids
            ][:12]
            recommended = list(Product.objects.filter(id__in=popular_ids))

        return Response(
            {
                "buy_again": [self._ser_prod(p) for p in buy_again],
                "recommended": [self._ser_prod(p) for p in recommended[:12]],
                "categories_ranked": top_cats[:5],
                "stats": {"window_days": window_days, "items_count": len(items)},
                "favorites": favorites_payload,
                "favorites_count": favorites_qs.count(),
            }
        )

    def _ser_prod(self, product: Product):
        return {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "image_url": product.image_url,
            "category": product.category,
            "desc": product.desc,
        }

    def post(self, request):
        ident = self.get_identity(request)
        if not ident:
            return Response({"detail": "auth or email required"}, status=400)
        product_id = request.data.get("product_id")
        if not product_id:
            return Response({"detail": "product_id required"}, status=400)
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response({"detail": "product not found"}, status=404)

        filters = {"product": product}
        if ident["by"] == "user":
            filters["user"] = ident["user"]
        else:
            filters["email"] = ident["email"]

        action = (request.data.get("action") or "toggle").lower()
        existing = Favorite.objects.filter(**filters).first()
        favorited = False

        if action == "remove":
            if existing:
                existing.delete()
        elif action == "add":
            if not existing:
                Favorite.objects.create(**filters)
            favorited = True
        else:
            if existing:
                existing.delete()
            else:
                Favorite.objects.create(**filters)
                favorited = True

        if not favorited:
            favorited = Favorite.objects.filter(**filters).exists()
        return Response({"ok": True, "favorited": favorited})


def _clone_order_payload(order: Order):
    return {
        "customer_name": order.customer_name,
        "email": order.email,
        "customer_phone": order.customer_phone,
        "address": order.address,
        "delivery_address": order.delivery_address,
        "total": order.total,
        "subtotal": order.subtotal,
        "discount_amount": order.discount_amount,
        "delivery_fee": order.delivery_fee,
        "is_gift": order.is_gift,
        "gift_recipient_name": order.gift_recipient_name,
        "gift_recipient_phone": order.gift_recipient_phone,
        "gift_message": order.gift_message,
        "gift_card_signature": order.gift_card_signature,
        "user": order.user,
        "status": Order.Status.CREATED,
        "payment_method": order.payment_method,
        "payment_status": Order.PaymentStatus.PENDING,
    }


def repeat_order_view(request, token: str):
    try:
        order_id = int(_sign_repeat.unsign(token, max_age=60 * 60 * 24 * 30))
        source = Order.objects.get(pk=order_id)
    except (BadSignature, SignatureExpired, ValueError, Order.DoesNotExist):
        return _page("Ссылка недействительна", "Создайте повтор через личный кабинет.", ok=False)

    with transaction.atomic():
        new_order = Order.objects.create(**_clone_order_payload(source))
        for item in source.items.all():
            OrderItem.objects.create(
                order=new_order,
                product=item.product,
                qty=item.qty,
                price_at_purchase=item.price_at_purchase,
                product_name=item.product_name,
                product_category=item.product_category,
                product_image_url=item.product_image_url,
            )
        _record_event(new_order, "repeat_order", {"source": source.id}, source="telegram")

    return _page(
        f"Заказ #{new_order.id} создан",
        "Мы уже собираем ваш букет 💐",
        ok=True,
    )


def call_me_view(request, token: str):
    try:
        order_id = int(_sign_call.unsign(token, max_age=60 * 60 * 24 * 7))
        order = Order.objects.get(pk=order_id)
    except (BadSignature, SignatureExpired, ValueError, Order.DoesNotExist):
        return _page("Ссылка недействительна", "Запросите звонок из профиля.", ok=False)

    order.call_me_requested_at = timezone.now()
    order.save(update_fields=["call_me_requested_at"])
    _record_event(order, "call_me", {"source": "telegram"}, source="telegram")
    return _page("Мы перезвоним", "Оператор свяжется с вами в ближайшее время.")


@csrf_exempt
def change_address_view(request, token: str):
    try:
        order_id = int(_sign_address.unsign(token, max_age=60 * 60 * 24 * 7))
        order = Order.objects.get(pk=order_id)
    except (BadSignature, SignatureExpired, ValueError, Order.DoesNotExist):
        return _page("Ссылка недействительна", "Измените адрес через профиль.", ok=False)

    if request.method == "POST":
        new_address = (request.POST.get("address") or "").strip()
        comment = (request.POST.get("comment") or "").strip()
        if not new_address:
            return _page("Адрес обязателен", "Вернитесь назад и заполните форму.", ok=False)
        order.address_change_requested_at = timezone.now()
        order.address_change_payload = {"address": new_address, "comment": comment}
        order.save(update_fields=["address_change_requested_at", "address_change_payload"])
        _record_event(order, "address_change_requested", order.address_change_payload, source="telegram")
        return _page("Запрос получен", "Мы подтвердим новый адрес в ближайшее время.", ok=True)

    form_html = """
    <form method="post" style="display:grid;gap:12px;max-width:420px;margin:0 auto">
      <input name="address" placeholder="Новый адрес" style="padding:10px;border-radius:8px" required />
      <textarea name="comment" rows="3" placeholder="Комментарий" style="padding:10px;border-radius:8px"></textarea>
      <button style="padding:10px;border-radius:8px;background:#2563eb;color:#fff;border:none">Сохранить</button>
    </form>
    """
    return _page("Изменить адрес доставки", form_html, ok=True)


@csrf_exempt
def delivery_photo_view(request, token: str):
    try:
        order_id = int(_sign_photo.unsign(token, max_age=60 * 60 * 24))
        order = Order.objects.get(pk=order_id)
    except (BadSignature, SignatureExpired, ValueError, Order.DoesNotExist):
        return _page("Ссылка недействительна", "Загрузите фото через профиль.", ok=False)

    if request.method == "POST" and request.FILES.get("photo"):
        photo = request.FILES["photo"]
        filename = f"order_{order.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}_{photo.name}"
        order.delivery_photo.save(filename, photo, save=False)
        order.delivery_photo_uploaded_at = timezone.now()
        if order.delivery_status != Order.DeliveryStatus.DELIVERED:
            order.delivery_status = Order.DeliveryStatus.DELIVERED
        order.save(update_fields=["delivery_photo", "delivery_photo_uploaded_at", "delivery_status"])
        _record_event(order, "delivery_photo_uploaded", {"from": "courier"}, source="telegram")
        return _page("Фото получено", "Спасибо! Клиент увидит подтверждение.", ok=True)

    html = """
    <form method="post" enctype="multipart/form-data" style="display:grid;gap:12px;max-width:420px;margin:0 auto">
      <input type="file" name="photo" accept="image/*" required />
      <button style="padding:10px;border-radius:8px;background:#16a34a;color:#fff;border:none">Загрузить</button>
    </form>
    """
    return _page("Фото доставки", html, ok=True)
