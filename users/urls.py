from django.contrib import admin
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from django.conf.urls.static import static
from rest_framework import permissions
from django.conf import settings
from dj_rest_auth.registration.views import RegisterView
from dj_rest_auth.views import LogoutView, PasswordChangeView, UserDetailsView
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from . import views
from rest_framework.routers import DefaultRouter

app_name = "gp"
router = DefaultRouter()
router.register(r"post", views.PostCheckViews, basename="post")
router.register(r"post-community", views.PostCommunityViews, basename="post_community")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", views.CustomLoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="rest_logout"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "auth/password-change/",
        PasswordChangeView.as_view(),
        name="rest_password_change",
    ),
    path("auth/me/", UserDetailsView.as_view(), name="rest_user_details"),
    path("image-to-text/", views.DetectTextView.as_view(), name="image_to_text"),
    path("summary/", views.SummaryText.as_view(), name="summary"),
    path("recommend/", views.RecommendView.as_view(), name="recommend"),
    path("predict/", views.PredictView.as_view(), name="predict"),
    path("text-to-speech/", views.TextToSpeech.as_view(), name="text_to_speech"),
    path("", include(router.urls)),
]
