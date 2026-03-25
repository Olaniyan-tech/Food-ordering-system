from django.core.exceptions import ValidationError
from food.models import Review

def create_review(order, user, validated_data):
    if order.user != user:
        raise ValidationError("You can only review your own orders")
    
    if order.status != "DELIVERED":
        raise ValidationError("You can only review delivered orders")
    
    if hasattr(order, "review"):
        raise ValidationError("You have already reviewed this order")
    
    return Review.objects.create(
        order=order,
        user=user,
        **validated_data
    )

def get_order_review(order, user):
    if order.user != user:
        raise ValidationError("You can only view your own order review")
    
    try:
        return order.review    
    except Review.DoesNotExist:
        raise ValidationError("No review found for this order")

def get_food_reviews(food_id):
    return Review.objects.filter(
        order__items__food__id=food_id
    ).select_related("user").order_by("-created_at")