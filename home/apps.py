from django.apps import AppConfig
import threading


class HomeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'home'
    
    def ready(self):
        """Run when Django starts"""
        # Use threading to avoid database access during initialization warning
        def ensure_admin_user():
            try:
                from django.contrib.auth.models import User
                from .models import UserProfile
                
                username = 'admin'
                password = 'admin123'
                
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': 'admin@civichub.com',
                        'is_staff': True,
                        'is_superuser': True,
                        'is_active': True
                    }
                )
                
                # Always ensure password and permissions are correct
                if not user.check_password(password):
                    user.set_password(password)
                user.is_staff = True
                user.is_superuser = True
                user.is_active = True
                user.email = 'admin@civichub.com'
                user.save()
                
                # Create or update profile
                profile, _ = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={'role': 'admin', 'is_active': True}
                )
                profile.role = 'admin'
                profile.is_active = True
                profile.save()
                
            except Exception:
                # Ignore errors during startup (migrations might not be run yet)
                pass
        
        # Run in a separate thread to avoid initialization warnings
        threading.Thread(target=ensure_admin_user, daemon=True).start()