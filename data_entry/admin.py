from django.contrib import admin
from django.utils.html import format_html
from .models import MaterialConsumption


@admin.register(MaterialConsumption)
class MaterialConsumptionAdmin(admin.ModelAdmin):
    """Admin interface for Material Consumption records"""
    
    # List display
    list_display = [
        'hotel_name',
        'department',
        'product_name',
        'quantity',
        'product_unit',
        'emission_coefficient',
        'carbon_emission_display',
        'consumption_date',
        'consumption_time',
        'created_at',
    ]
    
    # List filters
    list_filter = [
        'department',
        'hotel_name',
        'category_level1',
        'category_level2',
        'consumption_date',
        'created_at',
    ]
    
    # Search fields
    search_fields = [
        'hotel_name',
        'product_name',
        'notes',
    ]
    
    # Read-only fields
    readonly_fields = [
        'carbon_emission',
        'created_at',
        'updated_at',
    ]
    
    # Fieldsets for better organization
    fieldsets = (
        ('基本信息', {
            'fields': ('hotel_name', 'department')
        }),
        ('产品信息', {
            'fields': (
                'product_name',
                'category_level1',
                'category_level2',
                'product_unit',
                'emission_coefficient',
            )
        }),
        ('消耗时间', {
            'fields': (('consumption_date', 'consumption_time'),)
        }),
        ('消耗数据', {
            'fields': ('quantity', 'carbon_emission')
        }),
        ('附加信息', {
            'fields': ('notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Ordering
    ordering = ['-consumption_date', '-consumption_time', '-created_at']
    
    # Date hierarchy
    date_hierarchy = 'consumption_date'
    
    # Items per page
    list_per_page = 25
    
    # Custom display methods
    def carbon_emission_display(self, obj):
        """Display carbon emission with color coding"""
        if obj.carbon_emission:
            if obj.carbon_emission > 1000:
                color = 'red'
            elif obj.carbon_emission > 500:
                color = 'orange'
            else:
                color = 'green'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{} kgCO2e</span>',
                color,
                f'{obj.carbon_emission:.2f}'
            )
        return '-'
    carbon_emission_display.short_description = '碳排放量'
    carbon_emission_display.admin_order_field = 'carbon_emission'
    
    
    # Actions
    actions = ['export_selected_records']
    
    def export_selected_records(self, request, queryset):
        """Export selected records (placeholder for future implementation)"""
        self.message_user(request, f"已选择 {queryset.count()} 条记录进行导出")
    export_selected_records.short_description = "导出选中的记录"
