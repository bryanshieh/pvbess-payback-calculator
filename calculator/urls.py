from django.urls import path
from . import views

app_name = 'calculator'

urlpatterns = [
    path('', views.home, name='home'),
    path('detailed/', views.detailed_calculator, name='detailed_calculator'),
    path('energy-profile/', views.energy_profile_create, name='energy_profile_create'),
    path('pv-system/', views.pv_system_create, name='pv_system_create'),
    path('bess-system/', views.bess_system_create, name='bess_system_create'),
    path('financial-params/', views.financial_params_create, name='financial_params_create'),
    path('calculate/', views.run_calculation, name='run_calculation'),
    path('results/<int:result_id>/', views.results_detail, name='results_detail'),
    path('my-calculations/', views.my_calculations, name='my_calculations'),
    path('about/', views.about, name='about'),
    path('help/', views.help_page, name='help'),
    path('api/calculate/', views.api_calculate, name='api_calculate'),
] 