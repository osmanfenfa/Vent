from django.urls import path
from django.shortcuts import redirect
from . import views

def redirect_to_login(request):
    return redirect('login')

urlpatterns = [
    path('', redirect_to_login, name='home'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('submit/non-anonymous/', views.submit_non_anonymous_complaint, name='submit_non_anonymous'),
    path('submit/anonymous/', views.submit_anonymous_complaint, name='submit_anonymous'),
    path('my-complaints/', views.my_complaints, name='my_complaints'),
    path('complaint/<int:complaint_id>/', views.complaint_detail, name='complaint_detail'),
    path('complaint/<int:complaint_id>/export/', views.export_complaint_pdf, name='export_complaint_pdf'),
    path('complaints/export/non-anonymous/', views.export_all_non_anonymous_pdf, name='export_all_non_anonymous_pdf'),
]