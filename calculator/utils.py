import math
import csv
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Tuple, Optional


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
    Run complete calculation for PV + BESS system.
    Returns detailed results including monthly breakdowns.
    """
    # Get monthly consumption data
    monthly_consumption = energy_profile.get_monthly_consumption()
    
    # Calculate PV production
    monthly_pv_production = calculate_pv_production(
        monthly_consumption, pv_system.system_size_kw,
        pv_system.latitude, pv_system.longitude,
        pv_system.tilt_angle, pv_system.azimuth,
        pv_system.system_efficiency
    )
    
    # Calculate BESS operation
    bess_results = calculate_bess_operation(
        monthly_consumption, monthly_pv_production,
        bess_system.capacity_kwh, bess_system.usable_capacity_kwh,
        bess_system.max_charge_rate_kw, bess_system.max_discharge_rate_kw,
        bess_system.round_trip_efficiency, bess_system.control_strategy
    )
    
    # Calculate financial metrics
    financial_results = calculate_financial_metrics(
        pv_system.system_size_kw, bess_system.capacity_kwh,
        bess_results['total_savings'] * financial_params.electricity_rate,
        financial_params.pv_cost_per_kw, financial_params.bess_cost_per_kwh,
        financial_params.installation_cost_percent, financial_params.federal_tax_credit,
        financial_params.state_incentive, financial_params.discount_rate,
        financial_params.electricity_inflation, financial_params.system_lifetime
    )
    
    # Prepare detailed monthly results
    monthly_results = []
    for i in range(12):
        monthly_results.append({
            'month': i + 1,
            'consumption': monthly_consumption[i],
            'pv_production': monthly_pv_production[i],
            'bess_energy': bess_results['monthly_bess_energy'][i],
            'grid_energy': bess_results['monthly_grid_energy'][i],
            'savings': bess_results['monthly_savings'][i]
        })
    
    return {
        'monthly_results': monthly_results,
        'financial_results': financial_results,
        'bess_results': bess_results,
        'total_consumption': sum(monthly_consumption),
        'total_pv_production': sum(monthly_pv_production),
        'annual_savings': bess_results['total_savings'] * financial_params.electricity_rate
    }


def quick_calculation(annual_consumption: float, system_size: float, 
                     battery_capacity: float, electricity_rate: float,
                     pv_cost_per_kw: float = 2000, battery_cost_per_kwh: float = 500) -> Dict:
    """
    Quick calculation for basic payback period estimation.
    Uses simplified assumptions for rapid results.
    """
    # Simplified assumptions
    system_efficiency = 0.75
    battery_efficiency = 0.90
    installation_cost_percent = 0.10
    
    # Calculate annual PV production (simplified)
    # Assume 4.5 kWh/kW/day average
    daily_production = system_size * 4.5 * system_efficiency
    annual_pv_production = daily_production * 365
    
    # Calculate self-consumption (simplified)
    # Assume 70% of PV production is used directly
    direct_use = min(annual_consumption, annual_pv_production * 0.7)
    excess_pv = max(0, annual_pv_production - direct_use)
    
    # Battery operation (simplified)
    # Assume battery can store excess PV and discharge when needed
    battery_cycles = min(excess_pv, battery_capacity * 365 * 0.8)  # 80% utilization
    battery_savings = battery_cycles * battery_efficiency
    
    # Total energy savings
    total_savings = direct_use + battery_savings
    annual_cost_savings = total_savings * electricity_rate
    
    # System cost
    total_cost = calculate_system_cost(
        system_size, battery_capacity,
        pv_cost_per_kw, battery_cost_per_kwh,
        installation_cost_percent
    )
    
    # Apply federal tax credit (30%)
    federal_credit = total_cost * 0.30
    net_cost = total_cost - federal_credit
    
    # Payback period
    if annual_cost_savings > 0:
        payback_period = net_cost / annual_cost_savings
    else:
        payback_period = 999999  # Use large number instead of infinity
    
    return {
        'payback_period_years': payback_period,
        'total_system_cost': total_cost,
        'net_system_cost': net_cost,
        'annual_savings': annual_cost_savings,
        'annual_pv_production': annual_pv_production,
        'self_consumption': direct_use,
        'battery_savings': battery_savings
    }


def calculate_pv_production(monthly_consumption: List[float], pv_size_kw: float, 
                          latitude: float, longitude: float, tilt_angle: float = 30, 
                          azimuth: float = 180, system_efficiency: float = 0.75) -> List[float]:
    """
    Calculate monthly PV production based on location and system parameters.
    Uses simplified solar radiation model.
    """
    # Monthly solar radiation data (kWh/m²/day) for different latitudes
    # This is a simplified model - in practice, you'd use more sophisticated solar data
    solar_radiation = {
        'low_lat': [4.5, 5.2, 5.8, 6.2, 6.5, 6.8, 6.9, 6.7, 6.2, 5.5, 4.8, 4.2],  # 0-30°
        'mid_lat': [3.8, 4.5, 5.2, 5.8, 6.2, 6.5, 6.6, 6.4, 5.8, 5.0, 4.2, 3.5],  # 30-45°
        'high_lat': [2.8, 3.5, 4.2, 5.0, 5.8, 6.2, 6.3, 6.0, 5.2, 4.2, 3.2, 2.5]  # 45-60°
    }
    
    # Determine latitude band
    abs_lat = abs(latitude)
    if abs_lat <= 30:
        radiation = solar_radiation['low_lat']
    elif abs_lat <= 45:
        radiation = solar_radiation['mid_lat']
    else:
        radiation = solar_radiation['high_lat']
    
    # Days per month
    days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    
    # Calculate monthly production
    monthly_production = []
    for i, (rad, days) in enumerate(zip(radiation, days_per_month)):
        # Basic tilt and azimuth correction (simplified)
        tilt_factor = 1.0 + 0.1 * (tilt_angle - 30) / 30  # Simple tilt correction
        azimuth_factor = 1.0 - 0.1 * abs(azimuth - 180) / 180  # Simple azimuth correction
        
        # Calculate production
        daily_production = rad * tilt_factor * azimuth_factor * system_efficiency
        monthly_production.append(daily_production * days * pv_size_kw)
    
    return monthly_production


def calculate_bess_operation(monthly_consumption: List[float], monthly_pv_production: List[float],
                           bess_capacity_kwh: float, usable_capacity_kwh: float,
                           max_charge_rate_kw: float, max_discharge_rate_kw: float,
                           round_trip_efficiency: float = 0.90,
                           control_strategy: str = 'self_consumption') -> Dict:
    """
    Calculate BESS operation and energy savings.
    """
    monthly_savings = []
    monthly_bess_energy = []
    monthly_grid_energy = []
    
    # Time-of-use rates (simplified - could be more sophisticated)
    peak_hours = 6  # Assume 6 peak hours per day
    off_peak_hours = 18
    
    for i, (consumption, pv_production) in enumerate(zip(monthly_consumption, monthly_pv_production)):
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][i]
        
        # Daily averages
        daily_consumption = consumption / days_in_month
        daily_pv_production = pv_production / days_in_month
        
        if control_strategy == 'self_consumption':
            # Simple self-consumption optimization
            # Use PV production directly, store excess in BESS, discharge when needed
            excess_pv = max(0, daily_pv_production - daily_consumption)
            
            # Calculate BESS operation
            bess_charge = min(excess_pv, max_charge_rate_kw * 24, usable_capacity_kwh)
            bess_discharge = min(daily_consumption - daily_pv_production, 
                               max_discharge_rate_kw * 24, bess_charge * round_trip_efficiency)
            
            # Calculate grid energy and savings
            grid_energy = daily_consumption - daily_pv_production - bess_discharge
            savings = daily_consumption - grid_energy
            
        elif control_strategy == 'time_of_use':
            # Time-of-use optimization
            # Charge during off-peak, discharge during peak
            peak_consumption = daily_consumption * 0.4  # Assume 40% during peak
            off_peak_consumption = daily_consumption * 0.6
            
            # BESS operation for TOU
            bess_charge = min(max_charge_rate_kw * off_peak_hours, usable_capacity_kwh)
            bess_discharge = min(peak_consumption, max_discharge_rate_kw * peak_hours, 
                               bess_charge * round_trip_efficiency)
            
            grid_energy = off_peak_consumption + (peak_consumption - bess_discharge)
            savings = daily_consumption - grid_energy
            
        else:  # peak_shaving
            # Peak demand shaving
            peak_demand = daily_consumption / 24  # Simplified peak calculation
            target_peak = peak_demand * 0.8  # Reduce peak by 20%
            
            bess_discharge = min(peak_demand - target_peak, max_discharge_rate_kw * 24)
            bess_charge = min(daily_pv_production, max_charge_rate_kw * 24, usable_capacity_kwh)
            
            grid_energy = daily_consumption - daily_pv_production - bess_discharge
            savings = daily_consumption - grid_energy
        
        monthly_savings.append(savings * days_in_month)
        monthly_bess_energy.append((bess_charge + bess_discharge) * days_in_month / 2)
        monthly_grid_energy.append(grid_energy * days_in_month)
    
    return {
        'monthly_savings': monthly_savings,
        'monthly_bess_energy': monthly_bess_energy,
        'monthly_grid_energy': monthly_grid_energy,
        'total_savings': sum(monthly_savings)
    }


def calculate_financial_metrics(pv_size_kw: float, bess_capacity_kwh: float,
                              annual_savings: float, pv_cost_per_kw: float = 2000,
                              bess_cost_per_kwh: float = 500, installation_cost_percent: float = 0.10,
                              federal_tax_credit: float = 0.30, state_incentive: float = 0.0,
                              discount_rate: float = 0.05, electricity_inflation: float = 0.03,
                              system_lifetime: int = 25) -> Dict:
    """
    Calculate financial metrics including payback period, NPV, and IRR.
    """
    # Calculate total system cost
    pv_cost = pv_size_kw * pv_cost_per_kw
    bess_cost = bess_capacity_kwh * bess_cost_per_kwh
    total_hardware_cost = pv_cost + bess_cost
    installation_cost = total_hardware_cost * installation_cost_percent
    total_system_cost = total_hardware_cost + installation_cost
    
    # Apply incentives
    federal_credit = total_system_cost * federal_tax_credit
    state_credit = bess_capacity_kwh * state_incentive
    net_system_cost = total_system_cost - federal_credit - state_credit
    
    # Calculate payback period
    if annual_savings > 0:
        payback_period = net_system_cost / annual_savings
    else:
        payback_period = 999999  # Use large number instead of infinity
    
    # Calculate NPV over system lifetime
    npv = -net_system_cost
    for year in range(1, system_lifetime + 1):
        # Apply electricity inflation to savings
        inflated_savings = annual_savings * (1 + electricity_inflation) ** (year - 1)
        # Discount future savings
        discounted_savings = inflated_savings / (1 + discount_rate) ** year
        npv += discounted_savings
    
    # Calculate IRR (simplified - in practice, you'd use a more sophisticated method)
    if npv > 0:
        # Simple IRR approximation
        irr = (npv / net_system_cost) ** (1 / system_lifetime) - 1
        irr_percent = irr * 100
    else:
        irr_percent = -100  # Indicates negative return
    
    return {
        'total_system_cost': total_system_cost,
        'net_system_cost': net_system_cost,
        'annual_savings': annual_savings,
        'payback_period_years': payback_period,
        'npv_25_years': npv,
        'irr_percent': irr_percent,
        'federal_credit': federal_credit,
        'state_credit': state_credit
    }


def parse_energy_data_file(file) -> Optional[Dict[str, List[float]]]:
    """
    Parse uploaded CSV or XML file to extract monthly energy consumption data.
    Returns a dictionary with monthly consumption data or None if parsing fails.
    """
    try:
        file_extension = file.name.lower()
        
        if file_extension.endswith('.csv'):
            return parse_csv_energy_data(file)
        elif file_extension.endswith('.xml'):
            return parse_xml_energy_data(file)
        else:
            return None
            
    except Exception as e:
        print(f"Error parsing file: {e}")
        return None


def parse_csv_energy_data(file) -> Optional[Dict[str, List[float]]]:
    """
    Parse CSV file for energy consumption data.
    Handles SCE format with irregular headers and interval data.
    """
    try:
        # Read CSV content
        content = file.read().decode('utf-8')
        lines = content.splitlines()
        
        # Initialize monthly data
        monthly_data = {
            'consumption': [0.0] * 12,
            'dates': [],
            'values': []
        }
        
        # Find the data header row (look for "Date" column)
        header_row_index = None
        for i, line in enumerate(lines):
            if 'Date' in line and ('Delivered' in line or 'Energy' in line):
                header_row_index = i
                break
        
        if header_row_index is None:
            return None
        
        # Parse the header to find column indices
        header_line = lines[header_row_index]
        header_reader = csv.reader([header_line])
        headers = next(header_reader)
        
        # Find relevant columns
        date_col_index = None
        delivered_col_index = None
        
        for i, header in enumerate(headers):
            header_lower = header.lower().strip()
            if 'date' in header_lower:
                date_col_index = i
            elif 'delivered' in header_lower:
                delivered_col_index = i
        
        if date_col_index is None or delivered_col_index is None:
            return None
        
        # Process data rows
        for line in lines[header_row_index + 1:]:
            if not line.strip():
                continue
                
            try:
                # Parse CSV row
                row_reader = csv.reader([line])
                row = next(row_reader)
                
                if len(row) <= max(date_col_index, delivered_col_index):
                    continue
                
                date_str = row[date_col_index].strip().strip('"')
                delivered_str = row[delivered_col_index].strip().strip('"')
                
                # Parse date (handle SCE format: "06/27/2022")
                try:
                    date_obj = datetime.strptime(date_str, '%m/%d/%Y')
                    month = date_obj.month - 1  # Convert to 0-based index
                except ValueError:
                    continue
                
                # Parse delivered energy value (convert Wh to kWh)
                try:
                    delivered_value = float(delivered_str.replace(',', '')) / 1000.0
                    monthly_data['consumption'][month] += delivered_value
                    monthly_data['dates'].append(date_str)
                    monthly_data['values'].append(delivered_value)
                except ValueError:
                    continue
                    
            except Exception:
                continue
        
        # Check if we have data
        if sum(monthly_data['consumption']) > 0:
            return monthly_data
        else:
            return None
            
    except Exception as e:
        print(f"Error parsing CSV: {e}")
        return None


def parse_xml_energy_data(file) -> Optional[Dict[str, List[float]]]:
    """
    Parse XML file for energy consumption data.
    Handles Green Button XML format (SCE standard).
    """
    try:
        # Read XML content
        content = file.read().decode('utf-8')
        root = ET.fromstring(content)
        
        # Initialize monthly data
        monthly_data = {
            'consumption': [0.0] * 12,
            'dates': [],
            'values': []
        }
        
        # Define namespaces for Green Button XML
        namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'espi': 'http://naesb.org/espi'
        }
        
        # Find IntervalBlock entries (these contain the actual usage data)
        interval_blocks = root.findall('.//espi:IntervalBlock', namespaces)
        
        for interval_block in interval_blocks:
            try:
                # Find interval readings
                intervals = interval_block.findall('.//espi:IntervalReading', namespaces)
                
                for interval in intervals:
                    # Get the time period
                    time_period = interval.find('.//espi:timePeriod', namespaces)
                    if time_period is None:
                        continue
                    
                    start_time = time_period.find('.//espi:start', namespaces)
                    if start_time is None or start_time.text is None:
                        continue
                    
                    # Parse start time (Unix timestamp)
                    try:
                        start_timestamp = int(start_time.text)
                        date_obj = datetime.fromtimestamp(start_timestamp)
                        month = date_obj.month - 1  # Convert to 0-based index
                    except (ValueError, TypeError):
                        continue
                    
                    # Get the value
                    value_elem = interval.find('.//espi:value', namespaces)
                    if value_elem is None or value_elem.text is None:
                        continue
                    
                    try:
                        value = float(value_elem.text) / 1000.0  # Wh to kWh
                        monthly_data['consumption'][month] += value
                        monthly_data['dates'].append(date_obj.strftime('%Y-%m-%d'))
                        monthly_data['values'].append(value)
                    except ValueError:
                        continue
                        
            except Exception:
                continue
        
        # Check if we have data
        if sum(monthly_data['consumption']) > 0:
            return monthly_data
        else:
            return None
            
    except Exception as e:
        print(f"Error parsing XML: {e}")
        return None


def get_most_recent_12_months(parsed_data: Dict[str, List[float]]) -> List[float]:
    """
    Extract the most recent 12 months of data from parsed file data.
    If more than 12 months are provided, use the most recent 12.
    """
    if not parsed_data or 'consumption' not in parsed_data:
        return [0.0] * 12
    
    consumption = parsed_data['consumption']
    
    # If we have exactly 12 months, return as is
    if len(consumption) == 12:
        return consumption
    
    # If we have more than 12 months, take the most recent 12
    if len(consumption) > 12:
        return consumption[-12:]
    
    # If we have less than 12 months, pad with zeros
    while len(consumption) < 12:
        consumption.append(0.0)
    
    return consumption[:12] 