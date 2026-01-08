from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import EmailVerification, PasswordReset
from .email_service import EmailService
from django.contrib.auth.hashers import make_password

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def send_verification_email_view(request):
    """Send or resend verification email"""
    email = request.data.get('email', '').strip().lower()
    
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if already verified
    if user.email_verified:
        return Response({'error': 'Email already verified'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get or create verification
    verification, created = EmailVerification.objects.get_or_create(user=user)
    
    # Check if locked due to too many attempts
    if verification.is_locked():
        return Response(
            {'error': 'Too many attempts. Please try again later.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    # Generate new OTP if expired or resending
    if verification.is_expired() or not created:
        verification.otp_code = EmailVerification.generate_otp()
        verification.expires_at = timezone.now() + timezone.timedelta(minutes=15)
        verification.attempts = 0
        verification.save()
    
    # Send email
    try:
        EmailService.send_verification_email(user, verification.otp_code)
        return Response({
            'message': 'Verification email sent successfully',
            'expires_in_minutes': 15
        })
    except Exception as e:
        return Response(
            {'error': f'Failed to send email: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email_view(request):
    """Verify email with OTP"""
    email = request.data.get('email', '').strip().lower()
    otp_code = request.data.get('otp_code', '').strip()
    
    if not email or not otp_code:
        return Response({'error': 'Email and OTP code are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        verification = EmailVerification.objects.get(user=user)
    except (User.DoesNotExist, EmailVerification.DoesNotExist):
        return Response({'error': 'Invalid verification request'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if already verified
    if user.email_verified:
        return Response({'error': 'Email already verified'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if locked
    if verification.is_locked():
        return Response(
            {'error': 'Too many failed attempts. Please request a new code.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    # Check if expired
    if verification.is_expired():
        return Response(
            {'error': 'Verification code has expired. Please request a new one.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify OTP
    if verification.otp_code != otp_code:
        verification.attempts += 1
        verification.save()
        
        remaining_attempts = 5 - verification.attempts
        return Response({
            'error': 'Invalid verification code',
            'remaining_attempts': remaining_attempts
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Success - mark as verified
    user.email_verified = True
    user.save()
    
    verification.is_verified = True
    verification.save()
    
    return Response({
        'message': 'Email verified successfully',
        'user': {
            'id': str(user.id),
            'email': user.email,
            'name': user.name,
            'email_verified': user.email_verified
        }
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset_view(request):
    """Request password reset email"""
    email = request.data.get('email', '').strip().lower()
    
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Don't reveal if user exists - security
        return Response({
            'message': 'If an account with that email exists, a password reset link has been sent.'
        })
    
    # Invalidate old reset tokens
    PasswordReset.objects.filter(user=user, is_used=False).update(is_used=True)
    
    # Create new reset token
    password_reset = PasswordReset.objects.create(user=user)
    
    # Send email
    try:
        EmailService.send_password_reset_email(user, password_reset.token)
        return Response({
            'message': 'If an account with that email exists, a password reset link has been sent.',
            'expires_in_minutes': 15
        })
    except Exception as e:
        return Response(
            {'error': f'Failed to send email: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_view(request):
    """Reset password with token"""
    token = request.data.get('token', '').strip()
    new_password = request.data.get('password', '').strip()
    
    if not token or not new_password:
        return Response({'error': 'Token and new password are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if len(new_password) < 8:
        return Response({'error': 'Password must be at least 8 characters'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        password_reset = PasswordReset.objects.get(token=token, is_used=False)
    except PasswordReset.DoesNotExist:
        return Response({'error': 'Invalid or expired reset token'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if expired
    if password_reset.is_expired():
        return Response({'error': 'Reset token has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Update password
    user = password_reset.user
    user.password = make_password(new_password)
    user.save()
    
    # Mark token as used
    password_reset.is_used = True
    password_reset.save()
    
    return Response({'message': 'Password reset successfully. You can now log in with your new password.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_verification_status_view(request):
    """Check if user's email is verified"""
    user = request.user
    
    return Response({
        'email_verified': user.email_verified,
        'email': user.email
    })