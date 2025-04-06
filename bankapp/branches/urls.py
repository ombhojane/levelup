from django.urls import path
from . import views

app_name = 'branches'  # Define the application namespace

urlpatterns = [
    path('input/', views.branch_input, name='branch_input'),  # Branch input page
    path('transactions/', views.transactions, name='transactions'),  # Transactions page
    path('risk-scoring/', views.risk_scoring, name='risk_scoring'),  # Risk scoring page
    path('insider-threat/', views.insider_threat, name='insider_threat'),  # Insider threat page
    path('api/risk-assessment/', views.risk_assessment_api, name='risk_assessment_api'),  # Risk assessment API endpoint
    path('api/insider-threat/logs/', views.insider_threat_logs_api, name='insider_threat_logs_api'),  # Insider threat logs API
    path('api/transaction-chat/', views.transaction_chat, name='transaction_chat_api'),  # Transaction chat API endpoint
    path('chatbot/', views.chat_bot, name='chatbot'),  # Chatbot page
    path('fraud-detection/', views.fraud_detection, name='fraud_detection'),
    path('ecom-dashboard/', views.ecom_dashboard, name='ecom_dashboard'),  # Make sure this is present
    path('send-email/', views.send_email, name='send_email'),  # Add this line for the email API endpoint
    path('mail/', views.mail, name='mail'),  # Updated mail view
]
