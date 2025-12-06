"""
Management command to create/update admin user
Run: python manage.py create_admin
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from home.models import UserProfile


class Command(BaseCommand):
    help = 'Creates or updates the admin user with username "admin" and password "admin123"'

    def handle(self, *args, **options):
        username = 'admin'
        password = 'admin123'
        email = 'admin@civichub.com'
        
        # Get or create admin user
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True
            }
        )
        
        # Always set password (in case user exists but password is wrong)
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.email = email
        user.save()
        
        # Create or update profile
        profile, profile_created = UserProfile.objects.get_or_create(
            user=user,
            defaults={'role': 'admin', 'is_active': True}
        )
        profile.role = 'admin'
        profile.is_active = True
        profile.save()
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created admin user "{username}" with password "{password}"')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated admin user "{username}" with password "{password}"')
            )


