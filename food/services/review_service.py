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

