from django.urls import path
from . import views

app_name = 'calculator'

urlpatterns = [
    path('', views.home, name='home'),
    path('energy-profile/', views.energy_profile_form, name='energy_profile_form'),
    path('pv-system/', views.pv_system_form, name='pv_system_form'),
    path('bess-system/', views.bess_system_form, name='bess_system_form'),
    path('financial-parameters/', views.financial_parameters_form, name='financial_parameters_form'),
    path('detailed-calculator/', views.detailed_calculator, name='detailed_calculator'),
    path('about/', views.about, name='about'),
    path('help/', views.help_page, name='help'),
    path('my-calculations/', views.my_calculations, name='my_calculations'),
    path('ajax/file-upload/', views.ajax_file_upload, name='ajax_file_upload'),
] 