from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.custom_login, name='login'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    
    # Coefficient management
    path('coefficients/', views.coefficient_list, name='coefficient_list'),
    path('coefficients/create/', views.coefficient_create, name='coefficient_create'),
    path('coefficients/<int:pk>/edit/', views.coefficient_edit, name='coefficient_edit'),
    path('coefficients/<int:pk>/delete/', views.coefficient_delete, name='coefficient_delete'),
    path('coefficients/export/', views.coefficient_export, name='coefficient_export'),
    path('coefficients/template/', views.coefficient_template, name='coefficient_template'),
    path('coefficients/import/', views.coefficient_import, name='coefficient_import'),
]
