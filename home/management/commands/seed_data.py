from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from home.models import UserProfile, Issue, Department, ActivityLog, Notification
import random
from datetime import timedelta
from django.utils import timezone

class Command(BaseCommand):
    help = 'Seeds the database with Indore-specific civic data'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Cleaning up old data...'))
        # Delete dependent models first to avoid cascade issues
        Notification.objects.all().delete()
        ActivityLog.objects.all().delete()
        Issue.objects.all().delete()
        
        # UserProfile is deleted via cascade when User is deleted, 
        # but we explicit delete to be safe if signal logic varies
        UserProfile.objects.all().delete()
        
        # Keep admin, delete everyone else
        User.objects.exclude(username='admin').delete()
        Department.objects.all().delete()

        # ---------------------------------------------------------
        # 1. Create Departments (Indore Municipal Corp style)
        # ---------------------------------------------------------
        depts_data = [
            {'name': 'Roads & Transport', 'desc': 'Road maintenance and traffic infrastructure'},
            {'name': 'Narmada Water Supply', 'desc': 'Water pipeline and supply management'},
            {'name': 'Waste Management (IMC)', 'desc': 'Door-to-door collection and disposal'},
            {'name': 'Electricity (MPPKVVCL)', 'desc': 'Street lights and power lines'},
            {'name': 'Health & Sanitation', 'desc': 'Public health and sanitation'},
        ]
        
        dept_objs = []
        for d in depts_data:
            dept, _ = Department.objects.get_or_create(
                name=d['name'],
                defaults={'description': d['desc'], 'email': f"{d['name'].split()[0].lower()}@imc.gov.in"}
            )
            dept_objs.append(dept)
        
        self.stdout.write(f'✓ Created {len(dept_objs)} Departments')

        # ---------------------------------------------------------
        # 2. Create Users (Citizens & Officers)
        # ---------------------------------------------------------
        first_names = ['Aarav', 'Vihaan', 'Aditya', 'Sai', 'Arjun', 'Reyansh', 'Vivaan', 'Rahul', 'Amit', 'Sujal', 'Priya', 'Anjali', 'Sneha', 'Diya', 'Isha', 'Kavya', 'Neha', 'Riya']
        last_names = ['Sharma', 'Verma', 'Gupta', 'Patel', 'Singh', 'Jain', 'Agrawal', 'Joshi', 'Trivedi', 'Dubey', 'Chouhan']
        
        indore_areas = [
            'Vijay Nagar', 'Bhawarkua', 'Palasia', 'Rajwada', 'Sarafa', 
            'LIG Colony', 'Bengali Square', 'Sudama Nagar', 'Annapurna Road', 
            'Khajrana', 'Geeta Bhawan', 'Navlakha', 'Sapna Sangeeta'
        ]

        users = []
        # Fetch admin to use in logs later
        admin_user = User.objects.filter(username='admin').first()

        for i in range(30):
            fname = random.choice(first_names)
            lname = random.choice(last_names)
            username = f"{fname.lower()}{random.randint(10,99)}"
            email = f"{username}@example.com"
            
            # Create User (Signal automatically creates UserProfile)
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': fname,
                    'last_name': lname,
                    'is_active': True
                }
            )
            
            if created:
                user.set_password('password123')
                user.save()

            # FIX: Get the existing profile instead of creating a new one
            if hasattr(user, 'profile'):
                profile = user.profile
                profile.role = random.choice(['citizen', 'citizen', 'citizen', 'officer']) # 25% Officers
                profile.phone = f"+91 {random.randint(6000000000, 9999999999)}"
                profile.address = f"{random.randint(1, 100)}, {random.choice(indore_areas)}, Indore, MP"
                
                # Make officers staff so they can theoretically access admin if needed
                if profile.role == 'officer':
                    user.is_staff = True
                    user.save()
                    
                profile.save()
            
            users.append(user)

        self.stdout.write(f'✓ Created {len(users)} Users with Indian profiles')

        # ---------------------------------------------------------
        # 3. Create Issues
        # ---------------------------------------------------------
        issues_titles = [
            'Pothole near square', 'Street light not working', 'Garbage not collected', 
            'Water leakage in main line', 'Illegal hoarding', 'Stray cattle causing traffic',
            'Drainage blocked', 'Manhole cover missing', 'Construction debris on road',
            'Low water pressure', 'Broken signal light'
        ]
        
        # Indore approx lat/long boundaries
        base_lat = 22.7196
        base_long = 75.8577

        all_issues = []

        for i in range(50):
            status = random.choice(['reported', 'verified', 'in_progress', 'resolved'])
            user = random.choice(users)
            
            # Random coordinate near Indore (~5km radius)
            lat = base_lat + random.uniform(-0.04, 0.04)
            lng = base_long + random.uniform(-0.04, 0.04)
            
            # Determine priority based on title keywords
            title = random.choice(issues_titles)
            priority = 'medium'
            if 'leakage' in title or 'Manhole' in title:
                priority = 'urgent'
            elif 'Street light' in title:
                priority = 'high'

            issue = Issue.objects.create(
                title=title,
                category=random.choice(['pothole', 'waste', 'electricity', 'water', 'other']),
                priority=priority,
                status=status,
                location=f"{random.choice(indore_areas)}, Indore",
                latitude=lat,
                longitude=lng,
                description="This issue was reported via the citizen mobile app. Needs immediate attention.",
                created_by=user,
                department=random.choice(dept_objs),
                assigned_to=random.choice([u for u in users if u.profile.role == 'officer'] + [None])
            )
            
            # Backdate
            days_ago = random.randint(0, 30)
            issue.created_at = timezone.now() - timedelta(days=days_ago)
            issue.save()
            all_issues.append(issue)

        self.stdout.write(f'✓ Created {len(all_issues)} Issues')

        # ---------------------------------------------------------
        # 4. Activity Logs
        # ---------------------------------------------------------
        log_actions = [
            'Issue Verified', 'Assigned to Inspector', 'Work Started', 
            'Material Requested', 'Inspection Failed', 'Completed successfully'
        ]

        for issue in all_issues:
            # Always have a "Reported" log
            ActivityLog.objects.create(
                issue=issue,
                action="Issue Reported",
                user=issue.created_by,
                timestamp=issue.created_at
            )

            # Random additional logs
            if issue.status != 'reported':
                ActivityLog.objects.create(
                    issue=issue,
                    action=random.choice(log_actions),
                    user=admin_user if admin_user else issue.created_by,
                    timestamp=issue.created_at + timedelta(hours=random.randint(2, 48))
                )

        self.stdout.write('✓ Created Activity Logs')

        # ---------------------------------------------------------
        # 5. Notifications
        # ---------------------------------------------------------
        for user in users[:10]: # Create notifications for first 10 users
            for _ in range(random.randint(1, 4)):
                related_issue = random.choice(all_issues)
                Notification.objects.create(
                    user=user,
                    issue=related_issue,
                    notification_type=random.choice(['status_change', 'assignment']),
                    title=f"Update on Issue #{related_issue.id}",
                    message=f"The status of '{related_issue.title}' has been updated.",
                    is_read=random.choice([True, False])
                )

        self.stdout.write('✓ Created Notifications')
        self.stdout.write(self.style.SUCCESS('\nSUCCESS: Indore Database Seeded!'))
        self.stdout.write(self.style.SUCCESS('Login with: admin / admin123'))