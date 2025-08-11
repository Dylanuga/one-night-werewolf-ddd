# backend/main/app.py
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
CORS(app, origins=["http://localhost:3000"])
socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000", async_mode='eventlet', logger=False, engineio_logger=False)

# Inicializar dependencias
room_repository = RoomRepository()

def emit_callback(event: str, data: Any, room: str = None):
    """Callback para que el GameService pueda emitir eventos"""
    try:
        if room:
            socketio.emit(event, data, room=room)
        else:
            socketio.emit(event, data)
    except Exception as e:
        print(f"Error en emit_callback - evento: {event}, room: {room}, error: {e}")

game_service = GameService(room_repository, emit_callback)

# 🔧 FIX: Mapeo de socket_id a player_id ESTABLE
connected_players: Dict[str, str] = {}

def generate_room_code() -> str:
    """Genera un código de sala aleatorio de 4 caracteres"""
    return ''.join(secrets.choice(string.ascii_uppercase) for _ in range(4))

def get_stable_player_id(player_name: str, room_code: str) -> str:
    """Genera un player_id estable basado en nombre y sala"""
    return f"player_{room_code}_{player_name}".replace(" ", "_")

def find_existing_player_in_room(room_code: str, player_name: str) -> str:
    """Busca si ya existe un jugador con ese nombre en la sala"""
    try:
        game = room_repository.get_game(room_code)
        if not game:
            return None
            
        for player_id, player in game.players.items():
            if player.name == player_name:
                print(f"🔧 JUGADOR EXISTENTE ENCONTRADO: {player_id} ({player_name})")
                return player_id
        
        return None
    except Exception as e:
        print(f"Error buscando jugador existente: {e}")
        return None

@socketio.on('connect')
def on_connect():
    """Un cliente se conecta"""
    try:
        print(f"Cliente conectado: {request.sid}")
        emit('connected', {'socket_id': request.sid})
    except Exception as e:
        print(f"Error en connect: {e}")

@socketio.on('disconnect')
def on_disconnect():
    """Un cliente se desconecta"""
    try:
        print(f"Cliente desconectado: {request.sid}")
        
        # 🔧 FIX: Solo limpiar el mapping, NO remover del juego
        # Esto permite que el jugador se reconecte sin perder su lugar
        if request.sid in connected_players:
            player_id = connected_players[request.sid]
            print(f"🔧 DESCONEXIÓN: {request.sid} -> {player_id} (manteniendo en juego)")
            
            # Marcar como desconectado pero no eliminar
            room_code = game_service.get_player_room(player_id)
            if room_code:
                game = room_repository.get_game(room_code)
                if game and player_id in game.players:
                    game.players[player_id].disconnect()
                    room_repository.save_game(room_code, game)
                    print(f"🔧 Jugador {player_id} marcado como desconectado")
            
            del connected_players[request.sid]
            
    except Exception as e:
        print(f"Error en disconnect: {e}")

@socketio.on('create_room')
def on_create_room(data):
    """Crear una nueva sala de juego"""
    try:
        player_name = data.get('name', '').strip()
        if not player_name:
            emit('error', {'message': 'Nombre requerido'})
            return
        
        room_code = generate_room_code()
        while game_service.room_exists(room_code):
            room_code = generate_room_code()
        
        # 🔧 FIX: Player ID estable basado en nombre y sala
        player_id = get_stable_player_id(player_name, room_code)
        
        success = game_service.create_room(room_code, player_id, player_name, request.sid)
        if success:
            connected_players[request.sid] = player_id
            join_room(room_code)
            emit('room_created', {'room_code': room_code})
            print(f"🔧 SALA CREADA: {player_id} (HOST)")
        else:
            emit('error', {'message': 'No se pudo crear la sala'})
        
    except Exception as e:
        print(f"Error creando sala: {e}")
        emit('error', {'message': 'Error interno del servidor'})

@socketio.on('join_room')
def on_join_room(data):
    """Unirse a una sala existente"""
    try:
        room_code = data.get('room_code', '').strip().upper()
        player_name = data.get('name', '').strip()
        
        print(f"🔧 JOIN_ROOM - NUEVO SISTEMA:")
        print(f"   request.sid: {request.sid}")
        print(f"   room_code: {room_code}")
        print(f"   player_name: {player_name}")
        
        if not room_code or not player_name:
            emit('error', {'message': 'Código de sala y nombre requeridos'})
            return
        
        if not game_service.room_exists(room_code):
            emit('error', {'message': 'Sala no encontrada'})
            return
        
        # 🔧 FIX: Buscar si el jugador ya existe en la sala
        existing_player_id = find_existing_player_in_room(room_code, player_name)
        
        if existing_player_id:
            # 🎯 RECONEXIÓN: Jugador existe, actualizar socket_id
            player_id = existing_player_id
            connected_players[request.sid] = player_id
            
            # Reconectar en el juego
            game = room_repository.get_game(room_code)
            if game and player_id in game.players:
                game.players[player_id].reconnect(request.sid)
                room_repository.save_game(room_code, game)
                print(f"🔧 RECONEXIÓN EXITOSA: {player_id} mantiene su identidad y rol")
                
                # Emitir eventos de reconexión
                join_room(room_code)
                emit('room_joined', {'room_code': room_code})
                
                # Forzar actualización del estado
                game_service._emit_game_update(room_code)
            else:
                emit('error', {'message': 'Error en la reconexión'})
                
        else:
            # 🎯 NUEVO JUGADOR: Crear con ID estable  
            player_id = get_stable_player_id(player_name, room_code)
            
            success = game_service.join_room(room_code, player_id, player_name, request.sid)
            if success:
                connected_players[request.sid] = player_id
                join_room(room_code)
                emit('room_joined', {'room_code': room_code})
                print(f"🔧 NUEVO JUGADOR: {player_id}")
            else:
                emit('error', {'message': 'No se pudo unir a la sala'})
        
    except Exception as e:
        print(f"Error uniéndose a sala: {e}")
        emit('error', {'message': 'Error interno del servidor'})

@socketio.on('leave_room')
def on_leave_room(data=None):
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
        
        success = game_service.leave_room(room_code, player_id)
        if success:
            leave_room(room_code)
            if request.sid in connected_players:
                del connected_players[request.sid]
            emit('room_left')
        else:
            emit('error', {'message': 'No se pudo abandonar la sala'})
        
    except Exception as e:
        print(f"Error abandonando sala: {e}")
        emit('error', {'message': 'Error interno del servidor'})

@socketio.on('set_roles')
def on_set_roles(data):
    """El host selecciona los roles para la partida"""
    try:
        roles = data.get('roles', [])
        
        print(f"🔧 SET_ROLES - SISTEMA FIJO:")
        print(f"   request.sid: {request.sid}")
        print(f"   roles: {roles}")
        
        if not roles:
            emit('error', {'message': 'Debe seleccionar roles'})
            return
        
        if request.sid not in connected_players:
            print(f"❌ Socket no registrado")
            emit('error', {'message': 'No estás en ninguna sala'})
            return
        
        player_id = connected_players[request.sid]
        room_code = game_service.get_player_room(player_id)
        
        print(f"   player_id: {player_id}")
        print(f"   room_code: {room_code}")
        
        if not room_code:
            emit('error', {'message': 'No se encontró tu sala'})
            return
        
        # Verificar host
        game = room_repository.get_game(room_code)
        if not game or player_id not in game.players:
            emit('error', {'message': 'Jugador no encontrado'})
            return
        
        is_host = game.players[player_id].is_host
        print(f"   is_host: {is_host}")
        
        if not is_host:
            emit('error', {'message': 'Solo el host puede establecer roles'})
            return
        
        success = game_service.set_selected_roles(room_code, player_id, roles)
        if success:
            emit('roles_set', {'roles': roles})
            print(f"✅ ROLES ESTABLECIDOS POR HOST: {player_id}")
        else:
            emit('error', {'message': 'No se pudieron establecer los roles'})
        
    except Exception as e:
        print(f"Error estableciendo roles: {e}")
        emit('error', {'message': 'Error interno del servidor'})

@socketio.on('start_game')
def on_start_game(data=None):
    """El host inicia la partida"""
    try:
        print(f"🔧 START_GAME - SISTEMA FIJO:")
        print(f"   request.sid: {request.sid}")
        
        if request.sid not in connected_players:
            emit('error', {'message': 'No estás en ninguna sala'})
            return
        
        player_id = connected_players[request.sid]
        room_code = game_service.get_player_room(player_id)
        
        print(f"   player_id: {player_id}")
        print(f"   room_code: {room_code}")
        
        if not room_code:
            emit('error', {'message': 'No se encontró tu sala'})
            return
        
        # Verificar host
        game = room_repository.get_game(room_code)
        if not game or player_id not in game.players:
            emit('error', {'message': 'Jugador no encontrado'})
            return
        
        is_host = game.players[player_id].is_host  
        print(f"   is_host: {is_host}")
        
        if not is_host:
            emit('error', {'message': 'Solo el host puede iniciar el juego'})
            return
        
        success = game_service.start_game(room_code, player_id)
        if success:
            emit('game_started')
            print(f"✅ JUEGO INICIADO POR HOST: {player_id}")
        else:
            emit('error', {'message': 'No se pudo iniciar el juego'})
        
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
        result = game_service.execute_night_action(room_code, player_id, action_data)
        if not result.get('success'):
            emit('error', {'message': result.get('message', 'Acción no válida')})
        
    except Exception as e:
        print(f"Error ejecutando acción nocturna: {e}")
        emit('error', {'message': 'Error interno del servidor'})

@socketio.on('get_game_state')
def on_get_game_state(data=None):
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

@app.route('/debug/rooms')
def debug_rooms():
    """Endpoint de debug"""
    try:
        rooms = room_repository.get_all_rooms()
        return {'rooms': rooms}
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/debug/connections')
def debug_connections():
    """Endpoint de debug"""
    try:
        return {
            'connected_players': connected_players,
            'total_connections': len(connected_players)
        }
    except Exception as e:
        return {'error': str(e)}, 500

if __name__ == '__main__':
    print("🐺 One Night Werewolf Backend iniciado")
    print("📡 Servidor corriendo en http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)