from django.db import models
from django.db.models import Avg, F
from django.core.exceptions import ValidationError
from django.utils.timezone import now

STATUS_CHOICES = (
    ("pending", "Pending"),
    ("completed", "Completed"),
    ("canceled", "Canceled"),
)

class Vendor(models.Model):
    """
    Represents a vendor with comprehensive details and metrics assessing their performance.
    Attributes:
        name (CharField): The name of the vendor.
        contact_details (TextField): Contact information for the vendor.
        address (TextField): Physical address of the vendor.
        vendor_code (CharField): A unique identifier for the vendor.
    """
    name = models.CharField(max_length=255)
    contact_details = models.TextField()
    address = models.TextField()
    vendor_code = models.CharField(max_length=100, unique=True)

    def __str__(self):
        """Returns the string representation of the Vendor, which is its name."""
        return self.name

    def on_time_delivery_rate(self):
        """
        Calculates the percentage of completed purchase orders that were delivered on or before their due date.
        Returns:
            float: The on-time delivery rate as a percentage.
        """
        total_completed = self.purchase_orders.filter(status='completed').count()
        if total_completed == 0:
            return 0
        on_time_orders = self.purchase_orders.filter(status='completed', delivery_date__lte=F('order_date')).count()
        return (on_time_orders / total_completed) * 100

    def quality_rating_avg(self):
        """
        Calculates the average quality rating for all completed purchase orders.
        Returns:
            float: The average quality rating, or 0 if there are no ratings.
        """
        result = self.purchase_orders.filter(status='completed').aggregate(Avg('quality_rating'))
        return result['quality_rating__avg'] or 0

    def average_response_time(self):
        """
        Calculates the average time taken for the vendor to acknowledge the purchase orders.
        Returns:
            float: The average response time in seconds.
        """
        responses = self.purchase_orders.exclude(acknowledgment_date=None)
        total_time = sum((po.acknowledgment_date - po.issue_date).total_seconds() for po in responses)
        return (total_time / responses.count()) if responses.exists() else 0

    def fulfillment_rate(self):
        """
        Calculates the percentage of all purchase orders that have been completed.
        Returns:
            float: The fulfillment rate as a percentage.
        """
        total_orders = self.purchase_orders.count()
        if total_orders == 0:
            return 0
        completed_orders = self.purchase_orders.filter(status='completed').count()
        return (completed_orders / total_orders) * 100

class PurchaseOrder(models.Model):
    """
    Tracks purchase orders issued to vendors, including their fulfillment status and quality.
    Attributes:
        po_number (CharField): The unique identifier for the purchase order.
        vendor (ForeignKey): The vendor to whom the order is issued.
        order_date (DateTimeField): The date the order was placed.
        delivery_date (DateTimeField): The expected or actual delivery date of the order.
        items (JSONField): Details of the items ordered.
        quantity (IntegerField): The total quantity of items ordered.
        status (CharField): The current status of the order.
        quality_rating (FloatField): The quality rating given to the vendor for this order.
        issue_date (DateTimeField): The timestamp when the order was issued.
        acknowledgment_date (DateTimeField): The timestamp when the order was acknowledged by the vendor.
    """
    po_number = models.CharField(max_length=100, unique=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='purchase_orders')
    order_date = models.DateTimeField()
    delivery_date = models.DateTimeField()
    items = models.JSONField()
    quantity = models.IntegerField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    quality_rating = models.FloatField(null=True, blank=True)
    issue_date = models.DateTimeField(auto_now_add=True)
    acknowledgment_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        """Returns the string representation of the Purchase Order, which is its PO number."""
        return self.po_number

    def save(self, *args, **kwargs):
        """
        Validates that the delivery date is not set before the order date before saving to ensure data integrity.
        """
        if self.delivery_date and self.delivery_date < self.order_date:
            raise ValidationError("Delivery date cannot be earlier than the order date.")
        super().save(*args, **kwargs)

class HistoricalPerformance(models.Model):
    """
    Stores historical data on vendor performance, allowing for trend analysis over time.
    Attributes:
        vendor (ForeignKey): The vendor associated with the historical data.
        date (DateTimeField): The date when the record was created.
        on_time_delivery_rate (FloatField): Historical on-time delivery rate.
        quality_rating_avg (FloatField): Historical average quality rating.
        average_response_time (FloatField): Historical average response time.
        fulfillment_rate (FloatField): Historical fulfillment rate.
    """
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='performance_history')
    date = models.DateTimeField(auto_now_add=True)
    on_time_delivery_rate = models.FloatField()
    quality_rating_avg = models.FloatField()
    average_response_time = models.FloatField()
    fulfillment_rate = models.FloatField()

    def __str__(self):
        """Returns a string representation showing the vendor and the date of the performance record."""
        return f"{self.vendor.name} - {self.date.strftime('%Y-%m-%d')}"
