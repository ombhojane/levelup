from django.db import models
from django.utils import timezone

class Customer(models.Model):
    customer_id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    state = models.CharField(max_length=100)
    account_type = models.CharField(max_length=50)
    balance_tier = models.CharField(max_length=50)
    credit_card_user = models.BooleanField(default=False)
    loan_status = models.CharField(max_length=50)
    relationship_tenure = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class EmailTemplate(models.Model):
    subject = models.CharField(max_length=200)
    content = models.TextField()
    segment_type = models.CharField(max_length=100)
    subcategory = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)
    scheduled_time = models.DateTimeField(null=True, blank=True)
    is_recurring = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='draft')
    recipient_count = models.IntegerField(default=0)

    def __str__(self):
        return self.subject