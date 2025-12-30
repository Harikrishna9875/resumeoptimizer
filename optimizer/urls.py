from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/optimize/', views.optimize_resume, name='optimize_resume'),
    path('api/upload-pdf/', views.upload_pdf, name='upload_pdf'),
]
