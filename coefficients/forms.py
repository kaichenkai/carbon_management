from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import Hotel, EmissionCoefficient, EmissionCategory


class CustomLoginForm(AuthenticationForm):
    """Custom login form with hotel selection"""
    hotel = forms.ModelChoiceField(
        queryset=Hotel.objects.filter(is_active=True),
        required=True,
        label=_('酒店代码'),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'hotel-select'
        })
    )
    
    username = forms.CharField(
        label=_('用户名'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('请输入用户名'),
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        label=_('密码'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('请输入密码')
        })
    )
    
    remember_me = forms.BooleanField(
        label=_('记住我'),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )


class EmissionCoefficientForm(forms.ModelForm):
    """Form for creating/editing emission coefficients"""
    
    category_level1_name = forms.CharField(
        label=_('一级分类'),
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'list': 'level1-datalist'
        })
    )
    
    category_level2_name = forms.CharField(
        label=_('二级分类'),
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'list': 'level2-datalist'
        })
    )
    
    department = forms.ChoiceField(
        label=_('部门名称'),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    class Meta:
        model = EmissionCoefficient
        fields = ['product_code', 'product_name', 'product_name_en', 
                  'unit', 'coefficient', 'special_note']
        widgets = {
            'product_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('例如: F101000319')
            }),
            'product_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('产品名称')
            }),
            'product_name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Product Name (English)')
            }),
            'unit': forms.Select(attrs={
                'class': 'form-select'
            }),
            'coefficient': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'special_note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('特殊备注（可选）')
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set department choices from model
        from .models import EmissionCoefficient
        self.fields['department'].choices = EmissionCoefficient.DEPARTMENT_CHOICES
        
        if self.instance.pk:
            # Editing existing coefficient
            if self.instance.category_level1:
                self.fields['category_level1_name'].initial = self.instance.category_level1.name
            if self.instance.category_level2:
                self.fields['category_level2_name'].initial = self.instance.category_level2.name
            if self.instance.department:
                self.fields['department'].initial = self.instance.department
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Get or create level 1 category
        level1_name = self.cleaned_data['category_level1_name']
        level1_category, _ = EmissionCategory.objects.get_or_create(
            name=level1_name,
            level=1,
            defaults={'parent': None}
        )
        
        # Get or create level 2 category
        level2_name = self.cleaned_data['category_level2_name']
        level2_category, _ = EmissionCategory.objects.get_or_create(
            name=level2_name,
            level=2,
            parent=level1_category
        )
        
        instance.category_level1 = level1_category
        instance.category_level2 = level2_category
        instance.department = self.cleaned_data['department']
        
        if commit:
            instance.save()
        return instance


class CoefficientSearchForm(forms.Form):
    """Search form for coefficients"""
    query = forms.CharField(
        required=False,
        label=_('搜索'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('搜索产品编号、分类或产品名称...')
        })
    )
