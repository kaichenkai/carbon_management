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
    product_name = models.CharField(_('产品名称'), max_length=200)
    product_unit = models.CharField(_('产品单位'), max_length=20)
    emission_coefficient = models.DecimalField(_('碳排放系数'), max_digits=10, decimal_places=6)
    
    # Consumption date and time
    consumption_date = models.DateField(_('消耗日期'), null=True)
    consumption_time = models.TimeField(_('消耗时间'), null=True)
    
    # Consumption data
    quantity = models.DecimalField(_('消耗数量'), max_digits=10, decimal_places=6)

    # 
    
    # Calculated emission (auto-calculated)
    carbon_emission = models.DecimalField(
        _('碳排放量(kgCO2e)'),
        max_digits=12,
        decimal_places=6,
        editable=False
    )
    
    special_note = models.TextField(_('特殊备注'), blank=True)
    
    # Additional info
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('物料消耗记录')
        verbose_name_plural = _('物料消耗记录')
        ordering = ['-consumption_date', '-consumption_time', '-created_at']
        indexes = [
            models.Index(fields=['hotel_name', 'department']),
            models.Index(fields=['consumption_date', 'consumption_time']),
            # Dashboard query optimization indexes
            models.Index(fields=['consumption_date', 'category_level1']),
            models.Index(fields=['consumption_date', 'category_level2']),
            models.Index(fields=['consumption_date', 'department']),
            models.Index(fields=['category_level1', 'category_level2']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-calculate carbon emission
        self.carbon_emission = self.quantity * self.emission_coefficient
        super().save(*args, **kwargs)
        
        # Update related ConsumerData records
        self.update_consumer_data()
    
    def delete(self, *args, **kwargs):
        # Store info before deletion
        hotel_name = self.hotel_name
        department = self.department
        consumption_date = self.consumption_date
        
        super().delete(*args, **kwargs)
        
        # Update related ConsumerData records after deletion
        consumer_data = ConsumerData.objects.filter(
            hotel_name=hotel_name,
            department=department,
            consumption_date=consumption_date
        )
        for cd in consumer_data:
            cd.daily_carbon_emission = cd.calculate_daily_emission()
            cd.save(update_fields=['daily_carbon_emission', 'updated_at'])
    
    def update_consumer_data(self):
        """Update daily carbon emission for related ConsumerData records"""
        try:
            consumer_data = ConsumerData.objects.filter(
                hotel_name=self.hotel_name,
                department=self.department,
                consumption_date=self.consumption_date
            )
            for cd in consumer_data:
                cd.daily_carbon_emission = cd.calculate_daily_emission()
                cd.save(update_fields=['daily_carbon_emission', 'updated_at'])
        except ConsumerData.DoesNotExist:
            pass
    
    def __str__(self):
        return f"{self.hotel_name} - {self.product_name} ({self.consumption_date} {self.consumption_time.strftime('%H:%M')})"


class ConsumerData(models.Model):
    """Consumer data record for tracking daily consumer count and carbon emissions"""
    
    # Basic information
    hotel_name = models.CharField(_('酒店名称'), max_length=200, blank=True)
    department = models.CharField(_('部门名称'), max_length=50, choices=EmissionCoefficient.DEPARTMENT_CHOICES)
    
    # Date information
    consumption_date = models.DateField(_('消耗日期'))
    
    # Consumer count
    consumer_count = models.IntegerField(_('消费者人数'), default=0)
    
    # Auto-calculated total carbon emission for the day
    daily_carbon_emission = models.DecimalField(
        _('当日碳排总量(kgCO2e)'),
        max_digits=12,
        decimal_places=6,
        default=0,
        editable=False
    )
    
    # Notes
    notes = models.TextField(_('备注'), blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('消费者数据')
        verbose_name_plural = _('消费者数据')
        ordering = ['-consumption_date', '-created_at']
        indexes = [
            models.Index(fields=['hotel_name', 'department']),
            models.Index(fields=['consumption_date']),
        ]
        # Ensure unique record per hotel/department/date
        unique_together = [['hotel_name', 'department', 'consumption_date']]
    
    def calculate_daily_emission(self):
        """Calculate total carbon emission for this hotel/department/date"""
        from django.db.models import Sum
        total = MaterialConsumption.objects.filter(
            hotel_name=self.hotel_name,
            department=self.department,
            consumption_date=self.consumption_date
        ).aggregate(total=Sum('carbon_emission'))['total']
        return total or 0
    
    def save(self, *args, **kwargs):
        # Auto-calculate daily carbon emission
        self.daily_carbon_emission = self.calculate_daily_emission()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.hotel_name} - {self.get_department_display()} ({self.consumption_date})"
