from app_instance import app
import threading
from sync_module import run_sync_module
from main import main as run_mixing_unit  # Импортируем функцию main

def start_sync_module():
    thread = threading.Thread(target=run_sync_module, args=(app,), daemon=True)
    thread.start()

def start_mixing_unit():
    thread = threading.Thread(target=run_mixing_unit, daemon=True)
    thread.start()

if __name__ == "__main__":
    # start_sync_module()    # Запуск модуля синхронизации в отдельном потоке
    # start_mixing_unit()    # Запуск модуля регулирования в отдельном потоке
    app.run(host='0.0.0.0', port=5555, debug=True, use_reloader=False)
