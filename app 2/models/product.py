import uuid

from django.db import models
from django.db.models import CASCADE

from core.mixins import AuditLogMixin

from .tender import Tender


# This product tabel stores several products of a tender.
class Product(AuditLogMixin):
    id = models.UUIDField(editable=False, primary_key=True, default=uuid.uuid4)
    product_name = models.CharField(max_length=100, null=True, blank=True)
    product_brand = models.CharField(max_length=100, null=True, blank=True)
    model_number = models.CharField(max_length=100, null=True, blank=True)
    warranty = models.CharField(max_length=255, null=True, blank=True)
    product_qty = models.CharField(max_length=255, null=True, blank=True)
    tender = models.ForeignKey(Tender, on_delete=CASCADE, related_name="products")
    is_reviewed = models.BooleanField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.product_name


class ProductSpacification(AuditLogMixin):
    id = models.UUIDField(editable=False, primary_key=True, default=uuid.uuid4)
    spacification_name = models.CharField(max_length=100, null=True, blank=True)
    required_spacification = models.CharField(max_length=100, null=True, blank=True)
    walton_spacification = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Walton Offered Spacification",
    )
    compettitors_spacification_one = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Compettitors One Offered Spacification",
    )
    compettitors_spacification_two = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Compettitors Two Offered Spacification",
    )
    product = models.ForeignKey(
        Product, on_delete=CASCADE, related_name="product_spacification"
    )

    def __str__(self) -> str:
        return self.spacification_name


class ProductAnalysis(AuditLogMixin):
    id = models.UUIDField(editable=False, primary_key=True, default=uuid.uuid4)
    walton_price = models.CharField(max_length=100, null=True, blank=True)
    lower_one_breakdown = models.CharField(max_length=100, null=True, blank=True)
    lower_two_breakdown = models.CharField(max_length=100, null=True, blank=True)
    product = models.OneToOneField(
        Product, on_delete=CASCADE, related_name="product_analysis"
    )
