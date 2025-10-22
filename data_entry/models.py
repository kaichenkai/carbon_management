from django.db import models
from django.utils.translation import gettext_lazy as _
from coefficients.models import EmissionCoefficient

# Create your models here.

class MaterialConsumption(models.Model):
    """Material consumption record for carbon emission tracking"""
    
    # Basic information
    hotel_name = models.CharField(_('酒店名称'), max_length=200, blank=True)
    department = models.CharField(_('部门'), max_length=50)
    
    # Product information (from EmissionCoefficient)
    product_code = models.CharField(_('产品代码'), max_length=50, db_index=True)
    product_name = models.CharField(_('产品名称'), max_length=200)
    category_level1 = models.CharField(_('一级分类'), max_length=100)
    category_level2 = models.CharField(_('二级分类'), max_length=100)
    product_unit = models.CharField(_('产品单位'), max_length=20)
    emission_coefficient = models.DecimalField(_('碳排放系数'), max_digits=10, decimal_places=2)
    
    # Consumption period
    consumption_date_start = models.DateField(_('消耗开始日期'))
    consumption_date_end = models.DateField(_('消耗结束日期'))
    consumption_time_start = models.TimeField(_('消耗开始时间'))
    consumption_time_end = models.TimeField(_('消耗结束时间'))
    
    # Consumption data
    quantity = models.DecimalField(_('消耗数量'), max_digits=10, decimal_places=2)
    
    # Calculated emission (auto-calculated)
    carbon_emission = models.DecimalField(
        _('碳排放量(kgCO2e)'),
        max_digits=12,
        decimal_places=2,
        editable=False
    )
    
    # Additional info
    notes = models.TextField(_('备注'), blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('物料消耗记录')
        verbose_name_plural = _('物料消耗记录')
        ordering = ['-consumption_date_start', '-created_at']
        indexes = [
            models.Index(fields=['hotel_name', 'department']),
            models.Index(fields=['consumption_date_start', 'consumption_date_end']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-calculate carbon emission
        self.carbon_emission = self.quantity * self.emission_coefficient
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.hotel_name} - {self.product_name} ({self.consumption_date_start})"
