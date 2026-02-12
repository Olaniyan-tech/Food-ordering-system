from django.db import models
from django.db.models import Q, UniqueConstraint
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify


# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=70, db_index=True)
    slug = models.SlugField(max_length=70, unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Food(models.Model):
    category = models.ForeignKey(Category, related_name="food", null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=70, db_index=True)
    slug = models.CharField(max_length=70, db_index=True, blank=True)
    descriptions = models.TextField(blank=True)
    price = models.FloatField()
    image_url = models.ImageField(upload_to="images/", null=True, blank=True)
    available = models.BooleanField(default=True)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    # class Meta:
    #     ordering = ('category', 'name',)
    #     index_together = (('id', 'slug'), )

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS = [
        ("pending", "Pending"),
        ("out for delivery", "Out for delivery"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled")
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    
    address = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="pending")
    total = models.FloatField(default=0.0)
    date_created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["user"],
                condition=Q(status="pending"),
                name="unique_pending_order_per_user"
            )
        ]
    
    def add_item(self, food, quantity=1):
        item, created = OrderItem.objects.get_or_create(
            order=self, 
            food=food,
            defaults={"quantity": quantity, 'price_at_purchase': food.price})
        
        if not created:
            item.quantity += quantity
            item.save()
        self.update_total()
    
    def remove_item(self, item_id, action):
        item = self.items.get(id=item_id)
        if action == "decrease":
            item.quantity -= 1
            if item.quantity <= 0:
                item.delete()
            else:
                item.save()
        elif action == "delete":
            item.delete()
        else:
            raise ValueError("Invalid action")
        self.update_total()

    def update_total(self):
        self.total = sum(item.subtotal for item in self.items.all())
        self.save(update_fields=["total"])
    
    def save(self, *args, **kwargs):
        if not self.phone and hasattr(self.user, "profile"):
            self.phone = self.user.profile.phone
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    food = models.ForeignKey(Food, on_delete=models.CASCADE, related_name="food_items")
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    subtotal = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{self.quantity} * {self.food.name}"
    
    def save(self, *args, **kwargs):
        if self.price_at_purchase is None:
            self.price_at_purchase = self.food.price
        self.subtotal = float(self.quantity) * float(self.price_at_purchase)
        super().save(*args, **kwargs)

