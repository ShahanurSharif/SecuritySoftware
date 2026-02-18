from rest_framework import serializers
from .models import Address, Company, CompanyPhone


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'flat', 'street', 'suburb', 'postal_code', 'state', 'country']
        extra_kwargs = {
            'id': {'read_only': True},
        }


class CompanyPhoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyPhone
        fields = ['id', 'number', 'label']
        extra_kwargs = {
            'id': {'read_only': True},
        }


class CompanySerializer(serializers.ModelSerializer):
    address = AddressSerializer()
    phones = CompanyPhoneSerializer(many=True, required=False)

    class Meta:
        model = Company
        fields = ['id', 'name', 'email', 'description', 'address', 'phones', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    # ---- nested create ----
    def create(self, validated_data):
        address_data = validated_data.pop('address')
        phones_data = validated_data.pop('phones', [])
        address = Address.objects.create(**address_data)
        company = Company.objects.create(address=address, **validated_data)
        for phone in phones_data:
            CompanyPhone.objects.create(company=company, **phone)
        return company

    # ---- nested update ----
    def update(self, instance, validated_data):
        address_data = validated_data.pop('address', None)
        phones_data = validated_data.pop('phones', None)

        # Update scalar fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update address
        if address_data:
            for attr, value in address_data.items():
                setattr(instance.address, attr, value)
            instance.address.save()

        # Replace phones (simple strategy: delete-all-then-recreate)
        if phones_data is not None:
            instance.phones.all().delete()
            for phone in phones_data:
                CompanyPhone.objects.create(company=instance, **phone)

        return instance


class CompanyLiteSerializer(serializers.ModelSerializer):
    """Lightweight serializer for dropdowns (id + name)."""
    class Meta:
        model = Company
        fields = ['id', 'name']
