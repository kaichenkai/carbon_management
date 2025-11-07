from django.db import models
from django.utils.translation import gettext_lazy as _
from coefficients.models import EmissionCoefficient, EmissionCategory

# Create your models here.

class MaterialConsumption(models.Model):
    """Material consumption record for carbon emission tracking"""
    
    # Basic information
    hotel_name = models.CharField(_('酒店名称'), max_length=200, blank=True)
    department = models.CharField(_('部门名称'), max_length=50, choices=EmissionCoefficient.DEPARTMENT_CHOICES)
    
    # Product information (from EmissionCoefficient)
    product_name = models.CharField(_('产品名称'), max_length=200)
    category_level1 = models.ForeignKey(
        EmissionCategory,
        on_delete=models.PROTECT,
        verbose_name=_('一级分类'),
        related_name='consumptions_level1',
        limit_choices_to={'level': 1}
    )
    category_level2 = models.ForeignKey(
        EmissionCategory,
        on_delete=models.PROTECT,
        verbose_name=_('二级分类'),
        related_name='consumptions_level2',
        limit_choices_to={'level': 2}
    )
    product_unit = models.CharField(_('产品单位'), max_length=20)
    emission_coefficient = models.DecimalField(_('碳排放系数'), max_digits=10, decimal_places=2)
    
    # Consumption datetime
    consumption_datetime = models.DateTimeField(_('消耗日期时间'), null=True)
    
    # Consumption data
    quantity = models.DecimalField(_('消耗数量'), max_digits=10, decimal_places=2)

    # 
    
    # Calculated emission (auto-calculated)
    carbon_emission = models.DecimalField(
        _('碳排放量(kgCO2e)'),
        max_digits=12,
        decimal_places=2,
        editable=False
    )
    
    special_note = models.TextField(_('特殊备注'), blank=True)
    
    # Additional info
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('物料消耗记录')
        verbose_name_plural = _('物料消耗记录')
        ordering = ['-consumption_datetime', '-created_at']
        indexes = [
            models.Index(fields=['hotel_name', 'department']),
            models.Index(fields=['consumption_datetime']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-calculate carbon emission
        self.carbon_emission = self.quantity * self.emission_coefficient
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.hotel_name} - {self.product_name} ({self.consumption_datetime.strftime('%Y-%m-%d %H:%M')})"
