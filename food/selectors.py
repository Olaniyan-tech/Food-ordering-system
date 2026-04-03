from food.models import Food, Order, Review, Vendor
from django.db.models import Avg, Count, Sum, Q
from django.core.cache import cache

def get_available_foods(vendor=None):
    qs = Food.objects.filter(available=True).select_related("vendor", "category")
    if vendor:
        qs = qs.filter(vendor=vendor)
    return qs

def get_food_by_id(food_id):
    return Food.objects.select_related("vendor", "category").get(id=food_id)

def get_available_food_by_id(food_id):
    return Food.objects.select_related("vendor", "category").get(id=food_id, available=True)

def get_user_orders(user):
    return Order.objects.prefetch_related(
        "items__food"
    ).filter(user=user).order_by("-created_at")

def get_pending_order(user):
    return Order.objects.prefetch_related(
        "items__food"
    ).filter(user=user, status="PENDING").first()

def get_order_by_id(order_id):
    return Order.objects.prefetch_related(
        "items__food"
    ).get(id=order_id)

def get_user_order_by_id(order_id, user):
    return Order.objects.prefetch_related(
        "items__food"
    ).get(id=order_id, user=user)

def get_order_by_id_for_email(order_id):
    return Order.objects.select_related(
        "user"
    ).get(id=order_id)

def get_order_by_reference(reference, user):
    return Order.objects.get(
        payment_reference=reference, 
        user=user
    )

def get_order_review(order):
    try:
        return order.review
    except Review.DoesNotExist:
        return None

def get_food_reviews(food_id):
    return Review.objects.filter(
            order__items__food__id=food_id
        ).select_related("user").order_by("-created_at")

def get_food_review_stats(food_id):
    cache_key = f"food_reviews_stats_{food_id}"
    stats = cache.get(cache_key)

    if stats is None:
        result = Review.objects.filter(
            order__items__food__id=food_id
        ).aggregate(
            average_rating=Avg("rating"),
            total_reviews=Count("id")
        )

        stats = {
            "average_rating": round(result["average_rating"] or 0, 1),
            "total_reviews": result["total_reviews"] or 0
        }
        cache.set(cache_key, stats, timeout=300)
    
    return stats

def get_all_vendors():
    return Vendor.objects.filter(
        is_approved=True,
        is_active=True
    )

def get_vendor_by_slug(slug):
    return Vendor.objects.get(slug=slug, is_active=True, is_approved=True)

def get_vendor_by_id(vendor_id):
    return Vendor.objects.get(id=vendor_id)

def get_pending_vendors():
    return Vendor.objects.filter(is_approved=False)

def get_vendor_foods(vendor, available_only=False):
    qs = Food.objects.filter(vendor=vendor).select_related("category")
    if available_only:
        qs = qs.filter(available=True)
    return qs

def get_vendor_orders(vendor):
    return Order.objects.filter(vendor=vendor).prefetch_related(
        "items__food"
    ).select_related("user").order_by("-created_at")

def get_vendor_order_by_id(vendor, order_id):
    return Order.objects.prefetch_related(
        "items__food"
    ).get(id=order_id, vendor=vendor)

def get_vendor_reviews(vendor):
    return Review.objects.filter(
        vendor=vendor
    ).select_related("user", "order").order_by("-created_at")

def get_vendor_review_stats(vendor_id):
    cache_key = f"vendor_review_stats_{vendor_id}"
    stats = cache.get(cache_key)

    if stats is None:
        result = Review.objects.filter(
            vendor_id=vendor_id,
        ).aggregate(
            average_rating=Avg("rating"),
            total_reviews=Count("id")
        )
        stats = {
            "average_rating": round(result["average_rating"] or 0, 1),
            "total_reviews": result["total_reviews"] or 0
        }
        cache.set(cache_key, stats, timeout=300)
    
    return stats

def get_vendor_dashboard_stats(vendor):
    stats = Order.objects.filter(vendor=vendor).aggregate(
        total_orders=Count("id"),
        pending_orders=Count("id", filter=Q(status="PENDING")),
        confirmed_orders=Count("id", filter=Q(status="CONFIRMED")),
        preparing_orders=Count("id", filter=Q(status="PREPARING")),
        ready_orders=Count("id", filter=Q(status="READY")),
        out_for_delivery_orders=Count("id", filter=Q(status="OUT FOR DELIVERY")),
        delivered_orders=Count("id", filter=Q(status="DELIVERED")),
        cancelled_orders=Count("id", filter=Q(status="CANCELLED")),
        total_earnings=Sum("total", filter=Q(payment_status="PAID")),
    )

    return {
        "total_orders": stats["total_orders"] or 0,
        "total_earnings": stats["total_earnings"] or 0,
        "total_foods": Food.objects.filter(vendor=vendor).count(),

        "order_breakdown": {
            "pending_orders": stats["pending_orders"] or 0,
            "confirmed_orders": stats["confirmed_orders"] or 0,
            "preparing_orders": stats["preparing_orders"] or 0,
            "ready_orders": stats["ready_orders"] or 0,
            "out_for_delivery_orders": stats["out_for_delivery_orders"] or 0,
            "delivered_orders": stats["delivered_orders"] or 0,
            "cancelled_orders": stats["cancelled_orders"] or 0,
        },
    }



# def get_food_by_id(food_id):
#     return Food.objects.get(id=food_id)

# def get_foods_by_category(category_slug):
#     return Food.objects.filter(
#         category__slug=category_slug,
#         available=True
#     ).select_related("category")
