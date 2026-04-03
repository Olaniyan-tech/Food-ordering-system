from food.models import Vendor, Food
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.cache import cache

@transaction.atomic
def register_vendor(user, validated_data):
    if hasattr(user, "vendor"):
        raise ValidationError("You already have a vendor profile.")
    
    if Vendor.objects.filter(
        business_name__iexact=validated_data["business_name"]
        ).exists():
        raise ValidationError("A vendor with this business name already exists.")
    
    vendor = Vendor.objects.create(user=user, **validated_data)
    return vendor

@transaction.atomic
def update_vendor_profile(vendor, validated_data):
    for field, value in validated_data.items():
        setattr(vendor, field, value)
    vendor.save()
    return vendor

@transaction.atomic
def approve_vendor(vendor, approved_by):
    if vendor.is_approved:
        raise ValidationError("Vendor is already approved")
    vendor.is_approved = True
    vendor.is_active = True
    vendor.save(update_fields=["is_approved", "is_active", "updated_at"])
    return vendor

@transaction.atomic
def reject_vendor(vendor, rejected_by):
    if vendor.is_approved:
        raise ValidationError("Cannot reject an already approved vendor.")
    vendor.is_active = False
    vendor.save(update_fields=["is_active", "updated_at"])
    return vendor

@transaction.atomic
def deactivate_vendor(vendor, deactivated_by):
    if not vendor.is_active:
        raise ValidationError("Vendor is already deactivated.")
    vendor.is_active = False
    vendor.save(update_fields=["is_active", "updated_at"])
    return vendor

@transaction.atomic
def activate_vendor(vendor, activated_by):
    if vendor.is_active:
        raise ValidationError("Vendor is already active.")
    if not vendor.is_approved:
        raise ValidationError("Vendor must be approved before activation.")
    vendor.is_active = True
    vendor.save(update_fields=["is_active", "updated_at"])
    return vendor

@transaction.atomic
def create_food(vendor, validated_data):
    if not vendor.is_approved:
        raise ValidationError("Your account must be approved before adding foods.")

    food = Food.objects.create(vendor=vendor, **validated_data)
    return food

@transaction.atomic
def update_food(food, validated_data):
    for field, value in validated_data.items():
        setattr(food, field, value)
    food.save()
    return food

@transaction.atomic
def delete_food(food):
    food.delete()

@transaction.atomic
def toggle_food_availability(food):
    food.available = not food.available
    food.save(update_fields=["available", "updated_at"])
    return food

@transaction.atomic
def update_food_stock(food, quantity):
    food.stock = quantity
    if food.stock == 0:
        food.available = False
    food.save(update_fields=["stock", "available", "updated_at"])
    return food
