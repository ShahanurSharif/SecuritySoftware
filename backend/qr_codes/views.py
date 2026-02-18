from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import QRCode, QRCodeSubmission
from .serializers import QRCodeSerializer, QRCodeSubmissionSerializer


class QRCodeViewSet(viewsets.ModelViewSet):
    queryset = QRCode.objects.select_related('branch', 'branch__company').all()
    serializer_class = QRCodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['area_name', 'branch__name', 'branch__company__name']
    ordering_fields = ['area_name', 'branch__name', 'branch__company__name', 'status', 'created_at']
    ordering = ['branch__company__name', 'branch__name', 'area_name']
    filterset_fields = ['branch', 'status']

    @action(detail=True, methods=['post'], url_path='submit')
    def submit_scan(self, request, pk=None):
        """Record a QR code scan for the current user."""
        qr_code = self.get_object()
        submission = QRCodeSubmission.objects.create(
            qr_code=qr_code,
            user=request.user,
        )
        return Response(QRCodeSubmissionSerializer(submission).data, status=201)


class QRCodeSubmissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = QRCodeSubmission.objects.select_related(
        'qr_code', 'qr_code__branch', 'qr_code__branch__company', 'user'
    ).all()
    serializer_class = QRCodeSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['qr_code__area_name', 'qr_code__branch__name', 'user__first_name', 'user__last_name']
    ordering_fields = ['scanned_at', 'qr_code__area_name']
    ordering = ['-scanned_at']
    filterset_fields = ['qr_code', 'user']
