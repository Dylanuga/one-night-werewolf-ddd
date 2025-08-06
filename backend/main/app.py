# Punto de entrada Flask + SocketIO

import asyncio
import secrets
import string
from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from typing import Dict, Any

from services.game_service import GameService
from infrastructure.room_repository import RoomRepository

# Configuración de la aplicación
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
CORS(app, origins=["http://localhost:3000"])  # Ajustar según frontend
socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000", async_mode='threading')

# Inicializar dependencias
room_repository = RoomRepository()

# Callback para emitir eventos desde el servicio
async def emit_callback(event: str, data: Any, room: str = None):
    """Callback para que el GameService pueda emitir eventos"""
    if room:
        socketio.emit(event, data, room=room)
    else:
        socketio.emit(event, data)

game_service = GameService(room_repository, emit_callback)

# Mapeo de socket_id a player_id para tracking
connected_players: Dict[str, str] = {}

def generate_room_code() -> str:
    """Genera un código de sala aleatorio de 4 caracteres"""
    return ''.join(secrets.choice(string.ascii_uppercase) for _ in range(4))

@socketio.on('connect')
def on_connect():
    """Un cliente se conecta"""
    print(f"Cliente conectado: {request.sid}")
    emit('connected', {'socket_id': request.sid})

@socketio.on('disconnect')
def on_disconnect():
    """Un cliente se desconecta"""
    print(f"Cliente desconectado: {request.sid}")
    
    # Si el jugador estaba en una sala, removerlo
    if request.sid in connected_players:
        player_id = connected_players[request.sid]
        room_code = game_service.get_player_room(player_id)
        
        if room_code:
            # Ejecutar la remoción de forma asíncrona
            asyncio.create_task(game_service.leave_room(room_code, player_id))
        
        del connected_players[request.sid]

@socketio.on('create_room')
def on_create_room(data):
    """Crear una nueva sala de juego"""
    try:
        player_name = data.get('name', '').strip()
        if not player_name:
            emit('error', {'message': 'Nombre requerido'})
            return
        
        # Generar código único de sala
        room_code = generate_room_code()
        while game_service.room_exists(room_code):
            room_code = generate_room_code()
        
        player_id = f"player_{request.sid}"
        
        # Crear sala de forma asíncrona
        async def create_room_async():
            success = await game_service.create_room(room_code, player_id, player_name, request.sid)
            if success:
                connected_players[request.sid] = player_id
                join_room(room_code)
                emit('room_created', {'room_code': room_code})
            else:
                emit('error', {'message': 'No se pudo crear la sala'})
        
        asyncio.create_task(create_room_async())
        
    except Exception as e:
        print(f"Error creando sala: {e}")
        emit('error', {'message': 'Error interno del servidor'})

@socketio.on('join_room')
def on_join_room(data):
    """Unirse a una sala existente"""
    try:
        room_code = data.get('room_code', '').strip().upper()
        player_name = data.get('name', '').strip()
        
        if not room_code or not player_name:
            emit('error', {'message': 'Código de sala y nombre requeridos'})
            return
        
        if not game_service.room_exists(room_code):
            emit('error', {'message': 'Sala no encontrada'})
            return
        
        player_id = f"player_{request.sid}"
        
        # Unirse a sala de forma asíncrona
        async def join_room_async():
            success = await game_service.join_room(room_code, player_id, player_name, request.sid)
            if success:
                connected_players[request.sid] = player_id
                join_room(room_code)
                emit('room_joined', {'room_code': room_code})
            else:
                emit('error', {'message': 'No se pudo unir a la sala'})
        
        asyncio.create_task(join_room_async())
        
    except Exception as e:
        print(f"Error uniéndose a sala: {e}")
        emit('error', {'message': 'Error interno del servidor'})

@socketio.on('leave_room')
def on_leave_room():
    """Abandonar la sala actual"""
    try:
        if request.sid not in connected_players:
            emit('error', {'message': 'No estás en ninguna sala'})
            return
        
        player_id = connected_players[request.sid]
        room_code = game_service.get_player_room(player_id)
        
        if not room_code:
            emit('error', {'message': 'No se encontró tu sala'})
            return
        
        # Abandonar sala de forma asíncrona
        async def leave_room_async():
            success = await game_service.leave_room(room_code, player_id)
            if success:
                leave_room(room_code)
                if request.sid in connected_players:
                    del connected_players[request.sid]
                emit('room_left')
            else:
                emit('error', {'message': 'No se pudo abandonar la sala'})
        
        asyncio.create_task(leave_room_async())
        
    except Exception as e:
        print(f"Error abandonando sala: {e}")
        emit('error', {'message': 'Error interno del servidor'})

@socketio.on('set_roles')
def on_set_roles(data):
    """El host selecciona los roles para la partida"""
    try:
        roles = data.get('roles', [])
        
        if not roles:
            emit('error', {'message': 'Debe seleccionar roles'})
            return
        
        if request.sid not in connected_players:
            emit('error', {'message': 'No estás en ninguna sala'})
            return
        
        player_id = connected_players[request.sid]
        room_code = game_service.get_player_room(player_id)
        
        if not room_code:
            emit('error', {'message': 'No se encontró tu sala'})
            return
        
        # Establecer roles de forma asíncrona
        async def set_roles_async():
            success = await game_service.set_selected_roles(room_code, player_id, roles)
            if success:
                emit('roles_set', {'roles': roles})
            else:
                emit('error', {'message': 'No se pudieron establecer los roles'})
        
        asyncio.create_task(set_roles_async())
        
    except Exception as e:
        print(f"Error estableciendo roles: {e}")
        emit('error', {'message': 'Error interno del servidor'})

@socketio.on('start_game')
def on_start_game():
    """El host inicia la partida"""
    try:
        if request.sid not in connected_players:
            emit('error', {'message': 'No estás en ninguna sala'})
            return
        
        player_id = connected_players[request.sid]
        room_code = game_service.get_player_room(player_id)
        
        if not room_code:
            emit('error', {'message': 'No se encontró tu sala'})
            return
        
        # Iniciar juego de forma asíncrona
        async def start_game_async():
            success = await game_service.start_game(room_code, player_id)
            if success:
                emit('game_started')
            else:
                emit('error', {'message': 'No se pudo iniciar el juego'})
        
        asyncio.create_task(start_game_async())
        
    except Exception as e:
        print(f"Error iniciando juego: {e}")
        emit('error', {'message': 'Error interno del servidor'})

@socketio.on('night_action')
def on_night_action(data):
    """Un jugador ejecuta su acción nocturna"""
    try:
        if request.sid not in connected_players:
            emit('error', {'message': 'No estás en ninguna sala'})
            return
        
        player_id = connected_players[request.sid]
        room_code = game_service.get_player_room(player_id)
        
        if not room_code:
            emit('error', {'message': 'No se encontró tu sala'})
            return
        
        action_data = data.get('action', {})
        
        # Ejecutar acción de forma asíncrona
        async def execute_action_async():
            result = await game_service.execute_night_action(room_code, player_id, action_data)
            if not result.get('success'):
                emit('error', {'message': result.get('message', 'Acción no válida')})
        
        asyncio.create_task(execute_action_async())
        
    except Exception as e:
        print(f"Error ejecutando acción nocturna: {e}")
        emit('error', {'message': 'Error interno del servidor'})

@socketio.on('get_game_state')
def on_get_game_state():
    """Obtener el estado actual del juego"""
    try:
        if request.sid not in connected_players:
            emit('error', {'message': 'No estás en ninguna sala'})
            return
        
        player_id = connected_players[request.sid]
        room_code = game_service.get_player_room(player_id)
        
        if not room_code:
            emit('error', {'message': 'No se encontró tu sala'})
            return
        
        game_state = game_service.get_game_state(room_code, player_id)
        if game_state:
            emit('game_state', game_state)
        else:
            emit('error', {'message': 'No se pudo obtener el estado del juego'})
            
    except Exception as e:
        print(f"Error obteniendo estado: {e}")
        emit('error', {'message': 'Error interno del servidor'})

# Endpoint de debug para ver todas las salas
@app.route('/debug/rooms')
def debug_rooms():
    """Endpoint de debug para ver el estado de todas las salas"""
    try:
        rooms = room_repository.get_all_rooms()
        return {'rooms': rooms}
    except Exception as e:
        return {'error': str(e)}, 500

if __name__ == '__main__':
    print("🐺 One Night Werewolf Backend iniciado")
    print("📡 Servidor corriendo en http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)