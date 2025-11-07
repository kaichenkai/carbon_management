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
    
    class Meta:
        model = MaterialConsumption
        fields = [
            'hotel_name', 'department', 'category_level1', 'category_level2',
            'product_name',
            'consumption_date', 'consumption_time',
            'quantity', 'special_note'
        ]
        widgets = {
            'hotel_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('输入酒店名称')
            }),
            'department': forms.Select(attrs={
                'class': 'form-select'
            }),
            'consumption_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'consumption_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': _('输入消耗数量')
            }),
            'special_note': forms.Textarea(attrs={
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
                category_level1=category_level1,
                category_level2=category_level2
            ).first()
            print(coefficient.coefficient)

            # Store product information
            cleaned_data['product_unit'] = coefficient.unit
            cleaned_data['emission_coefficient'] = coefficient.coefficient
            
        except EmissionCoefficient.DoesNotExist:
            raise forms.ValidationError(_('产品编号不存在或与所选分类不匹配'))
        
        # Validate consumption date is not in the future
        consumption_date = cleaned_data.get('consumption_date')
        if consumption_date:
            from datetime import date
            if consumption_date > date.today():
                raise forms.ValidationError(_('消耗日期不能是未来日期'))
        
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
