from django.contrib import admin
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from django.conf.urls.static import static
from rest_framework import permissions
from django.conf import settings
from users.views import NewsListView

schema_view = get_schema_view(
    openapi.Info(
        title='API NEWSAPP',
        default_version='v1',
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
urlpatterns = [
    path('api/v1/', include("users.urls")),
    path('api/v1/docs/', 
    schema_view.with_ui('swagger', 
    cache_timeout=0
    ), 
    name='schema-swagger-ui'),
    path('public/demo/',NewsListView.as_view(), name='demo'),
    path('admin/', admin.site.urls),
]
