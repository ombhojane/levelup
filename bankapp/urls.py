from django.urls import path, include
from . import views

urlpatterns = [
    path('compliance_dashboard/', views.compliance_dashboard, name='compliance_dashboard'),
    path('transactions/', views.transactions, name='transactions'),
    path('csv-data/', views.get_csv_data, name='get_csv_data'),
    path('branches/', include('branches.urls', namespace='branches')),
]