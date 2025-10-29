from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import MaterialConsumption
from .forms import MaterialConsumptionForm
from coefficients.models import EmissionCoefficient, EmissionCategory


def consumption_list(request):
    """List all material consumption records"""
    consumptions = MaterialConsumption.objects.all()
    
    # Sorting
    sort_by = request.GET.get('sort', '-consumption_date_start')
    order = request.GET.get('order', 'desc')
    
    # Valid sort fields
    valid_sorts = {
        'hotel_name': 'hotel_name',
        'department': 'department',
        'product_code': 'product_code',
        'product_name': 'product_name',
        'category_level1': 'category_level1__name',
        'category_level2': 'category_level2__name',
        'consumption_date_start': 'consumption_date_start',
        'quantity': 'quantity',
        'carbon_emission': 'carbon_emission',
    }
    
    if sort_by.lstrip('-') in valid_sorts:
        # Get the actual field name for sorting (handles ForeignKey relations)
        actual_sort_field = valid_sorts[sort_by.lstrip('-')]
        # Toggle order if clicking the same column
        if order == 'asc':
            consumptions = consumptions.order_by(actual_sort_field)
        else:
            consumptions = consumptions.order_by(f'-{actual_sort_field}')
    else:
        consumptions = consumptions.order_by('-consumption_date_start', '-created_at')
    
    # Pagination
    paginator = Paginator(consumptions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_sort': sort_by.lstrip('-'),
        'current_order': order,
    }
    return render(request, 'data_entry/consumption_list.html', context)


def consumption_create(request):
    """Create new material consumption record"""
    if request.method == 'POST':
        form = MaterialConsumptionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('消耗记录创建成功'))
            return redirect('consumption_list')
    else:
        form = MaterialConsumptionForm()
    
    # Get all product codes for datalist
    product_codes = EmissionCoefficient.objects.values_list('product_code', flat=True)
    
    context = {
        'form': form,
        'product_codes': product_codes,
    }
    return render(request, 'data_entry/consumption_form.html', context)


def consumption_edit(request, pk):
    """Edit existing material consumption record"""
    consumption = get_object_or_404(MaterialConsumption, pk=pk)
    
    if request.method == 'POST':
        form = MaterialConsumptionForm(request.POST, instance=consumption)
        if form.is_valid():
            form.save()
            messages.success(request, _('消耗记录更新成功'))
            return redirect('consumption_list')
    else:
        form = MaterialConsumptionForm(instance=consumption)
    
    # Get all product codes for datalist
    product_codes = EmissionCoefficient.objects.values_list('product_code', flat=True)
    
    context = {
        'form': form,
        'product_codes': product_codes,
        'consumption': consumption,
    }
    return render(request, 'data_entry/consumption_form.html', context)


def consumption_delete(request, pk):
    """Delete material consumption record"""
    consumption = get_object_or_404(MaterialConsumption, pk=pk)
    consumption.delete()
    messages.success(request, _('消耗记录删除成功'))
    return redirect('consumption_list')


def get_product_info(request):
    """API endpoint to get product information by product code"""
    product_code = request.GET.get('code')
    
    try:
        coefficient = EmissionCoefficient.objects.get(product_code=product_code)
        data = {
            'success': True,
            'product_name': coefficient.product_name,
            'category_level1': coefficient.category_level1.name,
            'category_level1_id': coefficient.category_level1.id,
            'category_level2': coefficient.category_level2.name,
            'category_level2_id': coefficient.category_level2.id,
            'unit': coefficient.unit,
            'coefficient': str(coefficient.coefficient),
        }
    except EmissionCoefficient.DoesNotExist:
        data = {
            'success': False,
            'error': _('产品代码不存在')
        }
    
    return JsonResponse(data)


def get_level2_categories(request):
    """API endpoint to get level 2 categories by level 1 category"""
    level1_id = request.GET.get('level1_id')
    
    if not level1_id:
        return JsonResponse({'success': False, 'error': 'Missing level1_id'})
    
    try:
        level1_category = EmissionCategory.objects.get(id=level1_id, level=1)
        level2_categories = EmissionCategory.objects.filter(
            level=2,
            parent=level1_category
        ).values('id', 'name')
        
        return JsonResponse({
            'success': True,
            'categories': list(level2_categories)
        })
    except EmissionCategory.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': _('一级分类不存在')
        })


def get_products_by_category(request):
    """API endpoint to get products by category"""
    level1_id = request.GET.get('level1_id')
    level2_id = request.GET.get('level2_id')
    
    try:
        filters = {}
        if level1_id:
            filters['category_level1_id'] = level1_id
        if level2_id:
            filters['category_level2_id'] = level2_id
        
        products = EmissionCoefficient.objects.filter(**filters).values(
            'id', 'product_code', 'product_name', 'unit', 'coefficient'
        )
        
        return JsonResponse({
            'success': True,
            'products': list(products)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
