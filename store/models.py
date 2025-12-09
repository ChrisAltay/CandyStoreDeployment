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
    STATUS_CANCELLED = "Cancelled"

    STATUS_CHOICES = (
        (STATUS_CREATED, "Created"),
        (STATUS_SHIPPED, "Shipped"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CANCELLED, "Cancelled"),
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

    # Added fields to match database schema from 'customerfeature-checkout-page' branch
    full_name = models.CharField(max_length=200, default="")
    address = models.CharField(max_length=255, default="")
    city = models.CharField(max_length=100, default="")
    zip_code = models.CharField(max_length=20, default="")

    def cancel_order(self):
        """
        Cancel the order and restore stock for all items.
        Only allowed if order status is 'Created'.
        Returns True if successful, False otherwise.
        """
        if self.status != self.STATUS_CREATED:
            return False

        # Restore stock for all items
        for item in self.items.all():
            item.product.stock += item.quantity
            item.product.save()

        # Update order status
        self.status = self.STATUS_CANCELLED
        self.save()
        return True

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

        # Status transitions based on elapsed time
        if diff >= datetime.timedelta(minutes=1):
            if self.status == self.STATUS_CREATED:
                self.status = self.STATUS_SHIPPED
                # Backdate the timestamp to when it 'should' have happened
                self.shipped_at = self.created_at + datetime.timedelta(minutes=1)
                self.save()

        if diff >= datetime.timedelta(minutes=2):
            if self.status in [self.STATUS_CREATED, self.STATUS_SHIPPED]:
                self.status = self.STATUS_DELIVERED
                # Ensure shipped_at is set if skipped
                if not self.shipped_at:
                    self.shipped_at = self.created_at + datetime.timedelta(minutes=1)
                self.delivered_at = self.created_at + datetime.timedelta(minutes=2)
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


class Favorite(models.Model):
    """Favorite model for users to save candies"""

    user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="favorites"
    )
    candy = models.ForeignKey(
        Candy, on_delete=models.CASCADE, related_name="favorited_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "candy")

    def __str__(self):
        return f"{self.user.username} - {self.candy.name}"


class Review(models.Model):
    """Review model for candies"""

    user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="reviews"
    )
    candy = models.ForeignKey(Candy, on_delete=models.CASCADE, related_name="reviews")
    rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)], default=5
    )  # 1-5 scale
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("user", "candy")  # Limit 1 review per candy per user

    def __str__(self):
        return f"{self.rating}* by {self.user.username} for {self.candy.name}"


class ProductWatchlist(models.Model):
    """
    Tracks products a user is watching.
    Used for low stock alerts.
    """

    user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="watchlist"
    )
    product = models.ForeignKey(
        Candy, on_delete=models.CASCADE, related_name="watchers"
    )
    # Flag to distinguish between manually added items and auto-added from orders
    auto_added = models.BooleanField(default=False)
    added_at = models.DateTimeField(auto_now_add=True)

    # Custom low stock threshold for this specific item (overrides global pref)
    custom_threshold = models.IntegerField(null=True, blank=True)

    # Track last notification to prevent spam (e.g., don't email every 5 mins)
    last_notified = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.user.username} watching {self.product.name}"


class StockAlert(models.Model):
    """
    Tracks one-time requests for 'Back in Stock' notifications.
    Automatically created when user requests alert for out-of-stock item.
    """

    user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="stock_alerts"
    )
    product = models.ForeignKey(
        Candy, on_delete=models.CASCADE, related_name="stock_alerts"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        # A user only needs one active alert per product
        # If notified=True, they can request another one later (new row or update existing)
        # For simplicity, we enforce unique active alerts
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"],
                condition=models.Q(notified=False),
                name="unique_active_alert",
            )
        ]

    def __str__(self):
        return f"Restock Alert: {self.user.username} - {self.product.name}"
