from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Branch
from .serializers import BranchSerializer, BranchLiteSerializer


class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.select_related('company', 'address').prefetch_related('staff').all()
    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['company']
    search_fields = ['name', 'company__name', 'front_desk_number', 'store_number', 'address__street', 'address__suburb', 'address__state', 'address__country']
    ordering_fields = ['name', 'company__name', 'address__state', 'front_desk_number', 'store_number', 'created_at']
    ordering = ['company__name', 'name']

    @action(detail=False, methods=['get'], url_path='lite')
    def lite(self, request):
        """Lightweight branch list for dropdowns, optionally filtered by ?company=ID — no pagination."""
        qs = Branch.objects.select_related('company').only('id', 'name', 'company__id', 'company__name').order_by('name')
        company_id = request.query_params.get('company')
        if company_id:
            qs = qs.filter(company_id=company_id)
        serializer = BranchLiteSerializer(qs, many=True)
        return Response(serializer.data)
