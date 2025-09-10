from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/<str:uidb64>/<str:token>/', views.verify_email, name='verify_email'),
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset-confirm/<str:uidb64>/<str:token>/', views.password_reset_confirm, name='password_reset_confirm'),
]