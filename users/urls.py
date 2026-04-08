from django.urls import path
from .views import(
    RegisterView,
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
    LogoutView,
    UserProfileView
)

app_name = 'users'
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CookieTokenObtainPairView.as_view(), name="login"),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name="token_refresh"),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('my_profile/', UserProfileView.as_view(), name="profile")
]