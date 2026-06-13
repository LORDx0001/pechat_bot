from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Client, StoreSettings
from .serializers import ClientSerializer, StoreSettingsSerializer, ClientRegisterSerializer

class ClientRegisterView(APIView):
    def post(self, request):
        serializer = ClientRegisterSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            defaults = {
                'username': data.get('username'),
                'first_name': data.get('first_name'),
                'phone': data.get('phone') or '',
            }
            if 'language' in request.data:
                defaults['language'] = data.get('language')
                
            client, created = Client.objects.update_or_create(
                telegram_id=data['telegram_id'],
                defaults=defaults
            )
            return Response(ClientSerializer(client).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StoreSettingsView(APIView):
    def get(self, request):
        settings_obj = StoreSettings.load()
        serializer = StoreSettingsSerializer(settings_obj, context={'request': request})
        return Response(serializer.data)
