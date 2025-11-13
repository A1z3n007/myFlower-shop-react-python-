from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        now = timezone.now()
        if not self.pk and not self.created_at:
            self.created_at = now
        self.updated_at = now
        return super().save(*args, **kwargs)


class Product(TimeStampedModel):
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=80, blank=True)
    price = models.IntegerField()
    image_url = models.URLField(blank=True)
    desc = models.TextField(blank=True)
    hero_color = models.CharField(max_length=20, blank=True)
    accent_color = models.CharField(max_length=20, blank=True)
    rating_avg = models.FloatField(default=0)
    rating_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.name

    def as_card(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "image_url": self.image_url,
            "desc": self.desc,
            "rating_avg": self.rating_avg,
            "rating_count": self.rating_count,
        }


class Coupon(TimeStampedModel):
    class DiscountType(models.TextChoices):
        PERCENT = "percent", "Percent"
        FIXED = "fixed", "Fixed"

    code = models.CharField(max_length=32, unique=True)
    discount_type = models.CharField(
        max_length=10, choices=DiscountType.choices, default=DiscountType.PERCENT
    )
    value = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Percent (1-100) or fixed amount in ₸",
    )
    max_discount_amount = models.PositiveIntegerField(default=0, help_text="0 = no cap")
    min_order_total = models.PositiveIntegerField(default=0)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return self.code.upper()

    def is_valid(self, now=None):
        now = now or timezone.now()
        if not self.is_active:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False
        return True

    def calculate_discount(self, subtotal):
        if not self.is_valid():
            return 0
        if subtotal < self.min_order_total:
            return 0
        if self.discount_type == self.DiscountType.PERCENT:
            discount = int(subtotal * (self.value / 100))
        else:
            discount = self.value
        if self.max_discount_amount:
            discount = min(discount, self.max_discount_amount)
        return min(discount, subtotal)


class SavedAddress(TimeStampedModel):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    email = models.EmailField(blank=True, null=True)
    label = models.CharField(max_length=80, blank=True)
    address = models.CharField(max_length=300)
    entrance = models.CharField(max_length=30, blank=True)
    floor = models.CharField(max_length=10, blank=True)
    apartment = models.CharField(max_length=30, blank=True)
    intercom = models.CharField(max_length=30, blank=True)
    comment = models.CharField(max_length=300, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    meta = models.JSONField(default=dict, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        return self.label or self.address


class Favorite(TimeStampedModel):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    email = models.EmailField(blank=True, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="hearts")

    class Meta:
        unique_together = [
            ("user", "product"),
            ("email", "product"),
        ]

    def __str__(self):
        owner = self.user.email if self.user else (self.email or "guest")
        return f"{owner or 'guest'} ❤️ {self.product_id}"


class Order(TimeStampedModel):
    class Status(models.TextChoices):
        CREATED = "created", "created"
        PROCESSING = "processing", "processing"
        DELIVERING = "delivering", "delivering"
        COMPLETED = "completed", "completed"
        CANCELED = "canceled", "canceled"

    class DeliveryStatus(models.TextChoices):
        NONE = "none", "none"
        PENDING = "pending", "pending"
        SCHEDULED = "scheduled", "scheduled"
        OUT_FOR_DELIVERY = "out_for_delivery", "out_for_delivery"
        DELIVERED = "delivered", "delivered"
        FAILED = "failed", "failed"

    class PaymentMethod(models.TextChoices):
        DEMO = "demo", "Учебная"
        STRIPE_TEST = "stripe_test", "Stripe test"

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Ожидает"
        REQUIRES_ACTION = "requires_action", "Нужно действие"
        PAID = "paid", "Оплачен"
        FAILED = "failed", "Ошибка"

    STATUS_TRANSITIONS = {
        Status.CREATED: {Status.PROCESSING, Status.CANCELED},
        Status.PROCESSING: {Status.DELIVERING, Status.CANCELED},
        Status.DELIVERING: {Status.COMPLETED, Status.CANCELED},
        Status.COMPLETED: set(),
        Status.CANCELED: set(),
    }
    DELIVERY_TRANSITIONS = {
        DeliveryStatus.NONE: {DeliveryStatus.PENDING, DeliveryStatus.SCHEDULED},
        DeliveryStatus.PENDING: {DeliveryStatus.SCHEDULED, DeliveryStatus.OUT_FOR_DELIVERY},
        DeliveryStatus.SCHEDULED: {
            DeliveryStatus.OUT_FOR_DELIVERY,
            DeliveryStatus.FAILED,
        },
        DeliveryStatus.OUT_FOR_DELIVERY: {
            DeliveryStatus.DELIVERED,
            DeliveryStatus.FAILED,
        },
        DeliveryStatus.DELIVERED: set(),
        DeliveryStatus.FAILED: set(),
    }

    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    customer_name = models.CharField(max_length=120)
    email = models.EmailField()
    customer_phone = models.CharField(max_length=32, blank=True)
    address = models.CharField(max_length=300)
    saved_address = models.ForeignKey(
        SavedAddress, null=True, blank=True, on_delete=models.SET_NULL
    )

    subtotal = models.IntegerField(default=0)
    discount_amount = models.IntegerField(default=0)
    delivery_fee = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)
    coupon_code = models.CharField(max_length=32, blank=True)
    coupon_snapshot = models.JSONField(default=dict, blank=True)

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.CREATED
    )
    delivery_requested = models.BooleanField(default=False)
    delivery_status = models.CharField(
        max_length=30, choices=DeliveryStatus.choices, default=DeliveryStatus.NONE
    )
    delivery_address = models.CharField(max_length=300, blank=True)
    delivery_datetime = models.DateTimeField(null=True, blank=True)
    delivery_slot = models.CharField(max_length=80, blank=True)
    delivery_day = models.DateField(null=True, blank=True)
    delivery_comment = models.CharField(max_length=300, blank=True)

    is_gift = models.BooleanField(default=False)
    gift_recipient_name = models.CharField(max_length=120, blank=True)
    gift_recipient_phone = models.CharField(max_length=32, blank=True)
    gift_message = models.CharField(max_length=300, blank=True)
    gift_card_signature = models.CharField(max_length=120, blank=True)

    quick_order = models.BooleanField(default=False)
    quick_order_payload = models.JSONField(default=dict, blank=True)

    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    rating_comment = models.CharField(max_length=300, null=True, blank=True)

    payment_method = models.CharField(
        max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.DEMO
    )
    payment_status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )
    payment_metadata = models.JSONField(default=dict, blank=True)
    stripe_payment_intent = models.CharField(max_length=80, blank=True)

    call_me_requested_at = models.DateTimeField(null=True, blank=True)
    address_change_requested_at = models.DateTimeField(null=True, blank=True)
    address_change_payload = models.JSONField(default=dict, blank=True)
    delivery_photo = models.ImageField(
        upload_to="delivery_photos/", null=True, blank=True
    )
    delivery_photo_uploaded_at = models.DateTimeField(null=True, blank=True)

    last_status_changed_at = models.DateTimeField(null=True, blank=True)
    last_delivery_status_changed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order #{self.id}"

    def can_transition(self, field, new_value):
        if field == "status":
            allowed = self.STATUS_TRANSITIONS.get(self.status, set())
            return new_value in allowed or new_value == self.status
        if field == "delivery_status":
            allowed = self.DELIVERY_TRANSITIONS.get(self.delivery_status, set())
            return new_value in allowed or new_value == self.delivery_status
        return True


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(default=1)
    price_at_purchase = models.IntegerField(default=0)
    product_name = models.CharField(max_length=120, blank=True)
    product_category = models.CharField(max_length=80, blank=True)
    product_image_url = models.URLField(blank=True)

    def save(self, *args, **kwargs):
        if not self.product_name:
            self.product_name = self.product.name
        if not self.product_category:
            self.product_category = self.product.category
        if not self.product_image_url:
            self.product_image_url = self.product.image_url
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} x{self.qty}"


class ProductReview(TimeStampedModel):
    product = models.ForeignKey(
        Product, related_name="reviews", on_delete=models.CASCADE
    )
    order_item = models.ForeignKey(
        OrderItem, null=True, blank=True, on_delete=models.SET_NULL
    )
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    email = models.EmailField(blank=True)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=120, blank=True)
    comment = models.TextField(blank=True)
    recommend = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.product} ★{self.rating}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_product_cache()

    def delete(self, *args, **kwargs):
        product = self.product
        super().delete(*args, **kwargs)
        self.update_product_cache(product)

    def update_product_cache(self, product=None):
        product = product or self.product
        agg = product.reviews.aggregate(
            avg=models.Avg("rating"), count=models.Count("id")
        )
        product.rating_avg = round(agg["avg"] or 0, 2)
        product.rating_count = agg["count"] or 0
        product.save(update_fields=["rating_avg", "rating_count", "updated_at"])


class OrderEvent(TimeStampedModel):
    order = models.ForeignKey(Order, related_name="events", on_delete=models.CASCADE)
    kind = models.CharField(max_length=60)
    payload = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_by_email = models.EmailField(blank=True)
    source = models.CharField(max_length=60, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.kind} ({self.order_id})"


class OrderAuditLog(TimeStampedModel):
    order = models.ForeignKey(Order, related_name="audit_logs", on_delete=models.CASCADE)
    field_name = models.CharField(max_length=60)
    old_value = models.CharField(max_length=120, blank=True)
    new_value = models.CharField(max_length=120, blank=True)
    actor = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    actor_email = models.EmailField(blank=True)
    actor_ip = models.GenericIPAddressField(null=True, blank=True)
    actor_notes = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.field_name}: {self.old_value}→{self.new_value}"


class AnalyticsEvent(TimeStampedModel):
    name = models.CharField(max_length=80)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    email = models.EmailField(blank=True)
    session_id = models.CharField(max_length=64, blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["name", "created_at"]),
        ]

    def __str__(self):
        return f"{self.name} @ {self.created_at}"
