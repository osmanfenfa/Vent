from django import forms
from .models import Complaint

class NonAnonymousComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['category', 'title', 'description', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter title (eg. Assessment, Exam Pass, Lab. etc)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe your complaint in detail'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].required = True

class AnonymousComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['title', 'description', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter complaint title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe your complaint in detail'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class ComplaintStatusForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['status', 'assigned_to']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department or person assigned'}),
        }