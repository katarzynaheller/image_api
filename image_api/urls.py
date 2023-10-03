from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserUploadedImageViewSet

router = DefaultRouter()
router.register(r"user-images", UserUploadedImageViewSet, basename="user-images")


urlpatterns = [
    path("", include(router.urls)),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
