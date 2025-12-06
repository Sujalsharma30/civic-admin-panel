"""
Complete Admin Dashboard Views
Clean URLs without /admin/ prefix
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Count
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta, datetime
import json
import csv

from .models import Issue, ActivityLog, UserProfile, Department, Notification


# ==================== AUTHENTICATION ====================

def admin_login(request):
    """Admin login page - redirects to /dashboard/"""
    if request.user.is_authenticated:
        return redirect('admin_dashboard')
    
    error_message = None
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        # Hardcoded admin credentials
        if username == 'admin' and password == 'admin123':
            try:
                user = User.objects.get(username='admin')
            except User.DoesNotExist:
                user = User.objects.create_user(
                    username='admin',
                    email='admin@civichub.com',
                    password='admin123',
                    is_staff=True,
                    is_superuser=True,
                    is_active=True
                )
            else:
                if not user.check_password('admin123'):
                    user.set_password('admin123')
                user.is_staff = True
                user.is_superuser = True
                user.is_active = True
                user.save()
            
            # Create/update profile
            profile, _ = UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': 'admin', 'is_active': True}
            )
            profile.role = 'admin'
            profile.is_active = True
            profile.save()
            
            # Authenticate and login
            user = authenticate(request, username='admin', password='admin123')
            if user:
                login(request, user)
                messages.success(request, 'Welcome to Admin Dashboard!')
                return redirect('admin_dashboard')  # Redirects to /dashboard/
        
        # Try normal authentication
        user = authenticate(request, username=username, password=password)
        if user and (user.is_staff or user.is_superuser):
            login(request, user)
            messages.success(request, f'Welcome, {user.username}!')
            return redirect('admin_dashboard')
        else:
            error_message = 'Invalid credentials. Please try again.'
    
    return render(request, 'adminpanel/login.html', {'error_message': error_message})


@login_required
def admin_logout(request):
    """Admin logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('admin_login')


def root_redirect(request):
    """Root URL redirect"""
    if request.user.is_authenticated:
        return redirect('admin_dashboard')
    return redirect('admin_login')


# ==================== DASHBOARD ====================

@login_required
def admin_dashboard(request):
    """Main dashboard with analytics"""
    # Date range filtering
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    # Base queryset
    issues = Issue.objects.all()
    
    # Apply date filters
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            issues = issues.filter(created_at__date__gte=start_date_obj)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            issues = issues.filter(created_at__date__lte=end_date_obj)
        except ValueError:
            pass
    
    # Calculate stats
    total_reports = issues.count()
    total_users = User.objects.count()
    pending_reports = issues.filter(status='reported').count()
    resolved_reports = issues.filter(status='resolved').count()
    
    # Chart data - Reports by status
    status_data = list(issues.values('status').annotate(count=Count('id')))
    status_labels = [item['status'].replace('_', ' ').title() for item in status_data]
    status_counts = [item['count'] for item in status_data]
    
    # Chart data - Reports by category
    category_data = list(issues.values('category').annotate(count=Count('id')))
    category_labels = [item['category'].replace('_', ' ').title() for item in category_data]
    category_counts = [item['count'] for item in category_data]
    
    # Recent reports
    recent_reports = issues.select_related('assigned_to', 'department').order_by('-created_at')[:10]
    
    # Unread notifications
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
    
    context = {
        'total_reports': total_reports,
        'total_users': total_users,
        'pending_reports': pending_reports,
        'resolved_reports': resolved_reports,
        'recent_reports': recent_reports,
        'unread_notifications': unread_notifications,
        'status_labels': status_labels,  # Pass as list for json_script filter
        'status_counts': status_counts,  # Pass as list for json_script filter
        'category_labels': category_labels,  # Pass as list for json_script filter
        'category_counts': category_counts,  # Pass as list for json_script filter
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'adminpanel/dashboard.html', context)


# ==================== REPORTS (Issues) ====================

@login_required
def admin_reports(request):
    """Reports list page"""
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    page_num = request.GET.get('page', 1)
    
    reports = Issue.objects.select_related('assigned_to', 'department').all()
    
    if search:
        reports = reports.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(location__icontains=search)
        )
    
    if status_filter:
        reports = reports.filter(status=status_filter)
    if category_filter:
        reports = reports.filter(category=category_filter)
    
    # Date range filtering
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            reports = reports.filter(created_at__date__gte=start_date_obj)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            reports = reports.filter(created_at__date__lte=end_date_obj)
        except ValueError:
            pass
    
    reports = reports.order_by('-created_at')
    
    paginator = Paginator(reports, 20)
    page = paginator.get_page(page_num)
    
    context = {
        'reports': page,
        'search': search,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'adminpanel/reports.html', context)


@login_required
def admin_report_detail(request, report_id):
    """Report detail page"""
    report = get_object_or_404(Issue, id=report_id)
    
    if request.method == 'POST':
        old_status = report.status
        old_priority = report.priority
        old_assigned_to = report.assigned_to
        old_department = report.department
        
        # Update report
        new_status = request.POST.get('status', report.status)
        new_priority = request.POST.get('priority', report.priority)
        assigned_to_id = request.POST.get('assigned_to', '')
        department_id = request.POST.get('department', '')
        
        report.status = new_status
        report.priority = new_priority
        
        if assigned_to_id:
            try:
                report.assigned_to = User.objects.get(id=assigned_to_id)
            except User.DoesNotExist:
                pass
        else:
            report.assigned_to = None
        
        if department_id:
            try:
                report.department = Department.objects.get(id=department_id)
            except Department.DoesNotExist:
                pass
        else:
            report.department = None
        
        report.save()
        
        # Log activities for changes
        if old_status != new_status:
            ActivityLog.objects.create(
                issue=report,
                action=f"Status changed from {dict(Issue.STATUS_CHOICES).get(old_status, old_status)} to {report.get_status_display()}",
                user=request.user
            )
        
        if old_priority != new_priority:
            ActivityLog.objects.create(
                issue=report,
                action=f"Priority changed from {dict(Issue.PRIORITY_CHOICES).get(old_priority, old_priority)} to {report.get_priority_display()}",
                user=request.user
            )
        
        if old_assigned_to != report.assigned_to:
            if report.assigned_to:
                ActivityLog.objects.create(
                    issue=report,
                    action=f"Assigned to {report.assigned_to.get_full_name() or report.assigned_to.username}",
                    user=request.user
                )
            else:
                ActivityLog.objects.create(
                    issue=report,
                    action="Assignment removed",
                    user=request.user
                )
        
        if old_department != report.department:
            if report.department:
                ActivityLog.objects.create(
                    issue=report,
                    action=f"Assigned to {report.department.name} department",
                    user=request.user
                )
            else:
                ActivityLog.objects.create(
                    issue=report,
                    action="Department assignment removed",
                    user=request.user
                )
        
        messages.success(request, 'Report updated successfully!')
        return redirect('admin_report_detail', report_id=report_id)
    
    activities = report.activities.all()[:20]
    users = User.objects.filter(is_active=True).order_by('username')
    departments = Department.objects.filter(is_active=True).order_by('name')
    
    context = {
        'report': report,
        'activities': activities,
        'users': users,
        'departments': departments,
    }
    
    return render(request, 'adminpanel/report_detail.html', context)


# ==================== USERS ====================

@login_required
def admin_users(request):
    """Users list page"""
    search = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    page_num = request.GET.get('page', 1)
    
    users = User.objects.select_related('profile').all()
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    if role_filter:
        users = users.filter(profile__role=role_filter)
    
    users = users.order_by('-date_joined')
    
    paginator = Paginator(users, 20)
    page = paginator.get_page(page_num)
    
    context = {
        'users': page,
        'search': search,
        'role_filter': role_filter,
    }
    
    return render(request, 'adminpanel/users.html', context)


@login_required
def export_reports_csv(request):
    """Export reports to CSV"""
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    reports = Issue.objects.select_related('assigned_to', 'department', 'created_by').all()
    
    if search:
        reports = reports.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(location__icontains=search)
        )
    
    if status_filter:
        reports = reports.filter(status=status_filter)
    if category_filter:
        reports = reports.filter(category=category_filter)
    
    # Date range filtering
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            reports = reports.filter(created_at__date__gte=start_date_obj)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            reports = reports.filter(created_at__date__lte=end_date_obj)
        except ValueError:
            pass
    
    reports = reports.order_by('-created_at')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="reports_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        _('ID'), _('Title'), _('Category'), _('Priority'), _('Status'),
        _('Location'), _('Assigned To'), _('Department'), _('Created By'),
        _('Created At'), _('Updated At')
    ])
    
    for report in reports:
        writer.writerow([
            report.id,
            report.title,
            report.get_category_display(),
            report.get_priority_display(),
            report.get_status_display(),
            report.location,
            report.assigned_to.get_full_name() if report.assigned_to else '',
            report.department.name if report.department else '',
            report.created_by.get_full_name() if report.created_by else '',
            report.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            report.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])
    
    return response


@login_required
def export_users_csv(request):
    """Export users to CSV"""
    search = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    
    users = User.objects.select_related('profile').all()
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    if role_filter:
        users = users.filter(profile__role=role_filter)
    
    users = users.order_by('-date_joined')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        _('ID'), _('Username'), _('Email'), _('First Name'), _('Last Name'),
        _('Role'), _('Phone'), _('Address'), _('Is Active'), _('Date Joined')
    ])
    
    for user in users:
        profile = getattr(user, 'profile', None)
        writer.writerow([
            user.id,
            user.username,
            user.email,
            user.first_name,
            user.last_name,
            profile.get_role_display() if profile else '',
            profile.phone if profile else '',
            profile.address if profile else '',
            _('Yes') if user.is_active else _('No'),
            user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
        ])
    
    return response


@login_required
@require_POST
def admin_user_toggle_active(request, user_id):
    """Toggle user active status"""
    user = get_object_or_404(User, id=user_id)
    
    # Prevent deactivating yourself
    if user == request.user:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('admin_users')
    
    user.is_active = not user.is_active
    user.save()
    
    # Update profile
    if hasattr(user, 'profile'):
        user.profile.is_active = user.is_active
        user.profile.save()
    
    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'User {user.username} has been {status}.')
    
    return redirect('admin_users')


# ==================== MAPS ====================

@login_required
def admin_maps(request):
    """Map view for issue locations"""
    # Get all issues with coordinates
    issues = Issue.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    
    # Filter by status if provided
    status_filter = request.GET.get('status', '')
    if status_filter:
        issues = issues.filter(status=status_filter)
    
    # Prepare data for map markers
    issues_data = []
    for issue in issues:
        issues_data.append({
            'id': issue.id,
            'title': issue.title,
            'status': issue.status,
            'category': issue.category,
            'priority': issue.priority,
            'location': issue.location,
            'latitude': float(issue.latitude),
            'longitude': float(issue.longitude),
            'url': f"/reports/{issue.id}/",
        })
    
    context = {
        'issues': json.dumps(issues_data),  # JSON string for template
        'issues_count': len(issues_data),
        'status_filter': status_filter,
    }
    
    return render(request, 'adminpanel/maps.html', context)


# ==================== PROFILE ====================

@login_required
def admin_profile(request):
    """Admin profile page with enhanced stats"""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            request.user.email = request.POST.get('email', request.user.email)
            request.user.first_name = request.POST.get('first_name', request.user.first_name)
            request.user.last_name = request.POST.get('last_name', request.user.last_name)
            request.user.save()
            
            profile.phone = request.POST.get('phone', profile.phone)
            profile.address = request.POST.get('address', profile.address)
            profile.save()
            
            messages.success(request, 'Profile updated successfully!')
        
        elif action == 'change_password':
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully!')
            else:
                for error in form.errors.values():
                    messages.error(request, error)
    
    password_form = PasswordChangeForm(request.user)
    
    # --- Statistics for Profile Header ---
    issues_reported = Issue.objects.filter(created_by=request.user).count()
    # Handle potentially None date_joined (though it should be set)
    if request.user.date_joined:
        days_joined = (timezone.now() - request.user.date_joined).days
    else:
        days_joined = 0
    
    context = {
        'profile': profile,
        'password_form': password_form,
        'issues_reported': issues_reported,
        'days_joined': days_joined,
    }
    
    return render(request, 'adminpanel/profile.html', context)