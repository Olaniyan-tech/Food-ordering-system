from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Profile


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True)
    

    class Meta:
        model = User
        fields = ["username", "email", "phone", "password"]
    
    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value
    
    def validate_phone(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Phone must contain digits only.")
        if len(value) <= 10:
            raise serializers.ValidationError("Phone number too short.")
        if Profile.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Phone number already exists.")
        return value
    
    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def create(self, validated_data):
        phone = validated_data.pop("phone")


        if Profile.objects.filter(phone=phone).exists():
            raise serializers.ValidationError({"phone": "Phone number already exists."})

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )

        Profile.objects.create(user=user, phone=phone)

        return user