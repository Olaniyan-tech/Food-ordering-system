from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework import status
from food.models import Food, Order, OrderItem
from .serializers import FoodSerializer, OrderSerializer, AddToCartSerializer, OrderDeliveryDetailSerializer



class AllFoodView(generics.ListAPIView):
        queryset = Food.objects.filter(available=True)
        serializer_class = FoodSerializer
        

class AllOrdersView(generics.ListAPIView):
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


# --- Add / Increase item ---
class AddToCartView(APIView):
    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        

        food_id = serializer.validated_data["food"]
        quantity = serializer.validated_data["quantity"]

        try:
            food = Food.objects.get(id=food_id, available=True)
        except Food.DoesNotExist:
            return Response({"error": "Food not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            order, _ = Order.objects.get_or_create(user=request.user, status="pending")
        except Order.DoesNotExist:
            return Response({"error": "Cart is empty"})

        order.add_item(food, quantity)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

# --- Decrease quantity or remove item ---
class RemoveFromCartView(APIView):
    def post(self, request):
        user = request.user
        item_id = request.data.get("item_id")
        action = request.data.get("action")  # 'decrease' or 'delete'

        try:
            order = Order.objects.get(user=user, status="pending")
        except Order.DoesNotExist:
            return Response({"error": "Cart is empty"}, status=status.HTTP_404_NOT_FOUND)

        try:
            item = order.remove_item(item_id=item_id, action=action)
        except OrderItem.DoesNotExist:
            return Response({"error": "Item not found in cart"}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CancelCartView(APIView):
    def delete(self, request):
        user = request.user

        try:
            order = Order.objects.get(user=user, status="pending")
        except Order.DoesNotExist:
            return Response({"error": "No pending order to cancel"}, status=status.HTTP_404_NOT_FOUND)

        order.status = "cancelled"
        order.save(update_fields=["status"])
        return Response({"message" : "Cart cancelled successfully"}, status=status.HTTP_200_OK)

class UpdateOrderDetailView(APIView):
    def patch(self, request):
        try:
            order = Order.objects.get(user=request.user, status="pending")
        except Order.DoesNotExist:
            return Response({"error" : "No pending order"}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderDeliveryDetailSerializer(order, data=request.data, partial=True)
        
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message" : "Order details updated"}, status=status.HTTP_200_OK)

# --- Checkout ---
class CheckOutView(APIView):
    def post(self, request):
        user = request.user
        try:
            order = Order.objects.get(user=user, status="pending")

        except Order.DoesNotExist:
            return Response({"error": "No pending order to checkout"}, status=status.HTTP_404_NOT_FOUND)
        
        if not order.address or not order.phone:
            return Response({"error" : "Address and phone number are required"}, status=status.HTTP_400_BAD_REQUEST)

        order.status = "out for delivery"
        order.save(update_fields=["status"])
        return Response(
            {"message": "Order checked out successfully",
            "user" : user.username,
            "address" : order.address,
            "phone" : order.phone,
            "status" : order.status,
            "total" : order.total}, 
            status=status.HTTP_200_OK)