from django.db import transaction
from django.db.models import F
from rest_framework import serializers

from .models import (
    AnalyticsEvent,
    Coupon,
    Favorite,
    Order,
    OrderEvent,
    OrderItem,
    Product,
    ProductReview,
    SavedAddress,
)
from .tasks import notify_order_in_telegram, send_order_confirmation_email
from .telegram import notify_order_created


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "price",
            "image_url",
            "desc",
            "hero_color",
            "accent_color",
            "rating_avg",
            "rating_count",
            "created_at",
        ]


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = [
            "id",
            "code",
            "discount_type",
            "value",
            "max_discount_amount",
            "min_order_total",
            "valid_from",
            "valid_until",
            "usage_limit",
            "used_count",
            "notes",
        ]
        read_only_fields = ["used_count"]


class SavedAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedAddress
        fields = [
            "id",
            "label",
            "address",
            "entrance",
            "floor",
            "apartment",
            "intercom",
            "comment",
            "latitude",
            "longitude",
            "is_default",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class OrderItemWriteSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    qty = serializers.IntegerField(min_value=1)


class OrderItemReadSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "qty",
            "price_at_purchase",
            "product_name",
            "product_category",
            "product_image_url",
        ]


class OrderEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderEvent
        fields = ["id", "kind", "payload", "created_at", "created_by_email", "source"]


class ProductReviewSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = ProductReview
        fields = [
            "id",
            "product",
            "order_item",
            "rating",
            "title",
            "comment",
            "recommend",
            "created_at",
        ]
        read_only_fields = ["id", "product", "created_at"]


class FavoriteSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ["id", "product", "created_at"]
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemWriteSerializer(many=True, write_only=True)
    items_info = OrderItemReadSerializer(source="items", many=True, read_only=True)
    events = OrderEventSerializer(many=True, read_only=True)
    saved_address = SavedAddressSerializer(read_only=True)
    delivery_photo = serializers.ImageField(read_only=True)
    coupon_code = serializers.CharField(
        required=False, allow_blank=True, write_only=True
    )
    saved_address_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )
    use_saved_address = serializers.BooleanField(required=False, write_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer_name",
            "customer_phone",
            "email",
            "address",
            "delivery_address",
            "delivery_slot",
            "delivery_day",
            "delivery_datetime",
            "delivery_comment",
            "saved_address",
            "delivery_photo",
            "subtotal",
            "discount_amount",
            "delivery_fee",
            "total",
            "status",
            "delivery_requested",
            "delivery_status",
            "rating",
            "rating_comment",
            "items",
            "items_info",
            "coupon_code",
            "saved_address_id",
            "use_saved_address",
            "coupon_snapshot",
            "is_gift",
            "gift_recipient_name",
            "gift_recipient_phone",
            "gift_message",
            "gift_card_signature",
            "quick_order",
            "events",
            "created_at",
            "updated_at",
            "payment_method",
            "payment_status",
            "stripe_payment_intent",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "status",
            "delivery_requested",
            "delivery_status",
            "rating",
            "rating_comment",
            "subtotal",
            "discount_amount",
            "delivery_fee",
            "total",
            "coupon_snapshot",
            "events",
            "payment_status",
            "stripe_payment_intent",
            "saved_address",
            "delivery_photo",
        ]
        extra_kwargs = {
            "saved_address_id": {"write_only": True, "required": False},
            "use_saved_address": {"write_only": True, "required": False},
        }

    def validate(self, attrs):
        coupon_code = (attrs.get("coupon_code") or "").strip()
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code__iexact=coupon_code)
            except Coupon.DoesNotExist:
                raise serializers.ValidationError({"coupon_code": "Coupon не найден"})
            if not coupon.is_valid():
                raise serializers.ValidationError(
                    {"coupon_code": "Coupon больше не активен"}
                )
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        items_data = validated_data.pop("items")
        coupon_code = (validated_data.pop("coupon_code", "") or "").strip()
        saved_address_id = validated_data.pop("saved_address_id", None)
        use_saved_address = validated_data.pop("use_saved_address", False)

        delivery_address = validated_data.pop("delivery_address", None)

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user if (request and request.user.is_authenticated) else None,
                status=Order.Status.PROCESSING,
                delivery_address=delivery_address or validated_data.get("address"),
                **validated_data,
            )
            subtotal = 0
            for it in items_data:
                try:
                    product = Product.objects.get(pk=it["product_id"])
                except Product.DoesNotExist:
                    raise serializers.ValidationError(
                        {"items": f"product #{it['product_id']} not found"}
                    )
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    qty=it["qty"],
                    price_at_purchase=product.price,
                )
                subtotal += product.price * it["qty"]
            order.subtotal = subtotal

            if coupon_code:
                coupon = Coupon.objects.filter(code__iexact=coupon_code).first()
                if not coupon or not coupon.is_valid():
                    raise serializers.ValidationError(
                        {"coupon_code": "Coupon больше не активен"}
                    )
                discount = coupon.calculate_discount(subtotal)
                if discount:
                    order.coupon = coupon
                    order.coupon_code = coupon.code.upper()
                    order.discount_amount = discount
                    order.coupon_snapshot = {
                        "type": coupon.discount_type,
                        "value": coupon.value,
                    }
                    Coupon.objects.filter(pk=coupon.pk).update(
                        used_count=F("used_count") + 1
                    )

            order.total = max(
                order.subtotal - order.discount_amount + order.delivery_fee, 0
            )

            owner_filter = {}
            if order.user:
                owner_filter["user"] = order.user
            elif order.email:
                owner_filter["email"] = order.email

            if owner_filter:
                if use_saved_address:
                    addr, _ = SavedAddress.objects.get_or_create(
                        defaults={
                            "address": order.delivery_address or order.address,
                            "label": "Checkout",
                        },
                        **owner_filter,
                    )
                    order.saved_address = addr
                elif saved_address_id:
                    addr = (
                        SavedAddress.objects.filter(
                            pk=saved_address_id, **owner_filter
                        )
                        .order_by("-created_at")
                        .first()
                    )
                    if addr:
                        order.saved_address = addr
                        order.delivery_address = addr.address

            order.save()

            OrderEvent.objects.create(
                order=order,
                kind="created",
                payload={
                    "subtotal": order.subtotal,
                    "discount": order.discount_amount,
                    "gift": order.is_gift,
                },
                created_by=request.user
                if request and request.user.is_authenticated
                else None,
                created_by_email=getattr(request.user, "email", "") if request else "",
                source="api",
            )

        self._notify(order)
        return order

    def _notify(self, order: Order):
        try:
            send_order_confirmation_email.delay(order.id)
        except Exception:
            send_order_confirmation_email(order.id)
        try:
            notify_order_in_telegram.delay(order.id)
        except Exception:
            notify_order_in_telegram(order.id)


        try:
            notify_order_created(order)
        except Exception:
            pass


class DeliveryRequestSerializer(serializers.Serializer):
    delivery_address = serializers.CharField(
        max_length=300, required=False, allow_blank=True
    )
    delivery_datetime = serializers.DateTimeField(required=False, allow_null=True)
    delivery_day = serializers.DateField(required=False, allow_null=True)
    delivery_slot = serializers.CharField(
        max_length=80, required=False, allow_blank=True
    )
    delivery_comment = serializers.CharField(
        max_length=300, required=False, allow_blank=True
    )


class AnalyticsEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsEvent
        fields = ["id", "name", "session_id", "payload", "created_at"]
        read_only_fields = ["id", "created_at"]
        extra_kwargs = {
            "session_id": {"required": False, "allow_blank": True},
            "payload": {"required": False},
        }
