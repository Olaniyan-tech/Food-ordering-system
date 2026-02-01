
from django.urls import path
from .views import(
    AllFoodView, 
    AddToCartView,
    RemoveFromCartView,
    CancelCartView,
    UpdateOrderDetailView, 
    CheckOutView, 
    AllOrdersView
)


urlpatterns = [
    path("foods/", AllFoodView.as_view()),
    path("my-orders/", AllOrdersView.as_view()),
    path("add_to_cart/", AddToCartView.as_view()),
    path("remove/", RemoveFromCartView.as_view()),
    path("cancel/", CancelCartView.as_view()),
    path("order/details/", UpdateOrderDetailView.as_view()),
    path("checkout/", CheckOutView.as_view())
]
