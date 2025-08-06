# backend/run.py
import sys
import os

# Añadir el directorio backend al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar y ejecutar la app
from main.app import app, socketio

if __name__ == '__main__':
    print("🐺 One Night Werewolf Backend iniciado")
    print("📡 Servidor corriendo en http://localhost:5000")
    print("🔌 Socket.IO habilitado para comunicación en tiempo real")
    print("🛠️ Modo debug activado")
    print("-" * 50)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)