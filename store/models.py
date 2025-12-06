"""
Store models
"""

from django.db import models
from django.utils import timezone
import datetime


class Candy(models.Model):
    """Candy model"""

    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    category = models.CharField(max_length=100)
    image_url = models.URLField(blank=True, default="")

    class Meta:
        verbose_name_plural = "candies"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Order(models.Model):
    """Order model"""

    STATUS_CREATED = "Created"
    STATUS_SHIPPED = "Shipped"
    STATUS_DELIVERED = "Delivered"

    STATUS_CHOICES = (
        (STATUS_CREATED, "Created"),
        (STATUS_SHIPPED, "Shipped"),
        (STATUS_DELIVERED, "Delivered"),
    )

    user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default=STATUS_CREATED
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def update_status_based_on_time(self):
        """
        Simulate order processing:
        Created -> Shipped (after 1 min)
        Shipped -> Delivered (after 2 mins from creation)
        """
        if self.status == self.STATUS_DELIVERED:
            return

        now = timezone.now()
        diff = now - self.created_at
        updated = False

        if self.status == self.STATUS_CREATED and diff >= datetime.timedelta(minutes=1):
            self.status = self.STATUS_SHIPPED
            self.shipped_at = now
            updated = True

        if self.status == self.STATUS_SHIPPED and diff >= datetime.timedelta(minutes=2):
            self.status = self.STATUS_DELIVERED
            self.delivered_at = now
            updated = True

        if updated:
            self.save()

    def __str__(self):
        return f"Order {self.id} - {self.status}"


class OrderItem(models.Model):
    """Order Item model"""

    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Candy, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
