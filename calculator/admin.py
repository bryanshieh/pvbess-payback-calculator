from django.contrib import admin
from .models import EnergyProfile, PVSystem, BESSSystem, FinancialParameters, CalculationResult


@admin.register(EnergyProfile)
class EnergyProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'annual_consumption', 'peak_demand', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['name', 'user__username']
    readonly_fields = ['annual_consumption']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'user')
        }),
        ('Monthly Consumption (kWh)', {
            'fields': (
                'jan_consumption', 'feb_consumption', 'mar_consumption', 'apr_consumption',
                'may_consumption', 'jun_consumption', 'jul_consumption', 'aug_consumption',
                'sep_consumption', 'oct_consumption', 'nov_consumption', 'dec_consumption'
            )
        }),
        ('Additional Information', {
            'fields': ('peak_demand', 'annual_consumption')
        }),
    )


@admin.register(PVSystem)
class PVSystemAdmin(admin.ModelAdmin):
    list_display = ['name', 'system_size_kw', 'latitude', 'longitude', 'tilt_angle', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'system_size_kw')
        }),
        ('Efficiency', {
            'fields': ('panel_efficiency', 'inverter_efficiency', 'system_efficiency')
        }),
        ('Location & Orientation', {
            'fields': ('latitude', 'longitude', 'tilt_angle', 'azimuth')
        }),
        ('Degradation', {
            'fields': ('annual_degradation',)
        }),
    )


@admin.register(BESSSystem)
class BESSSystemAdmin(admin.ModelAdmin):
    list_display = ['name', 'capacity_kwh', 'usable_capacity_kwh', 'control_strategy', 'created_at']
    list_filter = ['control_strategy', 'created_at']
    search_fields = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'capacity_kwh', 'usable_capacity_kwh')
        }),
        ('Power Ratings', {
            'fields': ('max_charge_rate_kw', 'max_discharge_rate_kw')
        }),
        ('Efficiency', {
            'fields': ('round_trip_efficiency', 'charge_efficiency', 'discharge_efficiency')
        }),
        ('Control & Operation', {
            'fields': ('control_strategy', 'min_soc', 'max_soc')
        }),
    )


@admin.register(FinancialParameters)
class FinancialParametersAdmin(admin.ModelAdmin):
    list_display = ['name', 'electricity_rate', 'pv_cost_per_kw', 'bess_cost_per_kwh', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name',)
        }),
        ('System Costs', {
            'fields': ('pv_cost_per_kw', 'bess_cost_per_kwh', 'installation_cost_percent')
        }),
        ('Electricity Rates', {
            'fields': ('electricity_rate', 'peak_rate', 'off_peak_rate')
        }),
        ('Incentives', {
            'fields': ('federal_tax_credit', 'state_incentive')
        }),
        ('Financial Parameters', {
            'fields': ('discount_rate', 'electricity_inflation', 'system_lifetime')
        }),
    )


@admin.register(CalculationResult)
class CalculationResultAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'payback_period_years', 'annual_savings', 'total_system_cost', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['name', 'user__username']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'user', 'created_at')
        }),
        ('Input References', {
            'fields': ('energy_profile', 'pv_system', 'bess_system', 'financial_params')
        }),
        ('Results', {
            'fields': ('total_system_cost', 'annual_savings', 'payback_period_years', 'npv_25_years', 'irr_percent')
        }),
        ('Detailed Results', {
            'fields': ('monthly_results', 'annual_results'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ('energy_profile', 'pv_system', 'bess_system', 'financial_params')
        return self.readonly_fields 