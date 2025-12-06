from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),
    
    # Dashboard
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Reports (Issues)
    path('reports/', views.admin_reports, name='admin_reports'),
    path('reports/<int:report_id>/', views.admin_report_detail, name='admin_report_detail'),
    path('reports/export-csv/', views.export_reports_csv, name='export_reports_csv'),
    
    # Users
    path('users/', views.admin_users, name='admin_users'),
    path('users/<int:user_id>/toggle-active/', views.admin_user_toggle_active, name='admin_user_toggle_active'),
    path('users/export-csv/', views.export_users_csv, name='export_users_csv'),
    
    # Maps
    path('maps/', views.admin_maps, name='admin_maps'),
    
    # Profile
    path('profile/', views.admin_profile, name='admin_profile'),
    
    # Root redirect
    path('', views.root_redirect, name='root'),
]
