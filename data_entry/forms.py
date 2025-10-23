from django import forms
from django.utils.translation import gettext_lazy as _
from .models import MaterialConsumption
from coefficients.models import EmissionCoefficient


class MaterialConsumptionForm(forms.ModelForm):
    """Form for material consumption entry"""
    
    # Product code field with autocomplete
    product_code = forms.CharField(
        label=_('产品编号'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('输入或选择产品编号'),
            'list': 'product-codes'
        })
    )
    
    class Meta:
        model = MaterialConsumption
        fields = [
            'hotel_name', 'department', 'product_code',
            'consumption_date_start', 'consumption_date_end',
            'consumption_time_start', 'consumption_time_end',
            'quantity', 'notes'
        ]
        widgets = {
            'hotel_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('输入酒店名称')
            }),
            'department': forms.Select(attrs={
                'class': 'form-select'
            }),
            'consumption_date_start': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'YYYY-MM-DD'
            }),
            'consumption_date_end': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'YYYY-MM-DD'
            }),
            'consumption_time_start': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'placeholder': 'HH:MM'
            }),
            'consumption_time_end': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'placeholder': 'HH:MM'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': _('输入消耗数量')
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('备注信息（可选）')
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set department choices from EmissionCoefficient
        from coefficients.models import EmissionCoefficient
        self.fields['department'].widget = forms.Select(
            choices=EmissionCoefficient.DEPARTMENT_CHOICES,
            attrs={'class': 'form-select'}
        )
        
        # If editing existing record, populate product code
        if self.instance.pk:
            self.fields['product_code'].initial = self.instance.product_code
    
    def clean(self):
        cleaned_data = super().clean()
        product_code = cleaned_data.get('product_code')
        
        # Validate product code exists
        try:
            coefficient = EmissionCoefficient.objects.filter(product_code=product_code).first()
            
            # Auto-fill product information
            cleaned_data['product_name'] = coefficient.product_name
            cleaned_data['category_level1'] = coefficient.category_level1.name
            cleaned_data['category_level2'] = coefficient.category_level2.name
            cleaned_data['product_unit'] = coefficient.unit
            cleaned_data['emission_coefficient'] = coefficient.coefficient
            
        except EmissionCoefficient.DoesNotExist:
            raise forms.ValidationError(_('产品编号不存在，请选择有效的产品编号'))
        
        # Validate date range
        date_start = cleaned_data.get('consumption_date_start')
        date_end = cleaned_data.get('consumption_date_end')
        if date_start and date_end and date_start > date_end:
            raise forms.ValidationError(_('开始日期不能晚于结束日期'))
        
        # Validate time range
        time_start = cleaned_data.get('consumption_time_start')
        time_end = cleaned_data.get('consumption_time_end')
        if time_start and time_end and time_start > time_end:
            raise forms.ValidationError(_('开始时间不能晚于结束时间'))
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set product information from cleaned data
        instance.product_name = self.cleaned_data['product_name']
        instance.category_level1 = self.cleaned_data['category_level1']
        instance.category_level2 = self.cleaned_data['category_level2']
        instance.product_unit = self.cleaned_data['product_unit']
        instance.emission_coefficient = self.cleaned_data['emission_coefficient']
        
        if commit:
            instance.save()
        return instance
