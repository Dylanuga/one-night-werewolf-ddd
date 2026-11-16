import time
from typing import Dict, Optional, Tuple

from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room

from infrastructure.room_repository import RoomRepository
from main.session_manager import (
    find_existing_player_in_room,
    generate_room_code,
    get_stable_player_id,
    recover_player_by_socket_or_host,
)
from services.game_service import GameService


def _emit_night_turn_sync(game, game_service: GameService, room_code: str) -> Optional[str]:
    """Emite el evento turn_start al cliente reconectado si la partida está en fase nocturna."""
    current_turn = 'open_eyes' if getattr(game, 'open_eyes_active', False) else game.get_current_turn_role()
    if not current_turn:
        return None

    now = time.time()
    duration = game.turn_duration or game_service._get_turn_duration(room_code)
    start_ts = game.turn_start_timestamp or now
    end_ts = game.turn_end_timestamp or (start_ts + duration)
    emit('turn_start', {
        'role': current_turn,
        'phase': f'Fase: {current_turn}',
        'duration': duration,
        'timestamp': start_ts,
        'end_timestamp': end_ts,
        'server_time': now,
        'remaining': max(0.0, end_ts - now)
    })
    return current_turn


def _resolve_player_and_room(
    room_repository: RoomRepository,
    game_service: GameService,
    connected_players: Dict[str, str],
    recover: bool = False
) -> Tuple[Optional[str], Optional[str]]:
    """Resuelve (player_id, room_code) para el socket actual o emite error."""
    sid = request.sid
    if sid not in connected_players:
        if recover:
            recovered_player_id, _ = recover_player_by_socket_or_host(room_repository, sid)
            if recovered_player_id:
                connected_players[sid] = recovered_player_id
            else:
                emit('error', {'message': 'No estás en ninguna sala'})
                return None, None
        else:
            emit('error', {'message': 'No estás en ninguna sala'})
            return None, None

    player_id = connected_players[sid]
    room_code = game_service.get_player_room(player_id)
    if not room_code:
        emit('error', {'message': 'No se encontró tu sala'})
        return None, None

    return player_id, room_code


def register_socket_handlers(
    socketio: SocketIO,
    game_service: GameService,
    room_repository: RoomRepository,
    connected_players: Dict[str, str]
):
    """Registra todos los manejadores de eventos Socket.IO."""

    @socketio.on('connect')
    def on_connect():
        """Un cliente se conecta."""
        try:
            print(f"Cliente conectado: {request.sid}")
            emit('connected', {'socket_id': request.sid})
        except Exception as e:
            print(f"Error en connect: {e}")

    @socketio.on('disconnect')
    def on_disconnect():
        """Un cliente se desconecta."""
        try:
            print(f"Cliente desconectado: {request.sid}")

            if request.sid in connected_players:
                player_id = connected_players[request.sid]

                room_code = game_service.get_player_room(player_id)
                if room_code:
                    game = room_repository.get_game(room_code)
                    if game and player_id in game.players:
                        game.players[player_id].disconnect()
                        room_repository.save_game(room_code, game)

        except Exception as e:
            print(f"Error en disconnect: {e}")

    @socketio.on('create_room')
    def on_create_room(data):
        """Crear una nueva sala de juego."""
        try:
            player_name = data.get('name', '').strip()
            if not player_name:
                emit('error', {'message': 'Nombre requerido'})
                return

            room_code = generate_room_code()
            while game_service.room_exists(room_code):
                room_code = generate_room_code()

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
        """Unirse a una sala existente."""
        try:
            room_code = data.get('room_code', '').strip().upper()
            player_name = data.get('name', '').strip()

            if not room_code or not player_name:
                emit('error', {'message': 'Código de sala y nombre requeridos'})
                return

            if not game_service.room_exists(room_code):
                emit('error', {'message': 'Sala no encontrada'})
                return

            existing_player_id = find_existing_player_in_room(room_repository, room_code, player_name)

            if existing_player_id:
                player_id = existing_player_id
                connected_players[request.sid] = player_id

                game = room_repository.get_game(room_code)
                if game and player_id in game.players:
                    game.players[player_id].reconnect(request.sid)
                    room_repository.save_game(room_code, game)

                    join_room(room_code)
                    emit('room_joined', {'room_code': room_code})

                    private_state = game_service.get_private_state(room_code, player_id)
                    if private_state:
                        emit('private_update', private_state)

                    if game.phase.value in ('lobby', 'role_selection') and game.selected_roles:
                        emit('roles_set', {'roles': game.selected_roles})

                    if game.phase.value == 'night_phase':
                        _emit_night_turn_sync(game, game_service, room_code)

                    game_service._emit_game_update(room_code)
                else:
                    emit('error', {'message': 'Error en la reconexión'})

            else:
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
        """Reconecta una sesión de jugador tras pérdida de conexión, cambio de app o recarga."""
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

            player = game.players[target_pid]
            player.reconnect(request.sid)
            connected_players[request.sid] = target_pid
            room_repository.save_game(room_code, game)
            join_room(room_code)

            print(f"✅ RECONEXIÓN EXITOSA: {player.name} ({target_pid}) en sala {room_code}")

            emit('reconnected_success', {
                'room_code': room_code,
                'player_name': player.name,
                'player_id': target_pid,
                'is_host': player.is_host,
                'phase': game.phase.value
            })
            emit('room_joined', {'room_code': room_code})

            if game.selected_roles:
                emit('roles_set', {'roles': game.selected_roles})

            private_state = game_service.get_private_state(room_code, target_pid)
            if private_state:
                emit('private_update', private_state)

            if game.phase.value == 'night_phase':
                current_turn = _emit_night_turn_sync(game, game_service, room_code)
                if current_turn and player.original_role == current_turn and current_turn != 'open_eyes':
                    action_data = game.get_night_action_data_for_player(target_pid)
                    if action_data:
                        emit('night_action', action_data)

            if game.phase.value == 'voting':
                emit('voting_started', {'room_code': room_code})

            if game.phase.value == 'game_end':
                reveal_data = game.get_reveal_data()
                emit('reveal', reveal_data)
                emit('game_end', reveal_data)

            game_service._emit_game_update(room_code)

        except Exception as e:
            print(f"❌ Error en reconnect_session: {e}")
            emit('reconnect_failed', {'message': 'Error interno al reconectar'})

    @socketio.on('set_discussion_timer')
    def on_set_discussion_timer(data):
        """El host selecciona la duración del temporizador de debate (120, 300, 600 segundos)."""
        try:
            duration = data.get('duration', 300) if data else 300
            if duration not in (120, 300, 600):
                emit('error', {'message': 'Duración inválida. Opciones: 120, 300, 600 segundos'})
                return

            player_id, room_code = _resolve_player_and_room(
                room_repository, game_service, connected_players, recover=True
            )
            if not player_id or not room_code:
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
        """Abandonar la sala actual con recuperación tolerante a desconexión."""
        try:
            player_id = connected_players.get(request.sid)
            room_code = None

            if data and isinstance(data, dict):
                room_code = data.get('room_code')
                name = data.get('player_name') or data.get('name')
                if not player_id and room_code and name:
                    player_id = find_existing_player_in_room(room_repository, room_code, name)

            if not player_id:
                recovered_id, recovered_room = recover_player_by_socket_or_host(room_repository, request.sid)
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

            emit('room_left')
            print(f"👋 leave_room ejecutado para sid={request.sid}, player_id={player_id}")

        except Exception as e:
            print(f"Error abandonando sala: {e}")
            emit('room_left')

    @socketio.on('set_roles')
    def on_set_roles(data):
        """El host selecciona los roles para la partida."""
        try:
            roles = data.get('roles', [])

            print("🔧 SET_ROLES - SISTEMA FIJO:")
            print(f"   request.sid: {request.sid}")
            print(f"   roles: {roles}")
            print(f"   connected_players actual: {connected_players}")

            if not roles:
                emit('error', {'message': 'Debe seleccionar roles'})
                return

            player_id, room_code = _resolve_player_and_room(
                room_repository, game_service, connected_players, recover=True
            )
            if not player_id or not room_code:
                return

            print(f"   player_id: {player_id}")
            print(f"   room_code: {room_code}")

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

                print(f"✅ EMITIENDO roles_set A TODA LA SALA {room_code}: {roles}")
                socketio.emit('roles_set', {'roles': roles}, room=room_code)
                emit('roles_set', {'roles': roles})
                print(f"✅ Roles establecidos y sincronizados en sala: {roles}")
            else:
                emit('error', {'message': 'No se pudieron establecer los roles'})

        except Exception as e:
            print(f"Error estableciendo roles: {e}")
            emit('error', {'message': 'Error interno del servidor'})

    @socketio.on('start_game')
    def on_start_game(data=None):
        """El host inicia la partida."""
        try:
            player_id, room_code = _resolve_player_and_room(
                room_repository, game_service, connected_players, recover=True
            )
            if not player_id or not room_code:
                return

            game = room_repository.get_game(room_code)
            if not game or player_id not in game.players:
                emit('error', {'message': 'Jugador no encontrado'})
                return

            if not game.players[player_id].is_host:
                emit('error', {'message': 'Solo el host puede iniciar el juego'})
                return

            success = game_service.start_game(room_code, player_id)
            if success:
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
            player_id, room_code = _resolve_player_and_room(
                room_repository, game_service, connected_players, recover=False
            )
            if not player_id or not room_code:
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
            player_id, room_code = _resolve_player_and_room(
                room_repository, game_service, connected_players, recover=False
            )
            if not player_id or not room_code:
                return

            target_id = data.get('target_player_id')
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
            player_id, room_code = _resolve_player_and_room(
                room_repository, game_service, connected_players, recover=False
            )
            if not player_id or not room_code:
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
        """El host reinicia la partida a LOBBY o ROLE_SELECTION."""
        try:
            player_id, room_code = _resolve_player_and_room(
                room_repository, game_service, connected_players, recover=False
            )
            if not player_id or not room_code:
                return

            to_phase = data.get('to_phase') if data else None
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
        """Un jugador ejecuta su acción nocturna."""
        try:
            player_id, room_code = _resolve_player_and_room(
                room_repository, game_service, connected_players, recover=False
            )
            if not player_id or not room_code:
                return

            action_data = data.get('action', {})
            result = game_service.execute_night_action(room_code, player_id, action_data)
            if not result.get('success'):
                emit('error', {'message': result.get('message', 'Acción no válida')})
            return result

        except Exception as e:
            print(f"Error ejecutando acción nocturna: {e}")
            emit('error', {'message': 'Error interno del servidor'})

    @socketio.on('get_game_state')
    def on_get_game_state(data=None):
        """Obtener el estado actual del juego."""
        try:
            player_id, room_code = _resolve_player_and_room(
                room_repository, game_service, connected_players, recover=False
            )
            if not player_id or not room_code:
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
        """Avanzar manualmente el turno durante la fase nocturna."""
        try:
            print(f"🔄 RECIBIDO ADVANCE_TURN de {request.sid}, data: {data}")

            player_id, room_code = _resolve_player_and_room(
                room_repository, game_service, connected_players, recover=False
            )
            if not player_id or not room_code:
                return

            print(f"✅ ADVANCE_TURN: Socket {request.sid} -> player_id: {player_id}")
            print(f"✅ ADVANCE_TURN: player_id {player_id} -> room_code: {room_code}")

            game = room_repository.get_game(room_code)
            if not game:
                print(f"❌ ADVANCE_TURN: No se encontró juego para sala {room_code}")
                emit('error', {'message': 'Sala no encontrada'})
                return

            if game.phase.value != 'night_phase':
                print(f"❌ ADVANCE_TURN: Fase incorrecta {game.phase.value}")
                emit('error', {'message': f'Solo se puede avanzar turno en night_phase, actual: {game.phase.value}'})
                return

            print(f"🔧 AVANZANDO TURNO MANUALMENTE: {player_id} para sala {room_code}")
            game_service.advance_turn(room_code)
            print(f"✅ ADVANCE_TURN: Turno avanzado correctamente para sala {room_code}")

        except Exception as e:
            print(f"❌ ERROR avanzando turno: {e}")
            emit('error', {'message': f'Error al avanzar turno: {str(e)}'})

