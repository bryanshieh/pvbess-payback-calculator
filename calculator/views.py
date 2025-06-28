from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from .models import EnergyProfile, PVSystem, BESSSystem, FinancialParameters, CalculationResult
from .forms import (EnergyProfileForm, PVSystemForm, BESSSystemForm, 
                   FinancialParametersForm, QuickCalculatorForm)
from .utils import run_complete_calculation, quick_calculation, parse_energy_data_file, get_most_recent_12_months


def home(request):
    """Home page with quick calculator"""
    if request.method == 'POST':
        form = QuickCalculatorForm(request.POST)
        if form.is_valid():
            # Get form data
            annual_consumption = form.cleaned_data['annual_consumption']
            pv_size = form.cleaned_data['pv_size']
            bess_size = form.cleaned_data['bess_size']
            electricity_rate = form.cleaned_data['electricity_rate']
            
            # Run quick calculation
            results = quick_calculation(
                annual_consumption, pv_size, bess_size, electricity_rate
            )
            
            return render(request, 'calculator/quick_results.html', {
                'results': results,
                'form': form
            })
    else:
        form = QuickCalculatorForm()
    
    return render(request, 'calculator/home.html', {'form': form})


def detailed_calculator(request):
    """Detailed calculator with step-by-step input"""
    return render(request, 'calculator/detailed_calculator.html')


@login_required
def energy_profile_form(request):
    """Energy profile form with file upload support"""
    if request.method == 'POST':
        print(f"POST data keys: {list(request.POST.keys())}")
        print(f"FILES keys: {list(request.FILES.keys())}")
        
        form = EnergyProfileForm(request.POST)
        if form.is_valid():
            energy_profile = form.save(commit=False)
            energy_profile.user = request.user
            
            # Handle file upload (either direct upload or AJAX-populated values)
            if 'energy_data_file' in request.FILES:
                # Direct file upload during form submission
                uploaded_file = request.FILES['energy_data_file']
                
                # Validate file size and type
                if uploaded_file.size > 10 * 1024 * 1024:
                    messages.error(request, "File size must be under 10MB.")
                    return render(request, 'calculator/energy_profile_form.html', {'form': form})
                
                allowed_extensions = ['.csv', '.xml']
                file_extension = uploaded_file.name.lower()
                if not any(file_extension.endswith(ext) for ext in allowed_extensions):
                    messages.error(request, "Only CSV and XML files are allowed.")
                    return render(request, 'calculator/energy_profile_form.html', {'form': form})
                
                parsed_data = parse_energy_data_file(uploaded_file)
                
                if parsed_data:
                    # Get the most recent 12 months of data
                    monthly_consumption = get_most_recent_12_months(parsed_data)
                    
                    # Populate form fields with parsed data
                    energy_profile.jan_consumption = monthly_consumption[0]
                    energy_profile.feb_consumption = monthly_consumption[1]
                    energy_profile.mar_consumption = monthly_consumption[2]
                    energy_profile.apr_consumption = monthly_consumption[3]
                    energy_profile.may_consumption = monthly_consumption[4]
                    energy_profile.jun_consumption = monthly_consumption[5]
                    energy_profile.jul_consumption = monthly_consumption[6]
                    energy_profile.aug_consumption = monthly_consumption[7]
                    energy_profile.sep_consumption = monthly_consumption[8]
                    energy_profile.oct_consumption = monthly_consumption[9]
                    energy_profile.nov_consumption = monthly_consumption[10]
                    energy_profile.dec_consumption = monthly_consumption[11]
                    
                    messages.success(request, f"Successfully parsed {len(parsed_data['dates'])} data points from uploaded file.")
                else:
                    messages.error(request, "Could not parse the uploaded file. Please check the file format.")
            else:
                # No file uploaded, but form has monthly consumption data (from AJAX upload)
                # The form validation ensures we have valid monthly data
                messages.success(request, 'Energy profile created from manual entry data.')
            
            energy_profile.save()
            messages.success(request, 'Energy profile created successfully!')
            return redirect('calculator:pv_system_form')
        else:
            # Form is invalid - show validation errors
            print(f"Form errors: {form.errors}")
            messages.error(request, 'Please correct the errors below.')
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = EnergyProfileForm()
    
    return render(request, 'calculator/energy_profile_form.html', {'form': form})


@login_required
def pv_system_form(request):
    """PV system specifications form"""
    if request.method == 'POST':
        form = PVSystemForm(request.POST)
        if form.is_valid():
            pv_system = form.save(commit=False)
            pv_system.user = request.user
            pv_system.save()
            messages.success(request, 'PV system specifications saved!')
            return redirect('calculator:bess_system_form')
    else:
        form = PVSystemForm()
    
    return render(request, 'calculator/pv_system_form.html', {'form': form})


@login_required
def bess_system_form(request):
    """BESS system specifications form"""
    if request.method == 'POST':
        form = BESSSystemForm(request.POST)
        if form.is_valid():
            bess_system = form.save(commit=False)
            bess_system.user = request.user
            bess_system.save()
            messages.success(request, 'BESS system specifications saved!')
            return redirect('calculator:financial_parameters_form')
    else:
        form = BESSSystemForm()
    
    return render(request, 'calculator/bess_system_form.html', {'form': form})


@login_required
def financial_parameters_form(request):
    """Financial parameters form"""
    if request.method == 'POST':
        form = FinancialParametersForm(request.POST)
        if form.is_valid():
            financial_params = form.save(commit=False)
            financial_params.user = request.user
            financial_params.save()
            messages.success(request, 'Financial parameters saved!')
            return redirect('calculator:detailed_calculator')
    else:
        form = FinancialParametersForm()
    
    return render(request, 'calculator/financial_parameters_form.html', {'form': form})


@login_required
def detailed_calculator(request):
    """Detailed calculator with all parameters"""
    # Get the most recent data for each component
    try:
        energy_profile = EnergyProfile.objects.filter(user=request.user).latest('created_at')
        pv_system = PVSystem.objects.filter(user=request.user).latest('created_at')
        bess_system = BESSSystem.objects.filter(user=request.user).latest('created_at')
        financial_params = FinancialParameters.objects.filter(user=request.user).latest('created_at')
    except (EnergyProfile.DoesNotExist, PVSystem.DoesNotExist, 
            BESSSystem.DoesNotExist, FinancialParameters.DoesNotExist):
        messages.error(request, 'Please complete all previous steps first.')
        return redirect('calculator:energy_profile_form')
    
    # Run calculation
    results = run_complete_calculation(energy_profile, pv_system, bess_system, financial_params)
    
    # Save calculation result
    calculation_result = CalculationResult.objects.create(
        user=request.user,
        name=f"Calculation {energy_profile.name}",
        energy_profile=energy_profile,
        pv_system=pv_system,
        bess_system=bess_system,
        financial_params=financial_params,
        total_system_cost=results['financial_results']['total_system_cost'],
        annual_savings=results['financial_results']['annual_savings'],
        payback_period_years=results['financial_results']['payback_period_years'],
        npv_25_years=results['financial_results']['npv_25_years'],
        irr_percent=results['financial_results']['irr_percent']
    )
    
    # Store detailed results as JSON
    calculation_result.set_monthly_results(results['monthly_results'])
    calculation_result.set_annual_results(results['financial_results'])
    calculation_result.save()
    
    return render(request, 'calculator/detailed_calculator.html', {
        'results': results,
        'energy_profile': energy_profile,
        'pv_system': pv_system,
        'bess_system': bess_system,
        'financial_params': financial_params
    })


def about(request):
    """About page"""
    return render(request, 'calculator/about.html')


def help_page(request):
    """Help page"""
    return render(request, 'calculator/help.html')


@csrf_exempt
@require_http_methods(["POST"])
def ajax_file_upload(request):
    """AJAX endpoint for file upload processing"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file uploaded'}, status=400)
        
        uploaded_file = request.FILES['file']
        parsed_data = parse_energy_data_file(uploaded_file)
        
        if parsed_data:
            monthly_consumption = get_most_recent_12_months(parsed_data)
            return JsonResponse({
                'success': True,
                'monthly_data': monthly_consumption,
                'total_records': len(parsed_data['dates']),
                'message': f"Successfully parsed {len(parsed_data['dates'])} data points"
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Could not parse the uploaded file. Please check the file format.'
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error processing file: {str(e)}'
        }, status=500)


@login_required
def my_calculations(request):
    """View user's calculation history"""
    calculations = CalculationResult.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'calculator/my_calculations.html', {
        'calculations': calculations
    })


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