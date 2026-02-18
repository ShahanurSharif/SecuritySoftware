from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Company
from .serializers import CompanySerializer, CompanyLiteSerializer


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.select_related('address').prefetch_related('phones').all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name', 'email', 'address__street', 'address__suburb', 'address__state', 'address__country', 'phones__number']
    ordering_fields = ['name', 'email', 'address__state', 'created_at']
    ordering = ['name']

    @action(detail=False, methods=['get'], url_path='lite')
    def lite(self, request):
        """Return lightweight company list (id + name) for dropdowns — no pagination."""
        qs = Company.objects.only('id', 'name').order_by('name')
        serializer = CompanyLiteSerializer(qs, many=True)
        return Response(serializer.data)
