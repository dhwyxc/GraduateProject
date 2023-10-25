from rest_framework import serializers
from django.contrib.auth.models import User
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer, PasswordResetSerializer
from rest_framework.validators import ValidationError
from allauth.account.adapter import get_adapter
from django.core.validators import RegexValidator
from rest_framework.validators import UniqueValidator
from .models import UserProfile, PostCheck
from .constants import NEWS_CATEGORY_CHOICES

class PostCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostCheck
        exclude = ['is_deleted','deleted_at']
        read_only_fields = ['status']
        
        
class UserProfileSerializer(serializers.ModelSerializer):
    news_categories_like = serializers.MultipleChoiceField(
        choices = NEWS_CATEGORY_CHOICES)
    
    class Meta:
        model = UserProfile
        fields = [
            "news_categories_like"
        ]
        
        
class UserSerializer(serializers.ModelSerializer):
    news_categories_like = serializers.MultipleChoiceField(
        source='userprofile.news_categories_like',
        choices = NEWS_CATEGORY_CHOICES)
    
    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "news_categories_like",
        ]

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("userprofile", None)
        
        # Update or create UserProfile instance
        if profile_data:
            profile_instance, _ = UserProfile.objects.get_or_create(user=instance)
            field_name, field_value = profile_data.popitem()
            setattr(profile_instance, field_name, field_value)
            profile_instance.save()

        # Update User instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
        

class CustomRegisterSerializer(RegisterSerializer):
    email = serializers.EmailField(
        validators=[
        UniqueValidator(
            queryset = User.objects.all(),
            message = 'This email address is already in use.'
        )]
        )
   
    def save(self, request):
        adapter = get_adapter()
        user = adapter.new_user(request)
        self.cleaned_data = self.get_cleaned_data()
        adapter.save_user(request, user, self)
        return user
    
class CustomPasswordResetSerializer(PasswordResetSerializer):
    email = serializers.EmailField()    
        
    def validate(self, attrs):
        email = attrs['email']

        if not User.objects.filter(email=email).exists():
            raise ValidationError({'email':'This email address is not associated with any account.'})

        return attrs
         

class CustomLoginSerializer(LoginSerializer):
    username = None
    email = serializers.EmailField(required=True)