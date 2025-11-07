from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import Hotel, CustomUser, EmissionCategory, EmissionCoefficient


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'name_en', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code', 'name', 'name_en']


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'hotel', 'position', 'is_approved', 'can_manage_coefficients', 'is_staff']
    list_filter = ['is_approved', 'can_manage_coefficients', 'is_staff', 'hotel']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        (_('额外信息'), {'fields': ('hotel', 'position', 'phone', 'is_approved', 'can_manage_coefficients')}),
    )


@admin.register(EmissionCategory)
class EmissionCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_en', 'level', 'parent', 'updated_at']
    list_filter = ['level', 'parent']
    search_fields = ['name', 'name_en']


@admin.register(EmissionCoefficient)
class EmissionCoefficientAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'category_level1', 'category_level2', 
                    'unit', 'coefficient', 'updated_at', 'updated_by']
    list_filter = ['category_level1', 'category_level2', 'unit', 'updated_at']
    search_fields = ['product_name', 'product_name_en']
    readonly_fields = ['created_at', 'updated_at']
