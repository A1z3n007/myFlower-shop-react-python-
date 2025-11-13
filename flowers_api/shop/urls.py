from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AccountProfileApiView,
    AddressSuggestView,
    AnalyticsEventView,
    FavoritesApiView,
    ProductReviewViewSet,
    ProductViewSet,
    OrderViewSet,
    QuickOrderView,
    SavedAddressView,
    StripeIntentView,
    StripeWebhookView,
    change_address_view,
    call_me_view,
    cancel_order_view,
    confirm_received_view,
    CouponValidateView,
    delivery_photo_view,
    delivery_slots_view,
    rate_order_view,
    repeat_order_view,
)

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="products")
router.register(r"orders", OrderViewSet, basename="orders")
router.register(r"product-reviews", ProductReviewViewSet, basename="product-reviews")

urlpatterns = [
    path("orders/confirm/<str:token>/", confirm_received_view, name="order-confirm"),
    path("orders/cancel/<str:token>/", cancel_order_view, name="order-cancel"),
    path("orders/rate/<str:token>/", rate_order_view, name="order-rate"),
    path("orders/repeat/<str:token>/", repeat_order_view, name="order-repeat"),
    path("orders/call/<str:token>/", call_me_view, name="order-call-me"),
    path(
        "orders/change-address/<str:token>/",
        change_address_view,
        name="order-change-address",
    ),
    path("orders/photo/<str:token>/", delivery_photo_view, name="order-photo"),
    path("orders/quick/", QuickOrderView.as_view()),
    path("account/profile/", AccountProfileApiView.as_view()),
    path("account/favorites/", FavoritesApiView.as_view()),
    path("account/addresses/", SavedAddressView.as_view()),
    path("coupons/validate/", CouponValidateView.as_view()),
    path("delivery/slots/", delivery_slots_view),
    path("delivery/autocomplete/", AddressSuggestView.as_view()),
    path("analytics/events/", AnalyticsEventView.as_view()),
    path("payments/stripe/intent/", StripeIntentView.as_view()),
    path("payments/stripe/webhook/", StripeWebhookView.as_view()),
    path("", include(router.urls)),
]
