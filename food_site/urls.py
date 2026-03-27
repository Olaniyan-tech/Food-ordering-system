
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from django.contrib.admin.views.decorators import staff_member_required


def api_home(request):
    return JsonResponse({
        "message": "Food Ordering System",
        "status": "running"
    })


urlpatterns = [
    path('', api_home),
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/', include('food.urls')),   

    path('api/schema/', staff_member_required(SpectacularAPIView.as_view()), name='schema'),
]

if settings.DEBUG:
    urlpatterns += [
        path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    ]
    
else:
    urlpatterns += [
        path('api/docs/', staff_member_required(SpectacularSwaggerView.as_view(url_name='schema')), name='swagger-ui'),
        path('api/redoc/', staff_member_required(SpectacularRedocView.as_view(url_name='schema')), name='redoc'),
    ]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)