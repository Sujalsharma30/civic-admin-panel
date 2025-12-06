"""
Context processors to add common data to all templates
"""
from .models import Notification


def admin_context(request):
    """Add admin-related context to all templates"""
    context = {}
    
    if request.user.is_authenticated:
        # Add unread notifications count to all pages
        context['unread_notifications'] = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).count()
    else:
        context['unread_notifications'] = 0
    
    return context


