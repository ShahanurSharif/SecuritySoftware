from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ShiftTemplateViewSet, RosterShiftViewSet, AvailabilityViewSet,
    PTORequestViewSet, DropRequestViewSet, NotificationViewSet,
)

router = DefaultRouter()
router.register(r'roster/shift-templates', ShiftTemplateViewSet, basename='shift-templates')
router.register(r'roster/shifts', RosterShiftViewSet, basename='roster-shifts')
router.register(r'roster/availability', AvailabilityViewSet, basename='availability')
router.register(r'roster/pto', PTORequestViewSet, basename='pto-requests')
router.register(r'roster/drop-requests', DropRequestViewSet, basename='drop-requests')
router.register(r'roster/notifications', NotificationViewSet, basename='notifications')

urlpatterns = [
    path('', include(router.urls)),
]
