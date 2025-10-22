from django.urls import path
from . import views

urlpatterns = [
    path('', views.consumption_list, name='consumption_list'),
    path('create/', views.consumption_create, name='consumption_create'),
    path('<int:pk>/edit/', views.consumption_edit, name='consumption_edit'),
    path('<int:pk>/delete/', views.consumption_delete, name='consumption_delete'),
    path('api/product-info/', views.get_product_info, name='get_product_info'),
]
