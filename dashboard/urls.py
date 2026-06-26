from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('customization/', views.data_customization_view, name='data_customization'),
]
