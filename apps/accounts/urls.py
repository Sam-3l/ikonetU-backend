from django.urls import path
from . import views, email_views

urlpatterns = [
    # auth routes
    path('register', views.register_view, name='register'),
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('me', views.me_view, name='me'),
    
    # Email verification routes
    path('send-verification-email', email_views.send_verification_email_view, name='send-verification-email'),
    path('verify-email', email_views.verify_email_view, name='verify-email'),
    path('check-verification', email_views.check_verification_status_view, name='check-verification'),
    
    # Password reset routes
    path('request-password-reset', email_views.request_password_reset_view, name='request-password-reset'),
    path('reset-password', email_views.reset_password_view, name='reset-password'),
]