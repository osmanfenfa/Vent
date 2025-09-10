from django.db import models
from django.contrib.auth.models import User

class Complaint(models.Model):
    TYPE_CHOICES = (
        ('anonymous', 'Anonymous'),
        ('non_anonymous', 'Non-Anonymous'),
    )
    CATEGORY_CHOICES = (
        ('exam', 'Exam'),
        ('fees', 'Fees'),
        ('facilities', 'Facilities'),
        ('lecturer', 'Lecturer'),
        ('other', 'Other'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )

    student = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    attachment = models.FileField(upload_to="complaints/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    assigned_to = models.CharField(max_length=100, null=True, blank=True, help_text="Department or person assigned")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type} - {self.title}"