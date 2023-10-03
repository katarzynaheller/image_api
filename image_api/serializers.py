from rest_framework import serializers
from .models import (
    AccountTier,
    UploadedImage,
    UserProfile,
    DynamicImage,
)


class DynamicImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DynamicImage
        fields = ("size", "image")


class UploadedImageSerializer(serializers.ModelSerializer):
    dynamic_images = DynamicImageSerializer(many=True, read_only=True)

    class Meta:
        model = UploadedImage
        fields = ("id", "image", "upload_datetime", "dynamic_images")
