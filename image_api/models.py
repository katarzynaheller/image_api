from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class ThumbnailSettings(models.Model):
    height = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Thumbnail size"
        verbose_name_plural = "Thumbnail sizes"

    def __str__(self):
        return str(self.height)


class AccountTier(models.Model):
    name = models.CharField(max_length=100)
    thumbnail_sizes = models.ManyToManyField(ThumbnailSettings, blank=True)
    link_to_original = models.BooleanField(default=False)
    generate_expiring_links = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class TierConfiguration(models.Model):
    tier = models.OneToOneField(
        AccountTier, on_delete=models.CASCADE, related_name="configuration"
    )
    allow_expiring_links = models.BooleanField(default=False)
    expiration_seconds = models.PositiveBigIntegerField(
        default=300, validators=[MinValueValidator(300), MaxValueValidator(30000)]
    )


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    account_tier = models.ForeignKey(AccountTier, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.user.username


class UploadedImage(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="media/", blank=True, null=True)
    upload_datetime = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.image)


class DynamicImage(models.Model):
    image_model = models.ForeignKey(
        UploadedImage, related_name="dynamic_images", on_delete=models.CASCADE
    )
    size = models.PositiveIntegerField()
    image = models.ImageField(upload_to="media/dynamic/")

    def __str__(self):
        return f"{self.size}px thumbnail for {self.image_model}"
