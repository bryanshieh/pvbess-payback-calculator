from django.db import models
from django.contrib.auth.models import User
import json


class EnergyProfile(models.Model):
    """Model to store user's energy consumption profile"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # File upload for energy data
    energy_data_file = models.FileField(
        upload_to='energy_data/',
        null=True,
        blank=True,
        help_text="Upload CSV or XML file with monthly energy consumption data"
    )
    
    # Monthly energy consumption (kWh)
    jan_consumption = models.FloatField(default=0)
    feb_consumption = models.FloatField(default=0)
    mar_consumption = models.FloatField(default=0)
    apr_consumption = models.FloatField(default=0)
    may_consumption = models.FloatField(default=0)
    jun_consumption = models.FloatField(default=0)
    jul_consumption = models.FloatField(default=0)
    aug_consumption = models.FloatField(default=0)
    sep_consumption = models.FloatField(default=0)
    oct_consumption = models.FloatField(default=0)
    nov_consumption = models.FloatField(default=0)
    dec_consumption = models.FloatField(default=0)
    
    # Annual totals
    annual_consumption = models.FloatField(default=0)
    peak_demand = models.FloatField(default=0)  # kW
    
    def save(self, *args, **kwargs):
        # Calculate annual consumption
        self.annual_consumption = sum([
            self.jan_consumption, self.feb_consumption, self.mar_consumption,
            self.apr_consumption, self.may_consumption, self.jun_consumption,
            self.jul_consumption, self.aug_consumption, self.sep_consumption,
            self.oct_consumption, self.nov_consumption, self.dec_consumption
        ])
        super().save(*args, **kwargs)
    
    def get_monthly_consumption(self):
        """Return monthly consumption as a list"""
        return [
            self.jan_consumption, self.feb_consumption, self.mar_consumption,
            self.apr_consumption, self.may_consumption, self.jun_consumption,
            self.jul_consumption, self.aug_consumption, self.sep_consumption,
            self.oct_consumption, self.nov_consumption, self.dec_consumption
        ]
    
    def __str__(self):
        return f"{self.name} - {self.annual_consumption:.0f} kWh/year"


class PVSystem(models.Model):
    """Model to store PV system specifications"""
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # System specifications
    system_size_kw = models.FloatField(help_text="System size in kW")
    panel_efficiency = models.FloatField(default=0.20, help_text="Panel efficiency (0-1)")
    inverter_efficiency = models.FloatField(default=0.96, help_text="Inverter efficiency (0-1)")
    system_efficiency = models.FloatField(default=0.75, help_text="Overall system efficiency (0-1)")
    
    # Location and orientation
    latitude = models.FloatField(help_text="Latitude in decimal degrees")
    longitude = models.FloatField(help_text="Longitude in decimal degrees")
    tilt_angle = models.FloatField(default=30, help_text="Panel tilt angle in degrees")
    azimuth = models.FloatField(default=180, help_text="Panel azimuth (180 = South)")
    
    # Degradation
    annual_degradation = models.FloatField(default=0.005, help_text="Annual degradation rate (0-1)")
    
    def __str__(self):
        return f"{self.name} - {self.system_size_kw} kW"


class BESSSystem(models.Model):
    """Model to store BESS system specifications"""
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Battery specifications
    capacity_kwh = models.FloatField(help_text="Battery capacity in kWh")
    usable_capacity_kwh = models.FloatField(help_text="Usable capacity in kWh")
    max_charge_rate_kw = models.FloatField(help_text="Maximum charge rate in kW")
    max_discharge_rate_kw = models.FloatField(help_text="Maximum discharge rate in kW")
    
    # Efficiency
    round_trip_efficiency = models.FloatField(default=0.90, help_text="Round-trip efficiency (0-1)")
    charge_efficiency = models.FloatField(default=0.95, help_text="Charge efficiency (0-1)")
    discharge_efficiency = models.FloatField(default=0.95, help_text="Discharge efficiency (0-1)")
    
    # Control strategy
    CONTROL_STRATEGIES = [
        ('self_consumption', 'Self-consumption optimization'),
        ('time_of_use', 'Time-of-use optimization'),
        ('peak_shaving', 'Peak demand shaving'),
    ]
    control_strategy = models.CharField(max_length=20, choices=CONTROL_STRATEGIES, default='self_consumption')
    
    # Depth of discharge
    min_soc = models.FloatField(default=0.10, help_text="Minimum state of charge (0-1)")
    max_soc = models.FloatField(default=0.90, help_text="Maximum state of charge (0-1)")
    
    def __str__(self):
        return f"{self.name} - {self.capacity_kwh} kWh"


class FinancialParameters(models.Model):
    """Model to store financial parameters for calculations"""
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # System costs
    pv_cost_per_kw = models.FloatField(default=2000, help_text="PV system cost per kW")
    bess_cost_per_kwh = models.FloatField(default=500, help_text="BESS cost per kWh")
    installation_cost_percent = models.FloatField(default=0.10, help_text="Installation cost as % of system cost")
    
    # Electricity rates
    electricity_rate = models.FloatField(default=0.15, help_text="Electricity rate per kWh")
    peak_rate = models.FloatField(default=0.25, help_text="Peak electricity rate per kWh")
    off_peak_rate = models.FloatField(default=0.10, help_text="Off-peak electricity rate per kWh")
    
    # Incentives
    federal_tax_credit = models.FloatField(default=0.30, help_text="Federal tax credit (0-1)")
    state_incentive = models.FloatField(default=0.0, help_text="State incentive per kWh")
    
    # Other parameters
    discount_rate = models.FloatField(default=0.05, help_text="Discount rate for NPV calculations")
    electricity_inflation = models.FloatField(default=0.03, help_text="Annual electricity rate inflation")
    system_lifetime = models.IntegerField(default=25, help_text="System lifetime in years")
    
    def __str__(self):
        return f"{self.name} - {self.electricity_rate:.2f}/kWh"


class CalculationResult(models.Model):
    """Model to store calculation results"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Input references
    energy_profile = models.ForeignKey(EnergyProfile, on_delete=models.CASCADE)
    pv_system = models.ForeignKey(PVSystem, on_delete=models.CASCADE)
    bess_system = models.ForeignKey(BESSSystem, on_delete=models.CASCADE)
    financial_params = models.ForeignKey(FinancialParameters, on_delete=models.CASCADE)
    
    # Results
    total_system_cost = models.FloatField()
    annual_savings = models.FloatField()
    payback_period_years = models.FloatField()
    npv_25_years = models.FloatField()
    irr_percent = models.FloatField()
    
    # Detailed results (stored as JSON)
    monthly_results = models.TextField(default='{}')  # JSON string
    annual_results = models.TextField(default='{}')   # JSON string
    
    def set_monthly_results(self, data):
        """Store monthly results as JSON"""
        self.monthly_results = json.dumps(data)
    
    def get_monthly_results(self):
        """Retrieve monthly results from JSON"""
        return json.loads(self.monthly_results)
    
    def set_annual_results(self, data):
        """Store annual results as JSON"""
        self.annual_results = json.dumps(data)
    
    def get_annual_results(self):
        """Retrieve annual results from JSON"""
        return json.loads(self.annual_results)
    
    def __str__(self):
        return f"{self.name} - Payback: {self.payback_period_years:.1f} years" 