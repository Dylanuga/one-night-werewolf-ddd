# backend/run.py
import sys
import os

# Añadir el directorio backend al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar y ejecutar la app
from main.app import app, socketio

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() in ('true', '1', 't')
    
    print("🐺 One Night Werewolf Backend iniciado")
    print(f"📡 Servidor corriendo en http://0.0.0.0:{port}")
    print("🔌 Socket.IO habilitado para comunicación en tiempo real")
    print(f"🛠️ Modo debug: {debug}")
    print("-" * 50)
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)