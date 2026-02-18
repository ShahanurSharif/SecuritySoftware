from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QRCodeViewSet, QRCodeSubmissionViewSet

router = DefaultRouter()
router.register('qrcodes', QRCodeViewSet, basename='qrcode')
router.register('qrcode-submissions', QRCodeSubmissionViewSet, basename='qrcode-submission')

urlpatterns = [
    path('', include(router.urls)),
]
