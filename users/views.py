from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import redirect
from django.conf import settings

DEBUG = settings.DEBUG

class HomePageRedirectView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        user_auth_tuple = JWTAuthentication().authenticate(request)
        if user_auth_tuple is None:
            return redirect('accounts:register')
        return redirect('todo:my_tasks')

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "User created successfully.", 
                "username": user.username,
                "email": user.email},
                status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CookieTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = TokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response_data = super().post(request, *args, **kwargs).data

        response = Response({"message" : "Login successful"}, status=status.HTTP_200_OK)
        response.set_cookie(
            key='access_token',
            value=response_data['access'],
            httponly=True,
            samesite='Lax',
            secure=not DEBUG,
            max_age=30*60,
        )

        response.set_cookie(
            key='refresh_token',
            value=response_data['refresh'],
            httponly=True,
            samesite='Lax',
            secure=not DEBUG,
            max_age=7*24*60*60
        )
        return response

class CookieTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({"error" : "Refresh token not provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data={"refresh": refresh_token})
        serializer.is_valid(raise_exception=True)
        new_access = serializer.validated_data['access']

        response = Response({"message": "Access token refreshed"}, status=status.HTTP_200_OK)
        response.set_cookie(
            key='access_token',
            value=new_access,
            httponly=True,
            samesite='Lax',
            secure=not DEBUG,
            max_age=30*60
        )
        return response


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass
        
        response = Response({"message" : "Logout successful"}, status=status.HTTP_200_OK)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

        return response
