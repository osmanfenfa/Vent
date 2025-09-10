from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Profile
from collections import Counter


class Command(BaseCommand):
    help = 'Clean up duplicate users with the same email addresses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Find all users with emails
        users_with_emails = User.objects.exclude(email='').exclude(email__isnull=True)
        emails = [user.email for user in users_with_emails]
        
        # Find duplicate emails
        email_counts = Counter(emails)
        duplicate_emails = [email for email, count in email_counts.items() if count > 1]
        
        if not duplicate_emails:
            self.stdout.write(
                self.style.SUCCESS('No duplicate email addresses found.')
            )
            return
        
        self.stdout.write(
            self.style.WARNING(f'Found {len(duplicate_emails)} duplicate email addresses:')
        )
        
        for email in duplicate_emails:
            self.stdout.write(f'  - {email}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nDRY RUN - No changes will be made')
            )
            return
        
        # Clean up duplicates
        cleaned_count = 0
        for email in duplicate_emails:
            users = User.objects.filter(email=email).order_by('-date_joined')
            
            # Keep the most recent user, deactivate the others
            keep_user = users.first()
            users_to_deactivate = users[1:]
            
            self.stdout.write(f'\nEmail: {email}')
            self.stdout.write(f'  Keeping: {keep_user.username} (ID: {keep_user.id}, Created: {keep_user.date_joined})')
            
            for user in users_to_deactivate:
                self.stdout.write(f'  Deactivating: {user.username} (ID: {user.id}, Created: {user.date_joined})')
                
                # Deactivate the user instead of deleting to preserve data integrity
                user.is_active = False
                user.save()
                cleaned_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'\nCleaned up {cleaned_count} duplicate users.')
        )
