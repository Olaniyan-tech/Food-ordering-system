from django.core.exceptions import ValidationError
from food.models import Review
from django.core.cache import cache

def create_review(order, user, validated_data):
    if order.user != user:
        raise ValidationError("You can only review your own orders")
    
    if order.status != "DELIVERED":
        raise ValidationError("You can only review delivered orders")
    
    if hasattr(order, "review"):
        raise ValidationError("You have already reviewed this order")
    
    validated_data.pop("vendor", None)
    validated_data.pop("order", None)
    
    review = Review(
        order=order,
        user=user,
        vendor=order.vendor,
        **validated_data
    )
    review.full_clean()
    review.save()

    food_ids = order.items.values_list("food__id", flat=True)
    for food_id in food_ids:
        cache.delete(f"food_reviews_stats_{food_id}")
    if order.vendor_id:
        cache.delete(f"vendor_reviews_stats_{order.vendor_id}")
    
    return review



