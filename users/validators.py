from rest_framework import serializers
import phonenumbers

def validate_phone_format(value):
    try:
        phone = phonenumbers.parse(value)
        if not phonenumbers.is_valid_number(phone):
            raise serializers.ValidationError(
                "Enter a valid phone number with country code e.g +2349039624784"
            )
    
    except phonenumbers.NumberParseException:
        raise serializers.ValidationError(
            "Enter a valid phone number with country code e.g. +2348012345678"
        )