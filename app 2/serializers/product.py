from django.db import transaction
from rest_framework import serializers

from ..models.product import Product, ProductAnalysis, ProductSpacification


class ProductSpacificationSerializer(serializers.ModelSerializer):
    # id = serializers.UUIDField(required=False)

    class Meta:
        model = ProductSpacification
        fields = "__all__"


class ProductAnalysisSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)

    class Meta:
        model = ProductAnalysis
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    product_spacification = ProductSpacificationSerializer(many=True, required=False)
    product_analysis = ProductAnalysisSerializer(required=False)

    class Meta:
        model = Product
        fields = "__all__"


class CustomProductSerializer(serializers.ModelSerializer):
    product_spacification = ProductSpacificationSerializer(many=True, required=False)

    class Meta:
        model = ProductAnalysis
        fields = [
            "product_spacification",
            "walton_price",
            "lower_one_breakdown",
            "lower_two_breakdown",
            "product",
        ]

    @transaction.atomic
    def create(self, validated_data):
        product_spacifications_data = validated_data.pop("product_spacification", [])
        product = validated_data.pop("product")
        product_analysis = ProductAnalysis.objects.create(
            product=product, **validated_data
        )
        for spacification_data in product_spacifications_data:
            product = spacification_data.pop("product")
            ProductSpacification.objects.create(product=product, **spacification_data)
        # Set the product's is_reviewed field to True
        product.is_reviewed = True
        product.save()
        return product_analysis

    @transaction.atomic
    def update(self, instance, validated_data):
        # Update the main product fields
        instance.walton_price = validated_data.get(
            "walton_price", instance.walton_price
        )
        instance.lower_one_breakdown = validated_data.get(
            "lower_one_breakdown", instance.lower_one_breakdown
        )
        instance.lower_two_breakdown = validated_data.get(
            "lower_two_breakdown", instance.lower_two_breakdown
        )
        instance.product = validated_data.get("product", instance.product)
        # Handle nested product_spacification data
        product_spacifications_data = validated_data.pop("product_spacification", [])
        # Delete all ProductSpacification instance
        ProductSpacification.objects.filter(product=instance.product).delete()
        # Create new ProductSpacification instances
        for spacification_data in product_spacifications_data:
            product = spacification_data.pop("product")
            ProductSpacification.objects.create(product=product, **spacification_data)

        # Save the updated product instance
        instance.product.is_reviewed = True
        instance.save()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["id"] = str(instance.id)
        product_spacifications = ProductSpacification.objects.filter(
            product=instance.product
        )
        representation["product_spacification"] = ProductSpacificationSerializer(
            product_spacifications, many=True
        ).data
        return representation
