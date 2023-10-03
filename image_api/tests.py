from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from .models import (
    ThumbnailSettings,
    AccountTier,
    TierConfiguration,
    UserProfile,
    UploadedImage,
    DynamicImage,
)

from image_api.utils.image_utils import calculate_width

from io import BytesIO
from PIL import Image, UnidentifiedImageError


class ModelsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword", email="test@mail.com"
        )
        self.thumbnail_settings = ThumbnailSettings.objects.create(height=300)
        self.account_tier = AccountTier.objects.create(
            name="Test", link_to_original=True, generate_expiring_links=True
        )
        self.account_tier.thumbnail_sizes.add(self.thumbnail_settings)

        self.user_profile = UserProfile.objects.create(
            user=self.user, account_tier=self.account_tier
        )

        image_file = SimpleUploadedFile(
            "test_image.jpg", b"file_content", content_type="image/jpeg"
        )
        self.uploaded_image = UploadedImage.objects.create(
            user=self.user_profile, image=image_file
        )

        self.dynamic_image = DynamicImage.objects.create(
            image_model=self.uploaded_image, size=200
        )

        self.tier_configuration = TierConfiguration.objects.create(
            tier=self.account_tier, allow_expiring_links=True, expiration_seconds=600
        )

    def test_user_profile_str_method(self):
        self.assertEqual(str(self.user_profile), self.user.username)

    def test_uploaded_image_str_method(self):
        self.assertEqual(str(self.uploaded_image), str(self.uploaded_image.image))

    def test_dynamic_image_str_method(self):
        expected_str = f"200px thumbnail for {self.uploaded_image}"
        self.assertEqual(str(self.dynamic_image), expected_str)


class UserUploadedImageViewSetTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.account_tier_basic = AccountTier.objects.create(
            name="Basic",
            link_to_original=True,
            generate_expiring_links=True,
        )
        self.account_tier_basic.thumbnail_sizes.set(
            [ThumbnailSettings.objects.create(height="200")],
        )

        self.account_tier_enterprise = AccountTier.objects.create(
            name="Enterprise",
            link_to_original=True,
            generate_expiring_links=True,
        )
        self.account_tier_enterprise.thumbnail_sizes.set(
            [
                ThumbnailSettings.objects.create(height="200"),
                ThumbnailSettings.objects.create(height="400"),
            ],
        )
        self.user1 = User.objects.create_user(
            username="user1", password="password1", email="user1@example.com"
        )
        self.user2 = User.objects.create_user(
            username="user2", password="password2", email="user2@example.com"
        )
        self.user1_profile = UserProfile.objects.create(
            user=self.user1, account_tier=self.account_tier_basic
        )
        self.user2_profile = UserProfile.objects.create(
            user=self.user2, account_tier=self.account_tier_enterprise
        )

    def test_users_can_only_access_own_images(self):
        self.client.force_authenticate(user=self.user1)
        with open("image_api/testdata/img_landscape.jpg", "rb") as f:
            image_data = f.read()

        image_file = BytesIO(image_data)
        image_file.name = "test_img_user1.jpeg"

        uploaded_file = SimpleUploadedFile(image_file.name, image_file.read())
        response_user1 = self.client.post(
            "/user-images/",
            data={"image": uploaded_file},
            format="multipart",
        )

        self.assertEqual(response_user1.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(user=self.user2)
        response_user2 = self.client.get(f"/user-images/{response_user1.data['id']}/")
        self.assertEqual(response_user2.status_code, status.HTTP_404_NOT_FOUND)

    def test_for_generated_dynamic_images_based_on_tier(self):
        self.client.force_authenticate(user=self.user2)
        with open("image_api/testdata/img_vertical.jpg", "rb") as f:
            image_data_sq = f.read()

        image_file_vr = BytesIO(image_data_sq)
        image_file_vr.name = "test_img_vertical.jpeg"

        uploaded_file_vr = SimpleUploadedFile(image_file_vr.name, image_file_vr.read())
        response_user2 = self.client.post(
            "/user-images/",
            data={"image": uploaded_file_vr},
            format="multipart",
        )

        self.assertEqual(response_user2.status_code, status.HTTP_201_CREATED)
        self.assertIn("dynamic_images", response_user2.data)

        dynamic_images = response_user2.data["dynamic_images"]

        expected_sizes_in_tier = {200, 400}

        for dynamic_image in dynamic_images:
            size = dynamic_image["size"]
            image_url = dynamic_image["image"]

            self.assertIn(size, expected_sizes_in_tier)
            self.assertTrue(
                image_url.startswith("http://testserver/media/media/dynamic")
            )


class CalculateWidthTestCase(TestCase):
    def setUp(self):
        with open("image_api/testdata/img_landscape.jpg", "rb") as f:
            self.landscape_image_data = f.read()
        with open("image_api/testdata/img_square.jpg", "rb") as f:
            self.square_image_data = f.read()
        with open("image_api/testdata/img_vertical.jpg", "rb") as f:
            self.vertical_image_data = f.read()

        self.landscape_image = Image.open(BytesIO(self.landscape_image_data))
        self.square_image = Image.open(BytesIO(self.square_image_data))
        self.vertical_image = Image.open(BytesIO(self.vertical_image_data))

    def test_calculate_width_for_landscape_image(self):
        target_height = 200
        expected_width = int(
            target_height * (self.landscape_image.width / self.landscape_image.height)
        )
        calculated_width = calculate_width(
            image=self.landscape_image, target_height=target_height
        )
        self.assertEqual(calculated_width, expected_width)

    def test_calculate_width_for_square_image(self):
        target_height = 200
        expected_width = int(
            target_height * (self.square_image.width / self.square_image.height)
        )
        calculated_width = calculate_width(
            image=self.square_image, target_height=target_height
        )
        self.assertEqual(calculated_width, expected_width)

    def test_calculate_width_for_vertical_image(self):
        target_height = 200
        expected_width = int(
            target_height * (self.vertical_image.width / self.vertical_image.height)
        )
        calculated_width = calculate_width(
            image=self.vertical_image, target_height=target_height
        )
        self.assertEqual(calculated_width, expected_width)
