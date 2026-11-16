# backend/main/app.py
import os
import secrets
import traceback
from typing import Any

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

from infrastructure.room_repository import RoomRepository
from main.http_routes import register_http_routes, require_test_endpoints
from main.session_manager import (
    connected_players,
    find_existing_player_in_room,
    generate_room_code,
    get_stable_player_id,
    recover_player_by_socket_or_host,
)
from main.socket_handlers import register_socket_handlers
from services.game_service import GameService

# Configuración de la aplicación
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))

cors_origins = os.environ.get('CORS_ORIGINS', '*')
CORS(app, cors_allowed_origins=cors_origins)
socketio = SocketIO(
    app,
    cors_allowed_origins=cors_origins,
    async_mode='eventlet',
    logger=False,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25,
    transports=['websocket', 'polling']
)

# Inicializar dependencias
room_repository = RoomRepository()


def emit_callback(event: str, data: Any, room: str = None):
    """Callback para que el GameService pueda emitir eventos."""
    try:
        if room:
            socketio.emit(event, data, to=room)
        else:
            socketio.emit(event, data)
    except Exception as e:
        print(f"❌ ERROR en emit_callback - evento: {event}, room: {room}, error: {e}")
        traceback.print_exc()


game_service = GameService(
    room_repository,
    emit_callback,
    start_background_task=socketio.start_background_task,
    sleep_fn=socketio.sleep
)

# Registrar rutas HTTP y manejadores de Socket.IO
register_http_routes(app, game_service, room_repository, connected_players)
register_socket_handlers(socketio, game_service, room_repository, connected_players)

if __name__ == '__main__':
    print("🐺 One Night Werewolf Backend iniciado")
    print("📡 Servidor corriendo en http://localhost:5000")
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() in ('true', '1', 't')
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)
