from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class Hotel(models.Model):
    """Hotel model for multi-hotel support"""
    code = models.CharField(_('酒店代码'), max_length=50, unique=True)
    name = models.CharField(_('酒店名称'), max_length=200)
    name_en = models.CharField(_('酒店名称(英文)'), max_length=200, blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    is_active = models.BooleanField(_('是否启用'), default=True)

    class Meta:
        verbose_name = _('酒店')
        verbose_name_plural = _('酒店')
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class CustomUser(AbstractUser):
    """Extended user model"""
    hotel = models.ForeignKey(
        Hotel, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_('所属酒店'),
        related_name='users'
    )
    position = models.CharField(_('岗位'), max_length=100, blank=True)
    phone = models.CharField(_('电话'), max_length=20, blank=True)
    is_approved = models.BooleanField(_('是否审批通过'), default=False)
    can_manage_coefficients = models.BooleanField(_('可管理系数'), default=False)
    
    class Meta:
        verbose_name = _('用户')
        verbose_name_plural = _('用户')

    def __str__(self):
        return self.username


class EmissionCategory(models.Model):
    """Emission category for hierarchical classification"""
    LEVEL_CHOICES = [
        (1, _('一级分类')),
        (2, _('二级分类')),
    ]
    
    name = models.CharField(_('分类名称'), max_length=200)
    name_en = models.CharField(_('分类名称(英文)'), max_length=200, blank=True)
    level = models.IntegerField(_('分类级别'), choices=LEVEL_CHOICES)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name=_('父级分类'),
        related_name='children'
    )
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)

    class Meta:
        verbose_name = _('排放分类')
        verbose_name_plural = _('排放分类')
        ordering = ['level', 'name']
        unique_together = ['name', 'parent']

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class EmissionCoefficient(models.Model):
    """Carbon emission coefficient database"""
    UNIT_CHOICES = [
        ('KG', _('KG')),
        ('L', _('L')),
    ]
    
    DEPARTMENT_CHOICES = [
        ('production', _('生产部')),
        ('rd', _('研发部')),
        ('administration', _('行政部')),
        ('logistics', _('后勤部')),
    ]
    
    product_code = models.CharField(_('产品编号'), max_length=50, db_index=True)
    category_level1 = models.ForeignKey(
        EmissionCategory,
        on_delete=models.PROTECT,
        verbose_name=_('一级分类'),
        related_name='coefficients_level1',
        limit_choices_to={'level': 1}
    )
    category_level2 = models.ForeignKey(
        EmissionCategory,
        on_delete=models.PROTECT,
        verbose_name=_('二级分类'),
        related_name='coefficients_level2',
        limit_choices_to={'level': 2}
    )
    product_name = models.CharField(_('产品名称'), max_length=200)
    product_name_en = models.CharField(_('产品名称(英文)'), max_length=200, blank=True)
    unit = models.CharField(_('单位'), max_length=20, choices=UNIT_CHOICES)
    coefficient = models.DecimalField(_('碳排放系数'), max_digits=10, decimal_places=2)
    department = models.CharField(_('部门名称'), max_length=50, choices=DEPARTMENT_CHOICES)
    special_note = models.TextField(_('特殊备注'), blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('最后更新'), auto_now=True)
    updated_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('更新人')
    )

    class Meta:
        verbose_name = _('碳排放系数')
        verbose_name_plural = _('碳排放系数')
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.product_code} - {self.product_name}"

    @classmethod
    def find_coefficient(cls, product_code=None, product_name=None):
        """
        Find emission coefficient by product code or name
        Returns the coefficient value or None
        """
        # First try: exact match by product code
        if product_code:
            try:
                coef = cls.objects.get(product_code=product_code)
                return coef.coefficient
            except cls.DoesNotExist:
                pass
        
        # Second try: keyword match by product name
        if product_name:
            # Try to find by product name (case-insensitive contains)
            matches = cls.objects.filter(
                models.Q(product_name__icontains=product_name) |
                models.Q(product_name_en__icontains=product_name)
            )
            if matches.exists():
                return matches.first().coefficient
        
        # No match found
        return None
