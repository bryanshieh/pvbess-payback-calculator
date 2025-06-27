from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .models import EnergyProfile, PVSystem, BESSSystem, FinancialParameters, CalculationResult
from .forms import (EnergyProfileForm, PVSystemForm, BESSSystemForm, 
                   FinancialParametersForm, QuickCalculatorForm)
from .utils import run_complete_calculation, quick_calculation


def home(request):
    """Home page with quick calculator"""
    if request.method == 'POST':
        form = QuickCalculatorForm(request.POST)
        if form.is_valid():
            # Run quick calculation
            results = quick_calculation(
                annual_consumption=form.cleaned_data['annual_consumption'],
                system_size=form.cleaned_data['system_size'],
                battery_capacity=form.cleaned_data['battery_capacity'],
                electricity_rate=form.cleaned_data['electricity_rate'],
                pv_cost_per_kw=form.cleaned_data['pv_cost_per_kw'],
                battery_cost_per_kwh=form.cleaned_data['battery_cost_per_kwh']
            )
            return render(request, 'calculator/quick_results.html', {
                'form': form,
                'results': results
            })
    else:
        form = QuickCalculatorForm()
    
    return render(request, 'calculator/home.html', {'form': form})


def detailed_calculator(request):
    """Detailed calculator with step-by-step input"""
    return render(request, 'calculator/detailed_calculator.html')


def energy_profile_create(request):
    """Create energy profile"""
    if request.method == 'POST':
        form = EnergyProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            if request.user.is_authenticated:
                profile.user = request.user
            profile.save()
            messages.success(request, 'Energy profile created successfully!')
            return redirect('pv_system_create')
    else:
        form = EnergyProfileForm()
    
    return render(request, 'calculator/energy_profile_form.html', {'form': form})


def pv_system_create(request):
    """Create PV system"""
    if request.method == 'POST':
        form = PVSystemForm(request.POST)
        if form.is_valid():
            pv_system = form.save()
            messages.success(request, 'PV system created successfully!')
            return redirect('bess_system_create')
    else:
        form = PVSystemForm()
    
    return render(request, 'calculator/pv_system_form.html', {'form': form})


def bess_system_create(request):
    """Create BESS system"""
    if request.method == 'POST':
        form = BESSSystemForm(request.POST)
        if form.is_valid():
            bess_system = form.save()
            messages.success(request, 'BESS system created successfully!')
            return redirect('financial_params_create')
    else:
        form = BESSSystemForm()
    
    return render(request, 'calculator/bess_system_form.html', {'form': form})


def financial_params_create(request):
    """Create financial parameters"""
    if request.method == 'POST':
        form = FinancialParametersForm(request.POST)
        if form.is_valid():
            financial_params = form.save()
            messages.success(request, 'Financial parameters created successfully!')
            return redirect('run_calculation')
    else:
        form = FinancialParametersForm()
    
    return render(request, 'calculator/financial_params_form.html', {'form': form})


def run_calculation(request):
    """Run the complete calculation"""
    # Get the most recent inputs (in a real app, you'd use session or user-specific data)
    try:
        energy_profile = EnergyProfile.objects.latest('created_at')
        pv_system = PVSystem.objects.latest('created_at')
        bess_system = BESSSystem.objects.latest('created_at')
        financial_params = FinancialParameters.objects.latest('created_at')
    except (EnergyProfile.DoesNotExist, PVSystem.DoesNotExist, 
            BESSSystem.DoesNotExist, FinancialParameters.DoesNotExist):
        messages.error(request, 'Please complete all input forms first.')
        return redirect('energy_profile_create')
    
    # Run calculation
    results = run_complete_calculation(energy_profile, pv_system, bess_system, financial_params)
    
    # Save results
    calculation_result = CalculationResult.objects.create(
        user=request.user if request.user.is_authenticated else None,
        name=f"Calculation {energy_profile.name}",
        energy_profile=energy_profile,
        pv_system=pv_system,
        bess_system=bess_system,
        financial_params=financial_params,
        total_system_cost=results['system_cost'],
        annual_savings=results['annual_savings'],
        payback_period_years=results['financial_metrics']['payback_period'],
        npv_25_years=results['financial_metrics']['npv'],
        irr_percent=results['financial_metrics']['irr'] * 100
    )
    
    # Store detailed results
    monthly_data = {
        'generation': results['monthly_generation'],
        'consumption': results['monthly_consumption'],
        'grid_import': results['battery_results']['grid_import'],
        'grid_export': results['battery_results']['grid_export'],
        'self_consumption': results['battery_results']['self_consumption'],
        'battery_state': results['battery_results']['battery_state']
    }
    calculation_result.set_monthly_results(monthly_data)
    
    annual_data = {
        'total_generation': results['total_annual_generation'],
        'total_consumption': results['total_annual_consumption'],
        'self_consumption_rate': results['self_consumption_rate'],
        'total_grid_import': sum(results['battery_results']['grid_import']),
        'total_grid_export': sum(results['battery_results']['grid_export'])
    }
    calculation_result.set_annual_results(annual_data)
    calculation_result.save()
    
    return render(request, 'calculator/results.html', {
        'results': results,
        'calculation_result': calculation_result,
        'energy_profile': energy_profile,
        'pv_system': pv_system,
        'bess_system': bess_system,
        'financial_params': financial_params
    })


def results_detail(request, result_id):
    """View detailed results"""
    calculation_result = get_object_or_404(CalculationResult, id=result_id)
    
    # Check if user has permission to view this result
    if calculation_result.user and calculation_result.user != request.user:
        messages.error(request, 'You do not have permission to view this result.')
        return redirect('home')
    
    return render(request, 'calculator/results_detail.html', {
        'calculation_result': calculation_result
    })


@login_required
def my_calculations(request):
    """View user's calculation history"""
    calculations = CalculationResult.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'calculator/my_calculations.html', {
        'calculations': calculations
    })


def about(request):
    """About page"""
    return render(request, 'calculator/about.html')


def help_page(request):
    """Help page"""
    return render(request, 'calculator/help.html')


@csrf_exempt
def api_calculate(request):
    """API endpoint for calculations"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Extract parameters
            annual_consumption = data.get('annual_consumption', 0)
            system_size = data.get('system_size', 0)
            battery_capacity = data.get('battery_capacity', 0)
            electricity_rate = data.get('electricity_rate', 0.15)
            pv_cost_per_kw = data.get('pv_cost_per_kw', 2000)
            battery_cost_per_kwh = data.get('battery_cost_per_kwh', 500)
            
            # Run calculation
            results = quick_calculation(
                annual_consumption=annual_consumption,
                system_size=system_size,
                battery_capacity=battery_capacity,
                electricity_rate=electricity_rate,
                pv_cost_per_kw=pv_cost_per_kw,
                battery_cost_per_kwh=battery_cost_per_kwh
            )
            
            return JsonResponse({
                'success': True,
                'results': results
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Only POST method allowed'
    }, status=405) 