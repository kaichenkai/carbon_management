from django import forms
from django.utils.translation import gettext_lazy as _
from .models import MaterialConsumption
from coefficients.models import EmissionCoefficient, EmissionCategory


class MaterialConsumptionForm(forms.ModelForm):
    """Form for material consumption entry"""
    
    # Category level 1 field with search
    category_level1 = forms.ModelChoiceField(
        label=_('一级分类'),
        queryset=EmissionCategory.objects.filter(level=1),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_category_level1'
        })
    )
    
    # Category level 2 field with search (will be populated dynamically)
    category_level2 = forms.ModelChoiceField(
        label=_('二级分类'),
        queryset=EmissionCategory.objects.filter(level=2),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_category_level2'
        })
    )
    
    # Product name field
    product_name = forms.CharField(
        label=_('产品名称'),
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('输入产品名称'),
            'list': 'product-names'
        })
    )
    
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
            'hotel_name', 'department', 'category_level1', 'category_level2',
            'product_name', 'product_code',
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
        
        # If editing existing record, populate fields
        if self.instance.pk:
            self.fields['product_code'].initial = self.instance.product_code
            self.fields['product_name'].initial = self.instance.product_name
            
            # Set category fields if they exist (they are already ForeignKey objects)
            if self.instance.category_level1:
                # Filter level 2 categories by parent
                self.fields['category_level2'].queryset = EmissionCategory.objects.filter(
                    level=2,
                    parent=self.instance.category_level1
                )
    
    def clean(self):
        cleaned_data = super().clean()
        product_code = cleaned_data.get('product_code')
        category_level1 = cleaned_data.get('category_level1')
        category_level2 = cleaned_data.get('category_level2')
        product_name = cleaned_data.get('product_name')
        
        # Validate that level 2 category belongs to level 1 category
        if category_level1 and category_level2:
            if category_level2.parent != category_level1:
                raise forms.ValidationError(_('二级分类必须属于所选的一级分类'))
        
        # 根据二级分类计算碳排放系数
        try:
            coefficient = EmissionCoefficient.objects.filter(
                # product_code=product_code,
                category_level1=category_level1,
                category_level2=category_level2
            ).first()
            print(coefficient.coefficient)

            # Store product information
            cleaned_data['product_unit'] = coefficient.unit
            cleaned_data['emission_coefficient'] = coefficient.coefficient
            
        except EmissionCoefficient.DoesNotExist:
            raise forms.ValidationError(_('产品编号不存在或与所选分类不匹配'))
        
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
        # category_level1 and category_level2 are already set as ForeignKey objects
        instance.product_unit = self.cleaned_data['product_unit']
        instance.emission_coefficient = self.cleaned_data['emission_coefficient']
        
        if commit:
            instance.save()
        return instance
