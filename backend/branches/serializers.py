from rest_framework import serializers
from companies.models import Address
from companies.serializers import AddressSerializer
from .models import Branch, BranchStaff


class BranchStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = BranchStaff
        fields = ['id', 'name', 'designation', 'phone', 'email']
        extra_kwargs = {'id': {'read_only': True}}


class BranchSerializer(serializers.ModelSerializer):
    address = AddressSerializer()
    staff = BranchStaffSerializer(many=True, required=False)
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = Branch
        fields = [
            'id', 'company', 'company_name', 'name', 'address',
            'front_desk_number', 'store_number', 'staff',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    # ---- nested create ----
    def create(self, validated_data):
        address_data = validated_data.pop('address')
        staff_data = validated_data.pop('staff', [])
        address = Address.objects.create(**address_data)
        branch = Branch.objects.create(address=address, **validated_data)
        for s in staff_data:
            BranchStaff.objects.create(branch=branch, **s)
        return branch

    # ---- nested update ----
    def update(self, instance, validated_data):
        address_data = validated_data.pop('address', None)
        staff_data = validated_data.pop('staff', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if address_data:
            for attr, value in address_data.items():
                setattr(instance.address, attr, value)
            instance.address.save()

        if staff_data is not None:
            instance.staff.all().delete()
            for s in staff_data:
                BranchStaff.objects.create(branch=instance, **s)

        return instance


class BranchLiteSerializer(serializers.ModelSerializer):
    """Lightweight serializer for dropdowns (id + name + company)."""
    company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = Branch
        fields = ['id', 'name', 'company', 'company_name']
