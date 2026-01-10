from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


class EmailService:
    """Service for sending emails via Brevo"""
    
    @staticmethod
    def send_verification_email(user, otp_code):
        """Send OTP verification email"""
        subject = 'Verify Your ikonetU Account'
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }}
                .otp-box {{ background: white; border: 2px solid #667eea; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0; }}
                .otp-code {{ font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 8px; }}
                .footer {{ text-align: center; color: #6b7280; font-size: 12px; margin-top: 20px; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to ikonetU!</h1>
                </div>
                <div class="content">
                    <h2>Hi {user.name},</h2>
                    <p>Thank you for signing up! Please verify your email address to get started.</p>
                    
                    <div class="otp-box">
                        <p style="margin: 0; color: #6b7280;">Your verification code is:</p>
                        <div class="otp-code">{otp_code}</div>
                        <p style="margin: 10px 0 0 0; color: #6b7280; font-size: 14px;">This code expires in 15 minutes</p>
                    </div>
                    
                    <p>Enter this code in the app to verify your account and start connecting with founders and investors!</p>
                    
                    <p style="color: #6b7280; font-size: 14px;">If you didn't create this account, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© 2026 ikonetU. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_message = f"""
        Welcome to ikonetU!
        
        Hi {user.name},
        
        Thank you for signing up! Please verify your email address to get started.
        
        Your verification code is: {otp_code}
        
        This code expires in 15 minutes.
        
        Enter this code in the app to verify your account.
        
        If you didn't create this account, please ignore this email.
        
        © 2026 ikonetU. All rights reserved.
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
    
    @staticmethod
    def send_password_reset_email(user, reset_token):
        """Send password reset email"""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        subject = 'Reset Your ikonetU Password'
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ text-align: center; color: #6b7280; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <h2>Hi {user.name},</h2>
                    <p>We received a request to reset your password for your ikonetU account.</p>
                    
                    <p>Click the button below to reset your password:</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </div>
                    
                    <p style="color: #6b7280; font-size: 14px;">Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #667eea; font-size: 12px;">{reset_url}</p>
                    
                    <p style="margin-top: 20px; color: #6b7280; font-size: 14px;">This link expires in 15 minutes.</p>
                    
                    <p style="color: #ef4444; font-size: 14px;">If you didn't request this password reset, please ignore this email or contact support if you're concerned.</p>
                </div>
                <div class="footer">
                    <p>© 2026 ikonetU. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_message = f"""
        Password Reset Request
        
        Hi {user.name},
        
        We received a request to reset your password for your ikonetU account.
        
        Click this link to reset your password:
        {reset_url}
        
        This link expires in 15 minutes.
        
        If you didn't request this password reset, please ignore this email.
        
        © 2026 ikonetU. All rights reserved.
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )