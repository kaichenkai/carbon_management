from django.urls import path
from . import views

urlpatterns = [
    path('', views.consumption_list, name='consumption_list'),
    path('create/', views.consumption_create, name='consumption_create'),
    path('<int:pk>/edit/', views.consumption_edit, name='consumption_edit'),
    path('<int:pk>/delete/', views.consumption_delete, name='consumption_delete'),
    path('import/', views.data_import, name='data_import'),
    path('import/template/', views.download_import_template, name='download_import_template'),
    path('export/', views.consumption_export, name='consumption_export'),
    path('api/level2-categories/', views.get_level2_categories, name='get_level2_categories'),
    path('api/products-by-category/', views.get_products_by_category, name='get_products_by_category'),
]
