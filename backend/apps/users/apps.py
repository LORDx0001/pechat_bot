from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = 'Пользователи и Настройки'

    def ready(self):
        import os
        import sys
        import atexit
        # Only start bot when running the development server and from the reloader process
        if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') == 'true':
            import subprocess
            from pathlib import Path
            
            bot_path = Path(__file__).resolve().parent.parent.parent.parent / 'bot' / 'main.py'
            python_path = sys.executable
            
            print("🤖 Автозапуск Telegram бота...")
            bot_process = subprocess.Popen([python_path, str(bot_path)])
            
            def cleanup_bot():
                print("🛑 Останавливаем фоновый Telegram бот...")
                try:
                    bot_process.terminate()
                    bot_process.wait(timeout=3)
                except Exception:
                    pass
                    
            atexit.register(cleanup_bot)
