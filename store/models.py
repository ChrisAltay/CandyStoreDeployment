"""
Store models
"""

from django.db import models


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

    user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=50, default="Created")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Order {self.id}"


class OrderItem(models.Model):
    """Order Item model"""

    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Candy, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
