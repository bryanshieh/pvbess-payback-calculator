import math
import numpy as np
from typing import Dict, List, Tuple


def calculate_solar_irradiance(latitude: float, longitude: float, month: int) -> float:
    """
    Calculate average daily solar irradiance for a given location and month.
    This is a simplified model - in production, you'd use more sophisticated solar data.
    """
    # Simplified solar irradiance model based on latitude and season
    # Peak summer irradiance (June in Northern Hemisphere)
    peak_irradiance = 6.0  # kWh/m²/day
    
    # Seasonal variation (approximate)
    seasonal_factors = [
        0.4,  # January
        0.5,  # February
        0.7,  # March
        0.9,  # April
        1.0,  # May
        1.1,  # June
        1.1,  # July
        1.0,  # August
        0.8,  # September
        0.6,  # October
        0.4,  # November
        0.3,  # December
    ]
    
    # Latitude adjustment
    lat_factor = 1.0 - abs(latitude - 35) / 90  # Optimal around 35° latitude
    
    return peak_irradiance * seasonal_factors[month - 1] * lat_factor


def calculate_pv_generation(system_size_kw: float, irradiance: float, 
                          system_efficiency: float, days_in_month: int) -> float:
    """Calculate monthly PV generation in kWh"""
    return system_size_kw * irradiance * system_efficiency * days_in_month


def simulate_battery_operation(monthly_generation: List[float], 
                             monthly_consumption: List[float],
                             battery_capacity: float, usable_capacity: float,
                             charge_efficiency: float, discharge_efficiency: float,
                             min_soc: float, max_soc: float) -> Dict:
    """
    Simulate battery operation for a year.
    Returns battery state, grid interaction, and self-consumption data.
    """
    battery_state = []
    grid_import = []
    grid_export = []
    self_consumption = []
    
    # Initialize battery at 50% SOC
    current_soc = 0.5
    
    for month in range(12):
        generation = monthly_generation[month]
        consumption = monthly_consumption[month]
        
        # Daily averages for the month
        daily_generation = generation / 30
        daily_consumption = consumption / 30
        
        # Hourly simulation (simplified - 12 hours of generation, 24 hours of consumption)
        daily_self_consumption = 0
        daily_grid_import = 0
        daily_grid_export = 0
        
        # Solar generation period (6 AM to 6 PM)
        for hour in range(12):
            hourly_generation = daily_generation / 12
            hourly_consumption = daily_consumption / 24
            
            # First, use generation for immediate consumption
            if hourly_generation >= hourly_consumption:
                daily_self_consumption += hourly_consumption
                excess_generation = hourly_generation - hourly_consumption
                
                # Try to charge battery with excess
                if current_soc < max_soc:
                    charge_amount = min(excess_generation, 
                                      (max_soc - current_soc) * usable_capacity / charge_efficiency)
                    current_soc += charge_amount * charge_efficiency / usable_capacity
                    excess_generation -= charge_amount
                
                # Export remaining excess to grid
                daily_grid_export += excess_generation
            else:
                daily_self_consumption += hourly_generation
                shortfall = hourly_consumption - hourly_generation
                
                # Try to discharge battery
                if current_soc > min_soc:
                    discharge_amount = min(shortfall, 
                                         (current_soc - min_soc) * usable_capacity * discharge_efficiency)
                    current_soc -= discharge_amount / (usable_capacity * discharge_efficiency)
                    shortfall -= discharge_amount
                
                # Import from grid for remaining shortfall
                daily_grid_import += shortfall
        
        # Night period (6 PM to 6 AM)
        for hour in range(12):
            hourly_consumption = daily_consumption / 24
            
            # Try to discharge battery
            if current_soc > min_soc:
                discharge_amount = min(hourly_consumption, 
                                     (current_soc - min_soc) * usable_capacity * discharge_efficiency)
                current_soc -= discharge_amount / (usable_capacity * discharge_efficiency)
                hourly_consumption -= discharge_amount
            
            # Import from grid for remaining consumption
            daily_grid_import += hourly_consumption
        
        # Monthly totals
        battery_state.append(current_soc)
        grid_import.append(daily_grid_import * 30)
        grid_export.append(daily_grid_export * 30)
        self_consumption.append(daily_self_consumption * 30)
    
    return {
        'battery_state': battery_state,
        'grid_import': grid_import,
        'grid_export': grid_export,
        'self_consumption': self_consumption
    }


def calculate_financial_metrics(system_cost: float, annual_savings: float,
                              discount_rate: float, system_lifetime: int,
                              electricity_inflation: float) -> Dict:
    """Calculate financial metrics including payback period, NPV, and IRR"""
    
    # Simple payback period
    payback_period = system_cost / annual_savings if annual_savings > 0 else float('inf')
    
    # NPV calculation
    npv = -system_cost
    for year in range(1, system_lifetime + 1):
        # Apply degradation to savings (assuming 0.5% annual degradation)
        degraded_savings = annual_savings * (1 - 0.005) ** (year - 1)
        # Apply electricity rate inflation
        inflated_savings = degraded_savings * (1 + electricity_inflation) ** (year - 1)
        # Discount to present value
        npv += inflated_savings / (1 + discount_rate) ** year
    
    # IRR calculation (simplified)
    # For IRR, we need to find the discount rate that makes NPV = 0
    # This is a simplified approximation
    if npv > 0:
        # If NPV is positive, IRR is higher than discount rate
        irr = discount_rate + (npv / system_cost) * 0.1
    else:
        irr = discount_rate * 0.5  # Conservative estimate
    
    return {
        'payback_period': payback_period,
        'npv': npv,
        'irr': irr,
        'annual_savings': annual_savings,
        'total_savings_25_years': npv + system_cost
    }


def calculate_system_cost(pv_size: float, battery_capacity: float,
                         pv_cost_per_kw: float, battery_cost_per_kwh: float,
                         installation_cost_percent: float) -> float:
    """Calculate total system cost including installation"""
    pv_cost = pv_size * pv_cost_per_kw
    battery_cost = battery_capacity * battery_cost_per_kwh
    total_hardware_cost = pv_cost + battery_cost
    installation_cost = total_hardware_cost * installation_cost_percent
    return total_hardware_cost + installation_cost


def calculate_annual_savings(grid_import: List[float], grid_export: List[float],
                           electricity_rate: float, peak_rate: float = None,
                           off_peak_rate: float = None, export_rate: float = None) -> float:
    """Calculate annual electricity cost savings"""
    
    if export_rate is None:
        export_rate = electricity_rate * 0.7  # Typical export rate is 70% of import rate
    
    # Calculate costs without system
    total_import_cost = sum(grid_import) * electricity_rate
    total_export_credit = sum(grid_export) * export_rate
    
    # Net cost with system
    net_cost_with_system = total_import_cost - total_export_credit
    
    return net_cost_with_system


def run_complete_calculation(energy_profile, pv_system, bess_system, financial_params):
    """
    Run complete PV + BESS calculation and return results
    """
    # Get monthly consumption
    monthly_consumption = energy_profile.get_monthly_consumption()
    
    # Calculate monthly PV generation
    monthly_generation = []
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    
    for month in range(12):
        irradiance = calculate_solar_irradiance(
            pv_system.latitude, pv_system.longitude, month + 1
        )
        generation = calculate_pv_generation(
            pv_system.system_size_kw, irradiance, 
            pv_system.system_efficiency, days_in_month[month]
        )
        monthly_generation.append(generation)
    
    # Simulate battery operation
    battery_results = simulate_battery_operation(
        monthly_generation, monthly_consumption,
        bess_system.capacity_kwh, bess_system.usable_capacity_kwh,
        bess_system.charge_efficiency, bess_system.discharge_efficiency,
        bess_system.min_soc, bess_system.max_soc
    )
    
    # Calculate system cost
    system_cost = calculate_system_cost(
        pv_system.system_size_kw, bess_system.capacity_kwh,
        financial_params.pv_cost_per_kw, financial_params.bess_cost_per_kwh,
        financial_params.installation_cost_percent
    )
    
    # Apply federal tax credit
    system_cost_after_tax_credit = system_cost * (1 - financial_params.federal_tax_credit)
    
    # Calculate annual savings
    annual_savings = calculate_annual_savings(
        battery_results['grid_import'], battery_results['grid_export'],
        financial_params.electricity_rate, financial_params.peak_rate,
        financial_params.off_peak_rate
    )
    
    # Calculate financial metrics
    financial_metrics = calculate_financial_metrics(
        system_cost_after_tax_credit, annual_savings,
        financial_params.discount_rate, financial_params.system_lifetime,
        financial_params.electricity_inflation
    )
    
    # Prepare results
    results = {
        'monthly_generation': monthly_generation,
        'monthly_consumption': monthly_consumption,
        'battery_results': battery_results,
        'system_cost': system_cost,
        'system_cost_after_tax_credit': system_cost_after_tax_credit,
        'annual_savings': annual_savings,
        'financial_metrics': financial_metrics,
        'total_annual_generation': sum(monthly_generation),
        'total_annual_consumption': sum(monthly_consumption),
        'self_consumption_rate': sum(battery_results['self_consumption']) / sum(monthly_generation) if sum(monthly_generation) > 0 else 0
    }
    
    return results


def quick_calculation(annual_consumption: float, system_size: float, 
                     battery_capacity: float, electricity_rate: float,
                     pv_cost_per_kw: float = 2000, battery_cost_per_kwh: float = 500) -> Dict:
    """
    Simplified calculation for quick estimates
    """
    # Estimate monthly consumption (evenly distributed)
    monthly_consumption = [annual_consumption / 12] * 12
    
    # Estimate monthly generation (simplified)
    monthly_generation = []
    generation_factors = [0.4, 0.5, 0.7, 0.9, 1.0, 1.1, 1.1, 1.0, 0.8, 0.6, 0.4, 0.3]
    
    for factor in generation_factors:
        # Assume 4.5 peak sun hours per day average
        daily_generation = system_size * 4.5 * factor
        monthly_generation.append(daily_generation * 30)
    
    # Simplified battery simulation
    total_generation = sum(monthly_generation)
    total_consumption = sum(monthly_consumption)
    
    # Assume 70% self-consumption rate
    self_consumption = min(total_generation, total_consumption) * 0.7
    grid_export = max(0, total_generation - self_consumption)
    grid_import = max(0, total_consumption - self_consumption)
    
    # Calculate costs
    system_cost = system_size * pv_cost_per_kw + battery_capacity * battery_cost_per_kwh
    system_cost_after_tax_credit = system_cost * 0.7  # 30% federal tax credit
    
    # Calculate savings
    annual_savings = (grid_import * electricity_rate) - (grid_export * electricity_rate * 0.7)
    
    # Calculate payback period
    payback_period = system_cost_after_tax_credit / annual_savings if annual_savings > 0 else float('inf')
    
    return {
        'system_cost': system_cost,
        'system_cost_after_tax_credit': system_cost_after_tax_credit,
        'annual_savings': annual_savings,
        'payback_period': payback_period,
        'total_generation': total_generation,
        'self_consumption': self_consumption,
        'grid_export': grid_export,
        'grid_import': grid_import
    } 