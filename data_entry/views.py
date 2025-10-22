from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import MaterialConsumption
from .forms import MaterialConsumptionForm
from coefficients.models import EmissionCoefficient


def consumption_list(request):
    """List all material consumption records"""
    consumptions = MaterialConsumption.objects.all()
    
    # Pagination
    paginator = Paginator(consumptions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
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
            'category_level2': coefficient.category_level2.name,
            'unit': coefficient.unit,
            'coefficient': str(coefficient.coefficient),
        }
    except EmissionCoefficient.DoesNotExist:
        data = {
            'success': False,
            'error': _('产品代码不存在')
        }
    
    return JsonResponse(data)
