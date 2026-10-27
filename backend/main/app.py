# backend/main/app.py
import secrets
import string
import time
from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from typing import Dict, Any

from services.game_service import GameService
from infrastructure.room_repository import RoomRepository

# Configuración de la aplicación
app = Flask(__name__)
import os
from functools import wraps

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))

def require_test_endpoints(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if os.environ.get('ENABLE_TEST_ENDPOINTS', 'true').lower() not in ('true', '1', 'yes'):
            return {'error': 'Endpoints de prueba desactivados en este entorno'}, 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/test/create-test-room', methods=['POST'])
@require_test_endpoints
def create_test_room():
    """
    Crea una sala de prueba con código fijo 'TEST' y modo de prueba activado.
    
    Body JSON esperado:
    {
        "role_distribution": {
            "players": ["werewolf", "mason", "mason", "villager", "villager", "villager"],
            "center": ["villager", "villager", "villager"]
        },
        "auto_start": true,  // opcional, inicia el juego automáticamente
        "player_names": ["Player1", "Player2", ...] // opcional, nombres personalizados
    }
    
    Ejemplo de uso:
    POST /test/create-test-room
    {
        "role_distribution": {
            "players": ["werewolf", "mason", "mason", "villager"],
            "center": ["villager", "seer", "robber"]
        },
        "auto_start": true
    }
    """
    try:
        print(f"🧪 === CREANDO SALA DE PRUEBA TEST ===")
        
        data = request.get_json() or {}
        role_distribution = data.get('role_distribution')
        auto_start = data.get('auto_start', False)
        custom_player_names = data.get('player_names', [])
        turn_duration = data.get('turn_duration')
        
        # Validar entrada
        if not role_distribution:
            return {'error': 'Se requiere role_distribution en el body'}, 400
        
        if not isinstance(role_distribution, dict):
            return {'error': 'role_distribution debe ser un objeto JSON'}, 400
            
        if 'players' not in role_distribution or 'center' not in role_distribution:
            return {'error': 'role_distribution debe tener "players" y "center"'}, 400
        
        players_roles = role_distribution['players']
        center_roles = role_distribution['center']
        
        if not isinstance(players_roles, list) or not isinstance(center_roles, list):
            return {'error': 'players y center deben ser arrays'}, 400
        
        if len(players_roles) < 3 or len(players_roles) > 10:
            return {'error': 'Se requieren entre 3 y 10 jugadores'}, 400
        
        if len(center_roles) != 3:
            return {'error': 'center debe tener exactamente 3 roles'}, 400
        
        # Validar roles válidos
        valid_roles = {'werewolf', 'villager', 'seer', 'robber', 'troublemaker', 
                      'hunter', 'mason', 'drunk', 'insomniac', 'tanner'}
        all_roles = players_roles + center_roles
        invalid_roles = [role for role in all_roles if role not in valid_roles]
        if invalid_roles:
            return {'error': f'Roles inválidos: {invalid_roles}. Válidos: {list(valid_roles)}'}, 400
        
        room_code = 'TEST'
        
        print(f"🧪 Configuración de prueba:")
        print(f"   - Jugadores: {len(players_roles)} -> {players_roles}")
        print(f"   - Centro: {len(center_roles)} -> {center_roles}")
        print(f"   - Auto-start: {auto_start}")
        
        # Si ya existe una sala TEST, eliminarla
        if game_service.room_exists(room_code):
            print(f"🧪 Sala TEST ya existe, eliminándola...")
            room_repository.delete_game(room_code)
        
        # Crear jugadores de prueba
        num_players = len(players_roles)
        test_players = []
        
        for i in range(num_players):
            # Usar nombres personalizados si se proporcionan
            if i < len(custom_player_names):
                player_name = custom_player_names[i]
            else:
                player_name = f"TestPlayer{i+1}"
                
            player_id = get_stable_player_id(player_name, room_code)
            socket_id = f"test_socket_{i+1}"  # Socket ID ficticio para pruebas
            test_players.append({
                'id': player_id,
                'name': player_name,
                'socket_id': socket_id
            })
        
        print(f"🧪 Jugadores de prueba:")
        for player in test_players:
            print(f"   - {player['name']} (ID: {player['id']})")
        
        # Crear la sala con el primer jugador como host
        host_player = test_players[0]
        print(f"🧪 Creando sala con host: {host_player['name']}")
        
        success = game_service.create_room(room_code, host_player['id'], host_player['name'], host_player['socket_id'])
        if not success:
            return {'error': 'No se pudo crear la sala TEST'}, 500
        
        # Agregar el resto de jugadores
        for player in test_players[1:]:
            print(f"🧪 Agregando jugador: {player['name']}")
            success = game_service.join_room(room_code, player['id'], player['name'], player['socket_id'])
            if not success:
                return {'error': f'No se pudo agregar jugador {player["name"]}'}, 500
        
        # Activar modo de prueba
        print(f"🧪 Activando modo de prueba...")
        success = game_service.enable_test_mode(room_code, role_distribution)
        if not success:
            return {'error': 'No se pudo activar el modo de prueba'}, 500
        
        # Establecer roles (necesario antes de iniciar)
        print(f"🧪 Estableciendo roles...")
        success = game_service.set_selected_roles(room_code, host_player['id'], all_roles)
        if not success:
            return {'error': 'No se pudieron establecer los roles'}, 500
        
        result = {
            'message': 'Sala de prueba TEST creada exitosamente',
            'room_code': room_code,
            'players': [{'name': p['name'], 'id': p['id']} for p in test_players],
            'role_distribution': role_distribution,
            'test_mode': True,
            'game_started': False
        }

        # Opcional: ajustar duracion del turno para pruebas
        if isinstance(turn_duration, (int, float)) and 1 <= turn_duration <= 60:
            game_service.set_turn_duration(room_code, int(turn_duration))
            result['turn_duration'] = int(turn_duration)
        
        # Si auto_start está activado, iniciar el juego
        if auto_start:
            print(f"🧪 Iniciando juego automáticamente...")
            success = game_service.start_game(room_code, host_player['id'])
            if success:
                result['game_started'] = True
                result['message'] += ' y juego iniciado automáticamente'
                print(f"✅ Juego iniciado automáticamente")
            else:
                result['game_started'] = False
                result['warning'] = 'Sala creada pero no se pudo iniciar el juego'
                print(f"⚠️ No se pudo iniciar el juego automáticamente")
        
        print(f"✅ Sala TEST creada exitosamente")
        return result, 200
        
    except Exception as e:
        print(f"❌ Error en create_test_room: {e}")
        return {'error': str(e)}, 500
cors_origins = os.environ.get('CORS_ORIGINS', '*')
CORS(app, cors_allowed_origins=cors_origins)
socketio = SocketIO(
    app, 
    cors_allowed_origins=cors_origins, 
    async_mode='eventlet', 
    logger=False, 
    engineio_logger=False,
    ping_timeout=60,         # ✅ Timeout más largo para pings
    ping_interval=25,        # ✅ Intervalo de ping más frecuente
    transports=['websocket', 'polling']  # ✅ Permitir ambos transportes
)

# Inicializar dependencias
room_repository = RoomRepository()

def emit_callback(event: str, data: Any, room: str = None):
    """Callback para que el GameService pueda emitir eventos"""
    try:
        if room:
            # 🔧 FIX: Usar to= en lugar de room= para mayor compatibilidad
            socketio.emit(event, data, to=room)
        else:
            socketio.emit(event, data)
                
    except Exception as e:
        print(f"❌ ERROR en emit_callback - evento: {event}, room: {room}, error: {e}")
        import traceback
        traceback.print_exc()

game_service = GameService(
    room_repository,
    emit_callback,
    start_background_task=socketio.start_background_task,
    sleep_fn=socketio.sleep
)

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

def recover_player_by_socket_or_host(request_sid: str) -> tuple:
    """
    Intenta recuperar un player_id basado en el socket_id o asumiendo que es el host.
    Retorna (player_id, room_code) o (None, None) si no se puede recuperar.
    """
    try:
        print(f"🔍 Buscando en {len(room_repository.get_all_rooms())} salas...")
        for room_code in room_repository.get_all_rooms():
            game = room_repository.get_game(room_code)
            if game:
                print(f"🔍 Revisando sala {room_code} con {len(game.players)} jugadores...")
                for player_id, player in game.players.items():
                    print(f"🔍   - Jugador {player_id}: socket_id={getattr(player, 'socket_id', 'NONE')}, is_host={player.is_host}")
                    
                    # Estrategia 1: Coincidencia exacta de socket_id
                    if hasattr(player, 'socket_id') and player.socket_id == request_sid:
                        print(f"🔧 RECUPERADO POR SOCKET: {player_id} en sala {room_code}")
                        return player_id, room_code
                    
                    # Estrategia 2: Si es host y no hay socket_id válido, asumir reconexión
                    if player.is_host and (not hasattr(player, 'socket_id') or player.socket_id != request_sid):
                        print(f"🔧 CANDIDATO HOST ENCONTRADO: {player_id} ({player.name}) en sala {room_code}")
                        # Actualizar su socket_id
                        player.socket_id = request_sid
                        room_repository.save_game(room_code, game)
                        print(f"🔧 RECUPERADO POR HOST: {player_id} actualizado con nuevo socket {request_sid}")
                        return player_id, room_code
        
        return None, None
    except Exception as e:
        print(f"❌ Error en recuperación: {e}")
        return None, None

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
            
            # Marcar como desconectado pero no eliminar
            room_code = game_service.get_player_room(player_id)
            if room_code:
                game = room_repository.get_game(room_code)
                if game and player_id in game.players:
                    game.players[player_id].disconnect()
                    room_repository.save_game(room_code, game)
            
            # NO eliminar el mapeo inmediatamente - esperar un poco por si se reconecta
            # del connected_players[request.sid]  # ❌ NO hacer esto aún
            
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
                
                # Emitir eventos de reconexión
                join_room(room_code)
                emit('room_joined', {'room_code': room_code})
                
                # 🎯 CRÍTICO: Enviar estado privado al jugador reconectado
                private_state = game_service.get_private_state(room_code, player_id)
                if private_state:
                    emit('private_update', private_state)
                
                # Forzar actualización del estado público
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
            else:
                emit('error', {'message': 'No se pudo unir a la sala'})
        
    except Exception as e:
        print(f"Error uniéndose a sala: {e}")
        emit('error', {'message': 'Error interno del servidor'})

@socketio.on('reconnect_session')
def on_reconnect_session(data):
    """Reconecta una sesión de jugador tras pérdida de conexión, cambio de app o recarga"""
    try:
        room_code = data.get('room_code', '').strip().upper() if data else ''
        player_name = data.get('player_name', '').strip() if data else ''
        player_id = data.get('player_id') if data else None

        print(f"🔄 INTENTO DE RECONEXIÓN: room={room_code}, name={player_name}, id={player_id}, sid={request.sid}")

        if not room_code:
            emit('reconnect_failed', {'message': 'Código de sala no proporcionado'})
            return

        game = room_repository.get_game(room_code)
        if not game:
            print(f"❌ RECONEXIÓN FALLIDA: Sala {room_code} no existe")
            emit('reconnect_failed', {'message': 'La sala ya no existe'})
            return

        # Buscar jugador por player_id o por coincidencia de nombre
        target_pid = None
        if player_id and player_id in game.players:
            target_pid = player_id
        elif player_name:
            for pid, p in game.players.items():
                if p.name.strip().lower() == player_name.strip().lower():
                    target_pid = pid
                    break

        if not target_pid:
            print(f"❌ RECONEXIÓN FALLIDA: Jugador {player_name} no encontrado en sala {room_code}")
            emit('reconnect_failed', {'message': 'Jugador no encontrado en la sala'})
            return

        # Reconectar en el dominio y en el mapping de sockets
        player = game.players[target_pid]
        player.reconnect(request.sid)
        connected_players[request.sid] = target_pid
        room_repository.save_game(room_code, game)
        join_room(room_code)

        print(f"✅ RECONEXIÓN EXITOSA: {player.name} ({target_pid}) en sala {room_code}")

        # 1. Notificar éxito al cliente
        emit('reconnected_success', {
            'room_code': room_code,
            'player_name': player.name,
            'player_id': target_pid,
            'is_host': player.is_host,
            'phase': game.phase.value
        })
        emit('room_joined', {'room_code': room_code})

        # 2. Sincronizar roles seleccionados si existen
        if game.selected_roles:
            emit('roles_set', {'roles': game.selected_roles})

        # 3. Sincronizar estado privado y público
        private_state = game_service.get_private_state(room_code, target_pid)
        if private_state:
            emit('private_update', private_state)

        # 4. Sincronizar datos de fase nocturna si corresponde
        if game.phase.value == 'night_phase':
            current_turn = game.get_current_turn_role()
            if current_turn:
                emit('turn_start', {'role': current_turn, 'duration': game_service._get_turn_duration(room_code)})
                if player.original_role == current_turn:
                    action_data = game.get_night_action_data_for_player(target_pid)
                    if action_data:
                        emit('night_action', action_data)

        # 5. Sincronizar fase de votación si corresponde
        if game.phase.value == 'voting':
            emit('voting_started', {'room_code': room_code})

        # 6. Sincronizar fase de revelación final si corresponde
        if game.phase.value == 'game_end':
            reveal_data = game.get_reveal_data()
            emit('reveal', reveal_data)
            emit('game_end', reveal_data)

        # 7. Actualizar el estado público a toda la sala
        game_service._emit_game_update(room_code)

    except Exception as e:
        print(f"❌ Error en reconnect_session: {e}")
        emit('reconnect_failed', {'message': 'Error interno al reconectar'})

@socketio.on('set_discussion_timer')
def on_set_discussion_timer(data):
    """El host selecciona la duración del temporizador de debate (120, 300, 600 segundos)"""
    try:
        duration = data.get('duration', 300) if data else 300
        if duration not in (120, 300, 600):
            emit('error', {'message': 'Duración inválida. Opciones: 120, 300, 600 segundos'})
            return

        if request.sid not in connected_players:
            recovered_player_id, _ = recover_player_by_socket_or_host(request.sid)
            if recovered_player_id:
                connected_players[request.sid] = recovered_player_id
            else:
                emit('error', {'message': 'No estás en ninguna sala'})
                return

        player_id = connected_players[request.sid]
        room_code = game_service.get_player_room(player_id)
        if not room_code:
            emit('error', {'message': 'No se encontró tu sala'})
            return

        success = game_service.set_discussion_timer(room_code, player_id, duration)
        if success:
            socketio.emit('timer_settings_updated', {'discussion_duration': duration}, room=room_code)
            emit('timer_settings_updated', {'discussion_duration': duration})
            print(f"⏱️ Host configuró tiempo de debate: {duration}s en sala {room_code}")
        else:
            emit('error', {'message': 'Solo el host puede cambiar la duración del debate'})

    except Exception as e:
        print(f"Error configurando temporizador: {e}")
        emit('error', {'message': 'Error interno del servidor'})

@socketio.on('leave_room')
def on_leave_room(data=None):
    """Abandonar la sala actual con recuperación tolerante a desconexión"""
    try:
        player_id = connected_players.get(request.sid)
        room_code = None

        if data and isinstance(data, dict):
            room_code = data.get('room_code')
            name = data.get('player_name') or data.get('name')
            if not player_id and room_code and name:
                player_id = find_existing_player_in_room(room_code, name)

        if not player_id:
            recovered_id, recovered_room = recover_player_by_socket_or_host(request.sid)
            if recovered_id:
                player_id = recovered_id
                if not room_code:
                    room_code = recovered_room

        if player_id:
            if not room_code:
                room_code = game_service.get_player_room(player_id)
            if room_code:
                game_service.leave_room(room_code, player_id)
                leave_room(room_code)

        if request.sid in connected_players:
            del connected_players[request.sid]

        # IMPORTANTE: SIEMPRE emitir room_left para garantizar que el cliente limpie su UI
        emit('room_left')
        print(f"👋 leave_room ejecutado para sid={request.sid}, player_id={player_id}")

    except Exception as e:
        print(f"Error abandonando sala: {e}")
        emit('room_left')

@socketio.on('set_roles')
def on_set_roles(data):
    """El host selecciona los roles para la partida"""
    try:
        roles = data.get('roles', [])
        
        print(f"🔧 SET_ROLES - SISTEMA FIJO:")
        print(f"   request.sid: {request.sid}")
        print(f"   roles: {roles}")
        print(f"   connected_players actual: {connected_players}")
        
        if not roles:
            emit('error', {'message': 'Debe seleccionar roles'})
            return
        
        if request.sid not in connected_players:
            print(f"❌ ERROR: Socket ID no encontrado en connected_players")
            print(f"🔍 DEBUGGING - Intentando recuperar player_id por socket...")
            
            # Usar función auxiliar para recuperar
            recovered_player_id, recovered_room_code = recover_player_by_socket_or_host(request.sid)
            
            if recovered_player_id:
                connected_players[request.sid] = recovered_player_id
                print(f"✅ MAPEO RESTAURADO: {request.sid} -> {recovered_player_id}")
            else:
                print(f"❌ No se pudo recuperar ningún jugador para socket {request.sid}")
                emit('error', {'message': 'No estás en ninguna sala'})
                return
        
        player_id = connected_players[request.sid]
        room_code = game_service.get_player_room(player_id)
        
        print(f"   player_id: {player_id}")
        print(f"   room_code: {room_code}")
        
        if not room_code:
            emit('error', {'message': 'No se encontró tu sala'})
            return
        
        # Verificar que el jugador es realmente el host
        game = room_repository.get_game(room_code)
        if not game:
            emit('error', {'message': 'Sala no encontrada'})
            return
        
        if player_id not in game.players:
            emit('error', {'message': 'Jugador no encontrado en la sala'})
            return
        
        if not game.players[player_id].is_host:
            emit('error', {'message': 'Solo el host puede establecer roles'})
            return
        
        success = game_service.set_selected_roles(room_code, player_id, roles)
        if success:
            duration = data.get('discussion_duration')
            if duration in (120, 300, 600):
                game_service.set_discussion_timer(room_code, player_id, duration)

            # 🎯 CRÍTICO: Emitir roles_set a TODA LA SALA, NO solo al host
            print(f"✅ EMITIENDO roles_set A TODA LA SALA {room_code}: {roles}")
            socketio.emit('roles_set', {'roles': roles}, room=room_code)
            
            # También emitir al host individual (por compatibilidad)
            emit('roles_set', {'roles': roles})
            
            print(f"✅ Roles establecidos y sincronizados en sala: {roles}")
        else:
            emit('error', {'message': 'No se pudieron establecer los roles'})
        
    except Exception as e:
        print(f"Error estableciendo roles: {e}")
        emit('error', {'message': 'Error interno del servidor'})

@socketio.on('start_game')
def on_start_game(data=None):
    """El host inicia la partida"""
    try:
        if request.sid not in connected_players:
            # Usar función auxiliar para recuperar
            recovered_player_id, recovered_room_code = recover_player_by_socket_or_host(request.sid)
            
            if recovered_player_id:
                connected_players[request.sid] = recovered_player_id
            else:
                emit('error', {'message': 'No estás en ninguna sala'})
                return
        
        player_id = connected_players[request.sid]
        room_code = game_service.get_player_room(player_id)
        
        if not room_code:
            emit('error', {'message': 'No se encontró tu sala'})
            return
        
        # Verificar host
        game = room_repository.get_game(room_code)
        if not game or player_id not in game.players:
            emit('error', {'message': 'Jugador no encontrado'})
            return
        
        is_host = game.players[player_id].is_host  
        
        if not is_host:
            emit('error', {'message': 'Solo el host puede iniciar el juego'})
            return
        
        success = game_service.start_game(room_code, player_id)
        if success:
            # 🎯 CRÍTICO: Emitir game_started SOLO a toda la sala con datos consistentes
            game_started_data = {
                'room_code': room_code,
                'message': 'El juego ha comenzado',
                'timestamp': time.time()
            }
            socketio.emit('game_started', game_started_data, room=room_code)
        else:
            emit('error', {'message': 'No se pudo iniciar el juego'})
        
    except Exception as e:
        print(f"Error iniciando juego: {e}")
        emit('error', {'message': 'Error interno del servidor'})

@socketio.on('end_discussion')
def on_end_discussion(data=None):
    """El host finaliza la discusión e inicia votación."""
    try:
        if request.sid not in connected_players:
            emit('error', {'message': 'No estás en ninguna sala'})
            return

        player_id = connected_players[request.sid]
        room_code = game_service.get_player_room(player_id)

        if not room_code:
            emit('error', {'message': 'No se encontró tu sala'})
            return

        success = game_service.start_voting_phase(room_code, player_id)
        if not success:
            emit('error', {'message': 'No se pudo iniciar votación'})
            return

    except Exception as e:
        print(f"Error iniciando votación: {e}")
        emit('error', {'message': 'Error interno del servidor'})

@socketio.on('submit_vote')
def on_submit_vote(data):
    """Un jugador envía su voto."""
    try:
        if request.sid not in connected_players:
            emit('error', {'message': 'No estás en ninguna sala'})
            return

        player_id = connected_players[request.sid]
        room_code = game_service.get_player_room(player_id)
        target_id = data.get('target_player_id')

        if not room_code:
            emit('error', {'message': 'No se encontró tu sala'})
            return
        if not target_id:
            emit('error', {'message': 'Voto inválido'})
            return

        result = game_service.submit_vote(room_code, player_id, target_id)
        if result.get('success') is False:
            emit('error', {'message': result.get('message', 'Error al votar')})
        else:
            emit('vote_received', {'success': True})

    except Exception as e:
        print(f"Error enviando voto: {e}")
        emit('error', {'message': 'Error interno del servidor'})

@socketio.on('end_voting')
def on_end_voting(data=None):
    """El host finaliza la votación y revela resultados."""
    try:
        if request.sid not in connected_players:
            emit('error', {'message': 'No estás en ninguna sala'})
            return

        player_id = connected_players[request.sid]
        room_code = game_service.get_player_room(player_id)

        if not room_code:
            emit('error', {'message': 'No se encontró tu sala'})
            return

        success = game_service.end_voting_phase(room_code, player_id)
        if not success:
            emit('error', {'message': 'No se pudo revelar (faltan votos o no eres host)'})
            return

    except Exception as e:
        print(f"Error finalizando votación: {e}")
        emit('error', {'message': 'Error interno del servidor'})

@socketio.on('reset_game')
def on_reset_game(data):
    """El host reinicia la partida a LOBBY o ROLE_SELECTION"""
    try:
        if request.sid not in connected_players:
            emit('error', {'message': 'No estás en ninguna sala'})
            return

        player_id = connected_players[request.sid]
        room_code = game_service.get_player_room(player_id)
        to_phase = data.get('to_phase') if data else None

        if not room_code:
            emit('error', {'message': 'No se encontró tu sala'})
            return
            
        if to_phase not in ('lobby', 'role_selection'):
            emit('error', {'message': 'Fase de destino inválida'})
            return

        success = game_service.reset_game(room_code, player_id, to_phase)
        if not success:
            emit('error', {'message': 'No se pudo reiniciar el juego (no eres el host o la partida no ha terminado)'})
            return

    except Exception as e:
        print(f"Error reiniciando juego: {e}")
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

@socketio.on('advance_turn')
def on_advance_turn(data=None):
    """Avanzar manualmente el turno durante la fase nocturna"""
    try:
        print(f"🔄 RECIBIDO ADVANCE_TURN de {request.sid}, data: {data}")
        
        if request.sid not in connected_players:
            print(f"❌ ADVANCE_TURN: Socket {request.sid} no está en connected_players")
            emit('error', {'message': 'No estás en ninguna sala'})
            return
        
        player_id = connected_players[request.sid]
        print(f"✅ ADVANCE_TURN: Socket {request.sid} -> player_id: {player_id}")
        
        room_code = game_service.get_player_room(player_id)
        print(f"✅ ADVANCE_TURN: player_id {player_id} -> room_code: {room_code}")
        
        if not room_code:
            print(f"❌ ADVANCE_TURN: No se encontró sala para player_id {player_id}")
            emit('error', {'message': 'No se encontró tu sala'})
            return
        
        # Verificar que el juego esté en fase nocturna
        game = room_repository.get_game(room_code)
        if not game:
            print(f"❌ ADVANCE_TURN: No se encontró juego para sala {room_code}")
            emit('error', {'message': 'Sala no encontrada'})
            return
        
        if game.phase.value != 'night_phase':
            print(f"❌ ADVANCE_TURN: Fase incorrecta {game.phase.value}")
            emit('error', {'message': f'Solo se puede avanzar turno en night_phase, actual: {game.phase.value}'})
            return
        
        # Avanzar el turno manualmente
        print(f"🔧 AVANZANDO TURNO MANUALMENTE: {player_id} para sala {room_code}")
        game_service.advance_turn(room_code)
        print(f"✅ ADVANCE_TURN: Turno avanzado correctamente para sala {room_code}")
        
    except Exception as e:
        print(f"❌ ERROR avanzando turno: {e}")
        emit('error', {'message': f'Error al avanzar turno: {str(e)}'})

@app.route('/debug/rooms')
@require_test_endpoints
def debug_rooms():
    """Endpoint de debug"""
    try:
        rooms = room_repository.get_all_rooms()
        return {'rooms': rooms}
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/debug/connections')
@require_test_endpoints
def debug_connections():
    """Endpoint de debug"""
    try:
        # También obtener información de los sockets reales en los juegos
        socket_mappings_in_games = {}
        
        for room_code in room_repository.get_all_rooms():
            game = room_repository.get_game(room_code)
            if game:
                for player_id, player in game.players.items():
                    if hasattr(player, 'socket_id'):
                        socket_mappings_in_games[player.socket_id] = {
                            'player_id': player_id,
                            'player_name': player.name,
                            'room_code': room_code,
                            'is_connected': player.is_connected,
                            'is_host': player.is_host
                        }
        
        return {
            'connected_players': connected_players,
            'total_connections': len(connected_players),
            'socket_mappings_in_games': socket_mappings_in_games,
            'mismatch_count': len(set(connected_players.keys()) - set(socket_mappings_in_games.keys()))
        }
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/test/status')
@require_test_endpoints
def test_status():
    """Obtiene el estado actual de la sala TEST"""
    try:
        room_code = 'TEST'
        
        if not game_service.room_exists(room_code):
            return {'exists': False, 'message': 'Sala TEST no existe'}, 404
        
        # Obtener estado público y detallado para testing
        game_state = game_service.get_game_state(room_code)
        if not game_state:
            return {'error': 'No se pudo obtener el estado del juego'}, 500
        
        # Obtener información adicional para debugging
        game = room_repository.get_game(room_code)
        
        result = {
            'exists': True,
            'room_code': room_code,
            'game_state': game_state,
            'test_mode': getattr(game, 'test_mode', False) if game else False,
            'phase': game.phase.value if game else 'unknown',
            'current_turn_role': game.get_current_turn_role() if game else None,
            'players_count': len(game.players) if game else 0,
            'players': [
                {
                    'name': player.name,
                    'id': player_id,
                    'role': player.get_role_name() if hasattr(player, 'get_role_name') else 'unknown',
                    'is_host': player.is_host,
                    'is_connected': player.is_connected
                }
                for player_id, player in (game.players.items() if game else [])
            ]
        }
        
        return result, 200
        
    except Exception as e:
        print(f"Error en test_status: {e}")
        return {'error': str(e)}, 500

@app.route('/test/reset', methods=['POST'])
@require_test_endpoints
def reset_test_room():
    """Elimina la sala TEST si existe"""
    try:
        room_code = 'TEST'
        
        if game_service.room_exists(room_code):
            room_repository.delete_game(room_code)
            print(f"🧪 Sala TEST eliminada")
            return {'message': 'Sala TEST eliminada exitosamente'}, 200
        else:
            return {'message': 'Sala TEST no existía'}, 200
            
    except Exception as e:
        print(f"Error en reset_test_room: {e}")
        return {'error': str(e)}, 500

@app.route('/test/advance-turn', methods=['POST'])
@require_test_endpoints
def advance_test_turn():
    """Avanza manualmente el turno en la sala TEST (solo para debugging)"""
    try:
        room_code = 'TEST'
        
        if not game_service.room_exists(room_code):
            return {'error': 'Sala TEST no existe'}, 404
        
        game = room_repository.get_game(room_code)
        if not game:
            return {'error': 'No se pudo obtener el estado del juego'}, 500
        
        if game.phase.value != 'night_phase':
            return {'error': f'Solo se puede avanzar turno en night_phase, actual: {game.phase.value}'}, 400
        
        # Avanzar el turno manualmente
        advanced = game.advance_night_turn()
        if advanced:
            room_repository.save_game(room_code, game)
            
            result = {
                'message': 'Turno avanzado exitosamente',
                'new_phase': game.phase.value,
                'current_turn_role': game.get_current_turn_role(),
                'night_finished': game.phase.value == 'day_phase'
            }
            
            # Emitir actualización
            game_service._emit_game_update(room_code)
            
            return result, 200
        else:
            return {'error': 'No se pudo avanzar el turno'}, 400
            
    except Exception as e:
        print(f"Error en advance_test_turn: {e}")
        return {'error': str(e)}, 500

@app.route('/test/presets')
@require_test_endpoints
def test_presets():
    """Devuelve configuraciones predefinidas para testing"""
    presets = {
        'basic_werewolf': {
            'name': 'Lobo Básico',
            'description': '1 lobo, 2 masones, 3 aldeanos',
            'role_distribution': {
                'players': ['werewolf', 'mason', 'mason', 'villager', 'villager', 'villager'],
                'center': ['villager', 'seer', 'robber']
            }
        },
        'seer_game': {
            'name': 'Juego con Vidente',
            'description': '1 lobo, 1 vidente, 2 aldeanos',
            'role_distribution': {
                'players': ['werewolf', 'seer', 'villager', 'villager'],
                'center': ['villager', 'mason', 'robber']
            }
        },
        'complex_game': {
            'name': 'Juego Complejo',
            'description': '1 lobo, 1 vidente, 1 ladrón, 1 alborotador, 2 aldeanos',
            'role_distribution': {
                'players': ['werewolf', 'seer', 'robber', 'troublemaker', 'villager', 'villager'],
                'center': ['villager', 'mason', 'drunk']
            }
        },
        'mason_test': {
            'name': 'Prueba Masones',
            'description': '2 masones, 2 aldeanos (sin lobo para test)',
            'role_distribution': {
                'players': ['mason', 'mason', 'villager', 'villager'],
                'center': ['werewolf', 'seer', 'robber']
            }
        }
    }
    
    return {
        'presets': presets,
        'usage': 'Usa POST /test/create-test-room con el campo role_distribution de cualquier preset'
    }, 200

@app.route('/test/disable/<room_code>', methods=['POST'])
@require_test_endpoints
def disable_test_mode(room_code):
    """Desactiva el modo de prueba para una sala"""
    try:
        success = game_service.disable_test_mode(room_code)
        if success:
            return {'message': 'Modo de prueba desactivado'}, 200
        else:
            return {'error': 'No se pudo desactivar el modo de prueba'}, 400
    except Exception as e:
        return {'error': str(e)}, 500

if __name__ == '__main__':
    print("🐺 One Night Werewolf Backend iniciado")
    print("📡 Servidor corriendo en http://localhost:5000")
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() in ('true', '1', 't')
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)
