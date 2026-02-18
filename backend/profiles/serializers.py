from rest_framework import serializers
from django.contrib.auth.models import User
from media_library.serializers import MediaSerializer
from .models import Profile, ProfileAddress


class ProfileAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileAddress
        fields = ['flat', 'street', 'suburb', 'postal_code', 'state', 'country']


class ProfileSerializer(serializers.ModelSerializer):
    # Flatten user fields
    id = serializers.IntegerField(source='user.id', read_only=True)
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email')
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    last_login = serializers.DateTimeField(source='user.last_login', read_only=True)
    address = ProfileAddressSerializer(required=False, allow_null=True)
    photo = MediaSerializer(read_only=True)
    photo_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Profile
        fields = [
            'id', 'first_name', 'last_name', 'email', 'password',
            'phone', 'birthday', 'photo', 'photo_id', 'address',
            'role', 'group', 'status', 'last_login',
        ]

    def validate_email(self, value):
        """Ensure email is unique across users."""
        user_id = self.instance.user.id if self.instance else None
        if User.objects.filter(email=value).exclude(id=user_id).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def create(self, validated_data):
        user_data = validated_data.pop('user', {})
        password = validated_data.pop('password', None)
        address_data = validated_data.pop('address', None)

        # Create Django User
        user = User.objects.create_user(
            username=user_data.get('email', ''),
            email=user_data.get('email', ''),
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', ''),
            password=password or 'changeme123',
        )

        # Profile is auto-created by signal, fetch it
        profile = user.profile
        for attr, value in validated_data.items():
            setattr(profile, attr, value)

        # Handle address
        if address_data:
            profile.address = ProfileAddress.objects.create(**address_data)

        profile.save()
        return profile

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        password = validated_data.pop('password', None)
        address_data = validated_data.pop('address', None)

        # Update User fields
        user = instance.user
        for attr in ('first_name', 'last_name', 'email'):
            if attr in user_data:
                setattr(user, attr, user_data[attr])
        if 'email' in user_data:
            user.username = user_data['email']
        if password:
            user.set_password(password)
        user.save()

        # Update profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Update address
        if address_data:
            if instance.address:
                for attr, value in address_data.items():
                    setattr(instance.address, attr, value)
                instance.address.save()
            else:
                instance.address = ProfileAddress.objects.create(**address_data)

        instance.save()
        return instance


class RoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=Profile.ROLE_CHOICES)


class ChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=6)
    confirm_password = serializers.CharField(min_length=6)

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return data
