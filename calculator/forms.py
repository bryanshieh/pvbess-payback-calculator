from django import forms
from .models import EnergyProfile, PVSystem, BESSSystem, FinancialParameters


class EnergyProfileForm(forms.ModelForm):
    """Form for energy profile data entry"""
    
    class Meta:
        model = EnergyProfile
        fields = [
            'name', 'jan_consumption', 'feb_consumption', 
            'mar_consumption', 'apr_consumption', 'may_consumption', 'jun_consumption',
            'jul_consumption', 'aug_consumption', 'sep_consumption', 'oct_consumption',
            'nov_consumption', 'dec_consumption', 'peak_demand'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'jan_consumption': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'feb_consumption': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'mar_consumption': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'apr_consumption': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'may_consumption': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'jun_consumption': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'jul_consumption': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'aug_consumption': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sep_consumption': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'oct_consumption': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'nov_consumption': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'dec_consumption': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'peak_demand': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def clean(self):
        """Validate that monthly data is provided"""
        cleaned_data = super().clean()
        
        # Check if monthly consumption data is provided
        monthly_fields = [
            'jan_consumption', 'feb_consumption', 'mar_consumption', 'apr_consumption',
            'may_consumption', 'jun_consumption', 'jul_consumption', 'aug_consumption',
            'sep_consumption', 'oct_consumption', 'nov_consumption', 'dec_consumption'
        ]
        
        has_monthly_data = False
        total_consumption = 0
        
        for field in monthly_fields:
            value = cleaned_data.get(field)
            if value is not None:
                try:
                    # Convert to float and check if positive
                    float_value = float(value)
                    if float_value > 0:
                        has_monthly_data = True
                        total_consumption += float_value
                except (ValueError, TypeError):
                    # Skip invalid values
                    pass
        
        # Also check if name is provided
        name = cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError("Please provide a profile name.")
        
        if not has_monthly_data:
            raise forms.ValidationError(
                "Please enter monthly consumption data manually."
            )
        
        return cleaned_data


class PVSystemForm(forms.ModelForm):
    """Form for PV system specifications"""
    
    class Meta:
        model = PVSystem
        fields = [
            'name', 'system_size_kw', 'panel_efficiency', 'inverter_efficiency',
            'system_efficiency', 'latitude', 'longitude', 'tilt_angle', 'azimuth',
            'annual_degradation'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'system_size_kw': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'panel_efficiency': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0', 'max': '1'}),
            'inverter_efficiency': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0', 'max': '1'}),
            'system_efficiency': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0', 'max': '1'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'tilt_angle': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'max': '90'}),
            'azimuth': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'max': '360'}),
            'annual_degradation': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0', 'max': '1'}),
        }
        labels = {
            'name': 'System Name',
            'system_size_kw': 'System Size (kW)',
            'panel_efficiency': 'Panel Efficiency',
            'inverter_efficiency': 'Inverter Efficiency',
            'system_efficiency': 'Overall System Efficiency',
            'latitude': 'Latitude (°)',
            'longitude': 'Longitude (°)',
            'tilt_angle': 'Tilt Angle (°)',
            'azimuth': 'Azimuth (°)',
            'annual_degradation': 'Annual Degradation Rate',
        }


class BESSSystemForm(forms.ModelForm):
    """Form for BESS system specifications"""
    
    class Meta:
        model = BESSSystem
        fields = [
            'name', 'capacity_kwh', 'usable_capacity_kwh', 'max_charge_rate_kw',
            'max_discharge_rate_kw', 'round_trip_efficiency', 'charge_efficiency',
            'discharge_efficiency', 'control_strategy', 'min_soc', 'max_soc'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'capacity_kwh': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'usable_capacity_kwh': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_charge_rate_kw': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_discharge_rate_kw': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'round_trip_efficiency': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0', 'max': '1'}),
            'charge_efficiency': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0', 'max': '1'}),
            'discharge_efficiency': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0', 'max': '1'}),
            'control_strategy': forms.Select(attrs={'class': 'form-control'}),
            'min_soc': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '1'}),
            'max_soc': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '1'}),
        }
        labels = {
            'name': 'System Name',
            'capacity_kwh': 'Total Capacity (kWh)',
            'usable_capacity_kwh': 'Usable Capacity (kWh)',
            'max_charge_rate_kw': 'Max Charge Rate (kW)',
            'max_discharge_rate_kw': 'Max Discharge Rate (kW)',
            'round_trip_efficiency': 'Round-trip Efficiency',
            'charge_efficiency': 'Charge Efficiency',
            'discharge_efficiency': 'Discharge Efficiency',
            'control_strategy': 'Control Strategy',
            'min_soc': 'Minimum State of Charge',
            'max_soc': 'Maximum State of Charge',
        }


class FinancialParametersForm(forms.ModelForm):
    """Form for financial parameters"""
    
    class Meta:
        model = FinancialParameters
        fields = [
            'name', 'pv_cost_per_kw', 'bess_cost_per_kwh', 'installation_cost_percent',
            'electricity_rate', 'peak_rate', 'off_peak_rate', 'federal_tax_credit',
            'state_incentive', 'discount_rate', 'electricity_inflation', 'system_lifetime'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'pv_cost_per_kw': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'bess_cost_per_kwh': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'installation_cost_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0', 'max': '1'}),
            'electricity_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'peak_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'off_peak_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'federal_tax_credit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0', 'max': '1'}),
            'state_incentive': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'discount_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0', 'max': '1'}),
            'electricity_inflation': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0', 'max': '1'}),
            'system_lifetime': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '50'}),
        }
        labels = {
            'name': 'Parameter Set Name',
            'pv_cost_per_kw': 'PV Cost per kW ($)',
            'bess_cost_per_kwh': 'BESS Cost per kWh ($)',
            'installation_cost_percent': 'Installation Cost (%)',
            'electricity_rate': 'Electricity Rate ($/kWh)',
            'peak_rate': 'Peak Rate ($/kWh)',
            'off_peak_rate': 'Off-peak Rate ($/kWh)',
            'federal_tax_credit': 'Federal Tax Credit',
            'state_incentive': 'State Incentive ($/kWh)',
            'discount_rate': 'Discount Rate',
            'electricity_inflation': 'Electricity Rate Inflation',
            'system_lifetime': 'System Lifetime (years)',
        }


class QuickCalculatorForm(forms.Form):
    """Form for quick calculator"""
    annual_consumption = forms.FloatField(
        label="Annual Energy Consumption (kWh)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    pv_size = forms.FloatField(
        label="PV System Size (kW)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    bess_size = forms.FloatField(
        label="BESS Capacity (kWh)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    electricity_rate = forms.FloatField(
        label="Electricity Rate ($/kWh)",
        initial=0.15,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'})
    ) 