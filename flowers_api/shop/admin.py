import csv
from io import BytesIO

from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from openpyxl import Workbook

from .models import (
    Coupon,
    Favorite,
    Order,
    OrderEvent,
    OrderItem,
    Product,
    ProductReview,
    SavedAddress,
)
from .telegram import notify_delivery_status_changed, notify_status_changed


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "price", "rating_avg", "created_at")
    list_filter = ("category", "created_at")
    search_fields = ("name", "category")
    ordering = ("-created_at",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("price_at_purchase",)


class OrderEventInline(admin.TabularInline):
    model = OrderEvent
    extra = 0
    readonly_fields = ("kind", "payload", "created_at", "created_by", "source")
    can_delete = False
    max_num = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer_name",
        "email",
        "status_badge",
        "delivery_status",
        "total",
        "created_at",
    )
    list_filter = ("status", "delivery_status", "payment_method", "created_at")
    search_fields = ("customer_name", "email", "address", "delivery_address")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    inlines = [OrderItemInline, OrderEventInline]
    readonly_fields = ("created_at", "updated_at", "delivery_photo")
    actions = [
        "mark_processing",
        "mark_delivering",
        "mark_completed",
        "mark_canceled",
        "export_csv",
        "export_excel",
    ]

    def status_badge(self, obj):
        colors = {
            "created": "#e9d5ff",
            "processing": "#c7d2fe",
            "delivering": "#fde68a",
            "completed": "#bbf7d0",
            "canceled": "#fecaca",
        }
        color = colors.get(obj.status, "#e5e7eb")
        return format_html(
            '<span style="padding:2px 8px;border-radius:999px;background:#140d19;'
            'border:1px solid #3b2a58;color:{};font-size:12px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Статус"

    def _bulk_status(self, queryset, new_status=None, new_dstatus=None):
        for order in queryset:
            if new_status and order.status != new_status:
                old = order.status
                order.status = new_status
                order.save(update_fields=["status"])
                try:
                    notify_status_changed(order, old, new_status)
                except Exception:
                    pass
            if new_dstatus and order.delivery_status != new_dstatus:
                old_delivery = order.delivery_status
                order.delivery_status = new_dstatus
                order.save(update_fields=["delivery_status"])
                try:
                    notify_delivery_status_changed(order, old_delivery, new_dstatus)
                except Exception:
                    pass

    def export_csv(self, request, queryset):
        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = "attachment; filename=orders.csv"
        writer = csv.writer(resp)
        writer.writerow(
            [
                "id",
                "name",
                "email",
                "address",
                "total",
                "status",
                "delivery_status",
                "rating",
                "comment",
                "created_at",
            ]
        )
        for order in queryset:
            writer.writerow(
                [
                    order.id,
                    order.customer_name,
                    order.email,
                    order.delivery_address or order.address,
                    order.total,
                    order.status,
                    order.delivery_status,
                    order.rating or "",
                    order.rating_comment or "",
                    order.created_at,
                ]
            )
        return resp

    export_csv.short_description = "Экспорт в CSV"

    def export_excel(self, request, queryset):
        wb = Workbook()
        ws = wb.active
        ws.title = "Orders"
        ws.append(
            [
                "ID",
                "Name",
                "Email",
                "Address",
                "Total",
                "Status",
                "Delivery",
                "Payment",
                "Created",
            ]
        )
        for order in queryset:
            ws.append(
                [
                    order.id,
                    order.customer_name,
                    order.email,
                    order.delivery_address or order.address,
                    order.total,
                    order.status,
                    order.delivery_status,
                    order.payment_method,
                    order.created_at.strftime("%Y-%m-%d %H:%M"),
                ]
            )

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        resp = HttpResponse(
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        resp["Content-Disposition"] = "attachment; filename=orders.xlsx"
        return resp

    export_excel.short_description = "Экспорт в Excel"

    def mark_processing(self, request, queryset):
        self._bulk_status(queryset, new_status="processing")

    mark_processing.short_description = "Статус → processing"

    def mark_delivering(self, request, queryset):
        self._bulk_status(
            queryset, new_status="delivering", new_dstatus="out_for_delivery"
        )

    mark_delivering.short_description = "Статус → delivering"

    def mark_completed(self, request, queryset):
        self._bulk_status(queryset, new_status="completed", new_dstatus="delivered")

    mark_completed.short_description = "Статус → completed"

    def mark_canceled(self, request, queryset):
        self._bulk_status(queryset, new_status="canceled")

    mark_canceled.short_description = "Статус → canceled"


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "discount_type",
        "value",
        "is_active",
        "usage_limit",
        "used_count",
        "valid_from",
        "valid_until",
    )
    list_filter = ("discount_type", "is_active", "valid_from", "valid_until")
    search_fields = ("code", "notes")
    ordering = ("-valid_until", "-created_at")


@admin.register(SavedAddress)
class SavedAddressAdmin(admin.ModelAdmin):
    list_display = ("id", "label", "user", "email", "address", "is_default", "created_at")
    list_filter = ("is_default", "created_at")
    search_fields = ("label", "address", "email", "user__email")
    ordering = ("-created_at",)


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "rating", "recommend", "created_at")
    list_filter = ("rating", "recommend", "created_at")
    search_fields = ("product__name", "title", "comment", "email")
    ordering = ("-created_at",)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "email", "created_at")
    search_fields = ("product__name", "user__email", "email")
    ordering = ("-created_at",)
