from django import forms
from django.contrib import admin
from django.forms import inlineformset_factory
from .models import (
    AccountTier,
    TierConfiguration,
    UserProfile,
    UploadedImage,
    ThumbnailSettings,
    DynamicImage,
)


admin.site.register(UserProfile)
admin.site.register(UploadedImage)
admin.site.register(AccountTier)
admin.site.register(TierConfiguration)
admin.site.register(DynamicImage)
admin.site.register(ThumbnailSettings)
