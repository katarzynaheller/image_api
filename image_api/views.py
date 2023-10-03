from rest_framework import viewsets, permissions
from rest_framework import serializers
from rest_framework.parsers import MultiPartParser
from rest_framework.authtoken.models import Token
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile, InMemoryUploadedFile
from rest_framework.response import Response
from .models import UploadedImage, UserProfile, DynamicImage
from .serializers import UploadedImageSerializer

from django.contrib.auth.models import User

from .utils.image_utils import calculate_width

from PIL import Image
from io import BytesIO


@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class UserUploadedImageViewSet(viewsets.ModelViewSet):
    serializer_class = UploadedImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser]

    def perform_create(self, serializer):
        uploaded_image = serializer.validated_data["image"]
        pil_image = Image.open(uploaded_image)

        min_width = 200
        min_height = 200

        if pil_image.width < min_width:
            return serializers.ValidationError(
                f"Image dimensions must be at least {min_width}x{min_height}"
            )

        user = self.request.user
        user_profile = UserProfile.objects.get(user=user)
        instance = serializer.save(user=user_profile)
        user_tier = user_profile.account_tier

        thumbnail_sizes_in_tier = user_tier.thumbnail_sizes.all()

        sizes = []
        for thumbnail_size in thumbnail_sizes_in_tier:
            height = int(thumbnail_size.height)
            width = int(calculate_width(pil_image, height))
            size = (width, height)
            sizes.append(size)

        for size in sizes:
            width, height = size
            resized_image = self.resize_image(pil_image, width, height)
            dynamic_image = DynamicImage(image_model=instance, size=height)
            dynamic_image.image.save(f"{width}x{height}.jpg", resized_image)
            dynamic_image.save()

    def resize_image(self, image, width, height):
        try:
            image = image.convert("RGB")

            resized_image = image.resize((width, height), Image.LANCZOS)

            output_buffer = BytesIO()
            resized_image.save(output_buffer, format="JPEG")
            output_buffer.seek(0)

            return output_buffer

        except Exception as e:
            return f"Error in generating thumbnails: {e}"

    def get_queryset(self):
        user = self.request.user
        user_profile = UserProfile.objects.get(user=user)

        return UploadedImage.objects.filter(user=user_profile)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        user = self.request.user
        user_profile = UserProfile.objects.get(user=user)
        user_tier = user_profile.account_tier

        if not queryset.exists():
            return Response({"message": "No uploaded images found for this user"})

        data = serializer.data

        if (
            user_tier.name == "Basic"
            or user_profile.account_tier.link_to_original == False
        ):
            for item in data:
                item.pop("image", None)

        return Response(data)
