from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Complaint
from .forms import NonAnonymousComplaintForm, AnonymousComplaintForm, ComplaintStatusForm
from accounts.models import Profile

def home(request):
    """Home page view"""
    return render(request, 'home.html')

@login_required
def student_dashboard(request):
    try:
        profile = request.user.profile
        if profile.is_admin():
            return redirect('admin_dashboard')
    except Profile.DoesNotExist:
        pass
    
    user_complaints = Complaint.objects.filter(
        student=request.user, 
        type='non_anonymous'
    ).order_by('-created_at')[:5]
    
    context = {
        'user_complaints': user_complaints,
        'total_complaints': user_complaints.count(),
    }
    return render(request, 'complaints/student_dashboard.html', context)

@login_required
def submit_non_anonymous_complaint(request):
    try:
        profile = request.user.profile
        if profile.is_admin():
            return redirect('admin_dashboard')
    except Profile.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = NonAnonymousComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.student = request.user
            complaint.type = 'non_anonymous'
            complaint.save()
            messages.success(request, 'Your complaint has been submitted successfully!')
            return redirect('student_dashboard')
    else:
        form = NonAnonymousComplaintForm()
    
    return render(request, 'complaints/submit_non_anonymous.html', {'form': form})

@login_required
def submit_anonymous_complaint(request):
    try:
        profile = request.user.profile
        if profile.is_admin():
            return redirect('admin_dashboard')
    except Profile.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = AnonymousComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.student = None  # Anonymous complaint
            complaint.type = 'anonymous'
            complaint.category = 'other'
            complaint.save()
            messages.success(request, 'Your anonymous complaint has been submitted successfully!')
            return redirect('student_dashboard')
    else:
        form = AnonymousComplaintForm()
    
    return render(request, 'complaints/submit_anonymous.html', {'form': form})

@login_required
def my_complaints(request):
    try:
        profile = request.user.profile
        if profile.is_admin():
            return redirect('admin_dashboard')
    except Profile.DoesNotExist:
        pass
    
    complaints = Complaint.objects.filter(
        student=request.user, 
        type='non_anonymous'
    ).order_by('-created_at')
    
    paginator = Paginator(complaints, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'complaints/my_complaints.html', {'page_obj': page_obj})

@login_required
def admin_dashboard(request):
    try:
        profile = request.user.profile
        if not profile.is_admin():
            return redirect('student_dashboard')
    except Profile.DoesNotExist:
        return redirect('student_dashboard')
    
    
    complaint_type = request.GET.get('type', '')
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    assigned_to = request.GET.get('assigned_to', '')
    
    complaints = Complaint.objects.all()
    
    if complaint_type:
        complaints = complaints.filter(type=complaint_type)
    if category:
        complaints = complaints.filter(category=category)
    if status:
        complaints = complaints.filter(status=status)
    if assigned_to:
        complaints = complaints.filter(assigned_to__icontains=assigned_to)
    if search:
        complaints = complaints.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search) |
            Q(student__username__icontains=search) |
            Q(student__email__icontains=search)
        )
    
    complaints = complaints.order_by('-created_at')

    paginator = Paginator(complaints, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    total_complaints = Complaint.objects.count()
    pending_complaints = Complaint.objects.filter(status='pending').count()
    in_progress_complaints = Complaint.objects.filter(status='in_progress').count()
    resolved_complaints = Complaint.objects.filter(status='resolved').count()
    closed_complaints = Complaint.objects.filter(status='closed').count()
    
    # Get unique assigned departments for filter
    assigned_departments = Complaint.objects.exclude(assigned_to__isnull=True).exclude(assigned_to='').values_list('assigned_to', flat=True).distinct()
    context = {
        'page_obj': page_obj,
        'total_complaints': total_complaints,
        'pending_complaints': pending_complaints,
        'in_progress_complaints': in_progress_complaints,
        'resolved_complaints': resolved_complaints,
        'closed_complaints': closed_complaints,
        'assigned_departments': assigned_departments,
        'current_filters': {
            'type': complaint_type,
            'category': category,
            'status': status,
            'search': search,
            'assigned_to': assigned_to,
        }
    }
    return render(request, 'complaints/admin_dashboard.html', context)

@login_required
def complaint_detail(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    try:
        profile = request.user.profile
        if profile.is_admin():
            pass
        else:
            if complaint.student != request.user or complaint.type == 'anonymous':
                messages.error(request, 'You do not have permission to view this complaint.')
                return redirect('student_dashboard')
    except Profile.DoesNotExist:
        messages.error(request, 'You do not have permission to view this complaint.')
        return redirect('student_dashboard')
    
    if request.method == 'POST':
        form = ComplaintStatusForm(request.POST, instance=complaint)
        if form.is_valid():
            form.save()
            messages.success(request, 'Complaint status updated successfully!')
            return redirect('complaint_detail', complaint_id=complaint.id)
    else:
        form = ComplaintStatusForm(instance=complaint)
    
    context = {
        'complaint': complaint,
        'form': form,
        'is_admin': profile.is_admin() if hasattr(request.user, 'profile') else False,
    }
    return render(request, 'complaints/complaint_detail.html', context)