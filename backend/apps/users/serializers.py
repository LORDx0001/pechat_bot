from rest_framework import serializers
from .models import Client, StoreSettings

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'telegram_id', 'username', 'first_name', 'phone', 'language', 'is_manager', 'created_at']

class StoreSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreSettings
        fields = [
            'shop_name', 'logo', 'contacts', 'manager_telegram', 
            'currency', 'min_order_amount', 'welcome_text', 'about_text', 'admin_chat_id'
        ]
class ClientRegisterSerializer(serializers.Serializer):
    telegram_id = serializers.IntegerField()
    username = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    first_name = serializers.CharField()
    phone = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    language = serializers.CharField(required=False, default='ru')
