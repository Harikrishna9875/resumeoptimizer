from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'), 
    path('optimize/', views.optimize_resume, name='optimize_resume'),
]
