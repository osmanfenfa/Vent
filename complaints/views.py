from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from .models import Complaint
from .forms import NonAnonymousComplaintForm, AnonymousComplaintForm, ComplaintStatusForm
from accounts.models import Profile
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

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

@login_required
def export_complaint_pdf(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)

    # Only admin can export and only for non-anonymous complaints
    try:
        profile = request.user.profile
        if not profile.is_admin():
            messages.error(request, 'You do not have permission to export this complaint.')
            return redirect('complaint_detail', complaint_id=complaint.id)
    except Profile.DoesNotExist:
        messages.error(request, 'You do not have permission to export this complaint.')
        return redirect('complaint_detail', complaint_id=complaint.id)

    if complaint.type != 'non_anonymous' or not complaint.student:
        messages.error(request, 'Only non-anonymous complaints can be exported.')
        return redirect('complaint_detail', complaint_id=complaint.id)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title_style.textColor = colors.HexColor('#0b2e61')

    elements.append(Paragraph('VENT', title_style))
    elements.append(Paragraph('UniMak Students Complaint Report', title_style))
    elements.append(Spacer(1, 12))

    student = complaint.student
    profile = getattr(student, 'profile', None)
    student_name = (profile.full_name if profile and profile.full_name else student.get_full_name()) or student.username
    department = getattr(profile, 'department', '') or 'Not provided'
    student_id = getattr(profile, 'student_id', '') or 'Not provided'

    student_data = [
        ['Full Name', student_name],
        ['Department', department],
        ['Student ID', student_id],
    ]
    student_table = Table(student_data, colWidths=[120, 360])
    student_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e9eff7')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#c3d3eb')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#c3d3eb')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f5f7fb')),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(student_table)
    elements.append(Spacer(1, 18))

    submitted_date = complaint.created_at.strftime('%B %d, %Y at %I:%M %p')
    complaint_data = [
        ['Title', complaint.title],
        ['Category', complaint.get_category_display()],
        ['Submitted Date', submitted_date],
        ['Description', complaint.description],
        ['Status', complaint.get_status_display()],
        ['Handled By', complaint.assigned_to or 'Descreet']
    ]
    complaint_table = Table(complaint_data, colWidths=[120, 360])
    complaint_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e9eff7')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#c3d3eb')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#c3d3eb')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f5f7fb')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(complaint_table)

    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="complaint_{complaint.id}.pdf"'
    response.write(pdf)
    return response

@login_required
def export_all_non_anonymous_pdf(request):
    try:
        profile = request.user.profile
        if not profile.is_admin():
            messages.error(request, 'You do not have permission to export.')
            return redirect('admin_dashboard')
    except Profile.DoesNotExist:
        messages.error(request, 'You do not have permission to export.')
        return redirect('admin_dashboard')

    complaints = Complaint.objects.filter(type='non_anonymous').order_by('-created_at')

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles['Title']
    title_style.textColor = colors.HexColor('#0b2e61')

    elements.append(Paragraph('VENT', title_style))
    elements.append(Paragraph('UniMak Students Complaint Report', title_style))
    elements.append(Spacer(1, 12))

    if not complaints.exists():
        elements.append(Paragraph('No non-anonymous complaints found.', styles['Normal']))
    else:
        for idx, complaint in enumerate(complaints, start=1):
            student = complaint.student
            profile = getattr(student, 'profile', None)
            student_name = (profile.full_name if profile and profile.full_name else student.get_full_name()) or student.username
            department = getattr(profile, 'department', '') or 'Not provided'
            student_id = getattr(profile, 'student_id', '') or 'Not provided'

            # Section header per complaint
            elements.append(Paragraph(f'Complaint #{complaint.id}', styles['Heading2']))
            elements.append(Spacer(1, 6))

            student_data = [
                ['Full Name', student_name],
                ['Department', department],
                ['Student ID', student_id],
            ]
            student_table = Table(student_data, colWidths=[120, 360])
            student_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e9eff7')),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#c3d3eb')),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#c3d3eb')),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f5f7fb')),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('PADDING', (0,0), (-1,-1), 6),
            ]))
            elements.append(student_table)
            elements.append(Spacer(1, 12))

            submitted_date = complaint.created_at.strftime('%B %d, %Y at %I:%M %p')
            complaint_data = [
                ['Title', complaint.title],
                ['Category', complaint.get_category_display()],
                ['Submitted Date', submitted_date],
                ['Description', complaint.description],
                ['Status', complaint.get_status_display()],
                ['Handled By', complaint.assigned_to or 'Descreet']
            ]
            complaint_table = Table(complaint_data, colWidths=[120, 360])
            complaint_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e9eff7')),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#c3d3eb')),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#c3d3eb')),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f5f7fb')),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('PADDING', (0,0), (-1,-1), 6),
            ]))
            elements.append(complaint_table)

            # Separator between entries
            if idx < complaints.count():
                elements.append(Spacer(1, 18))

    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="non_anonymous_complaints.pdf"'
    response.write(pdf)
    return response