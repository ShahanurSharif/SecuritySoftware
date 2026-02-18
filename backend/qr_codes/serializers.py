from rest_framework import serializers
from .models import QRCode, QRCodeSubmission


class QRCodeSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    company_name = serializers.CharField(source='branch.company.name', read_only=True)
    company_id = serializers.IntegerField(source='branch.company.id', read_only=True)

    class Meta:
        model = QRCode
        fields = [
            'id', 'branch', 'branch_name', 'company_id', 'company_name',
            'area_name', 'status', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class QRCodeSubmissionSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    qr_area_name = serializers.CharField(source='qr_code.area_name', read_only=True)
    qr_branch_name = serializers.CharField(source='qr_code.branch.name', read_only=True)

    class Meta:
        model = QRCodeSubmission
        fields = [
            'id', 'qr_code', 'qr_area_name', 'qr_branch_name',
            'user', 'user_name', 'scanned_at',
        ]
        read_only_fields = ['id', 'scanned_at']

    def get_user_name(self, obj):
        return f'{obj.user.first_name} {obj.user.last_name}'.strip() or obj.user.username
