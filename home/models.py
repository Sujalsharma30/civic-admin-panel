from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _


class Department(models.Model):
    """Department model for issue assignment"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Issue(models.Model):
    CATEGORY_CHOICES = [
        ('pothole', _('Pothole')),
        ('drainage', _('Drainage')),
        ('streetlight', _('Streetlight')),
        ('waste', _('Waste Management')),
        ('electricity', _('Electricity')),
        ('water', _('Water Supply')),
        ('other', _('Other')),
    ]
    
    PRIORITY_CHOICES = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('urgent', _('Urgent')),
    ]
    
    STATUS_CHOICES = [
        ('reported', _('Reported')),
        ('verified', _('Verified')),
        ('in_progress', _('In Progress')),
        ('resolved', _('Resolved')),
        ('escalated', _('Escalated')),
    ]

    title = models.CharField(_('Title'), max_length=200)
    category = models.CharField(_('Category'), max_length=20, choices=CATEGORY_CHOICES)
    priority = models.CharField(_('Priority'), max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='reported')
    location = models.CharField(_('Location'), max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    description = models.TextField()
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_issues')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='issues')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_issues')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.id} - {self.title}"


class ActivityLog(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return self.action


class Notification(models.Model):
    """Notification model for status updates"""
    NOTIFICATION_TYPES = [
        ('status_change', _('Status Change')),
        ('assignment', _('Assignment')),
        ('comment', _('Comment')),
        ('escalation', _('Escalation')),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('citizen', _('Citizen')),
        ('officer', _('Officer')),
        ('admin', _('Admin')),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(_('Role'), max_length=10, choices=ROLE_CHOICES, default='citizen')
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"


# Signal to create UserProfile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
