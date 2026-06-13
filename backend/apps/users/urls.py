from django.urls import path
from .views import ClientRegisterView, StoreSettingsView

urlpatterns = [
    path('clients/register/', ClientRegisterView.as_view(), name='client-register'),
    path('settings/', StoreSettingsView.as_view(), name='store-settings'),
]
