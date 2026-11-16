import os
from functools import wraps
from typing import Dict

from flask import Flask, request

from domain.roles import ROLE_METADATA
from infrastructure.room_repository import RoomRepository
from main.session_manager import get_stable_player_id
from services.game_service import GameService


def require_test_endpoints(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if os.environ.get('ENABLE_TEST_ENDPOINTS', 'true').lower() not in ('true', '1', 'yes'):
            return {'error': 'Endpoints de prueba desactivados en este entorno'}, 403
        return f(*args, **kwargs)
    return decorated_function


def register_http_routes(
    app: Flask,
    game_service: GameService,
    room_repository: RoomRepository,
    connected_players: Dict[str, str]
):
    """Registra las rutas HTTP de testing y debug sobre la aplicación Flask."""

    @app.route('/test/create-test-room', methods=['POST'])
    @require_test_endpoints
    def create_test_room():
        """
        Crea una sala de prueba con código fijo 'TEST' y modo de prueba activado.
        """
        try:
            print("🧪 === CREANDO SALA DE PRUEBA TEST ===")

            data = request.get_json() or {}
            role_distribution = data.get('role_distribution')
            auto_start = data.get('auto_start', False)
            custom_player_names = data.get('player_names', [])
            turn_duration = data.get('turn_duration')

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

            valid_roles = set(ROLE_METADATA.keys())
            all_roles = players_roles + center_roles
            invalid_roles = [role for role in all_roles if role not in valid_roles]
            if invalid_roles:
                return {'error': f'Roles inválidos: {invalid_roles}. Válidos: {list(valid_roles)}'}, 400

            room_code = 'TEST'

            print("🧪 Configuración de prueba:")
            print(f"   - Jugadores: {len(players_roles)} -> {players_roles}")
            print(f"   - Centro: {len(center_roles)} -> {center_roles}")
            print(f"   - Auto-start: {auto_start}")

            if game_service.room_exists(room_code):
                print("🧪 Sala TEST ya existe, eliminándola...")
                game_service._cancel_turn_timer(room_code)
                game_service._cancel_discussion_timer(room_code)
                game_service._cancel_voting_timer(room_code)
                room_repository.delete_game(room_code)

            num_players = len(players_roles)
            test_players = []

            for i in range(num_players):
                if i < len(custom_player_names):
                    player_name = custom_player_names[i]
                else:
                    player_name = f"TestPlayer{i+1}"

                player_id = get_stable_player_id(player_name, room_code)
                socket_id = f"test_socket_{i+1}"
                test_players.append({
                    'id': player_id,
                    'name': player_name,
                    'socket_id': socket_id
                })

            print("🧪 Jugadores de prueba:")
            for player in test_players:
                print(f"   - {player['name']} (ID: {player['id']})")

            host_player = test_players[0]
            print(f"🧪 Creando sala con host: {host_player['name']}")

            success = game_service.create_room(room_code, host_player['id'], host_player['name'], host_player['socket_id'])
            if not success:
                return {'error': 'No se pudo crear la sala TEST'}, 500

            for player in test_players[1:]:
                print(f"🧪 Agregando jugador: {player['name']}")
                success = game_service.join_room(room_code, player['id'], player['name'], player['socket_id'])
                if not success:
                    return {'error': f'No se pudo agregar jugador {player["name"]}'}, 500

            print("🧪 Activando modo de prueba...")
            success = game_service.enable_test_mode(room_code, role_distribution)
            if not success:
                return {'error': 'No se pudo activar el modo de prueba'}, 500

            print("🧪 Estableciendo roles...")
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

            if isinstance(turn_duration, (int, float)) and 1 <= turn_duration <= 60:
                game_service.set_turn_duration(room_code, int(turn_duration))
                result['turn_duration'] = int(turn_duration)
            else:
                game_service.set_turn_duration(room_code, game_service.TURN_DURATION)
                result['turn_duration'] = game_service.TURN_DURATION

            if auto_start:
                print("🧪 Iniciando juego automáticamente...")
                success = game_service.start_game(room_code, host_player['id'])
                if success:
                    result['game_started'] = True
                    result['message'] += ' y juego iniciado automáticamente'
                    print("✅ Juego iniciado automáticamente")
                else:
                    result['game_started'] = False
                    result['warning'] = 'Sala creada pero no se pudo iniciar el juego'
                    print("⚠️ No se pudo iniciar el juego automáticamente")

            print("✅ Sala TEST creada exitosamente")
            return result, 200

        except Exception as e:
            print(f"❌ Error en create_test_room: {e}")
            return {'error': str(e)}, 500

    @app.route('/debug/rooms')
    @require_test_endpoints
    def debug_rooms():
        """Endpoint de debug."""
        try:
            rooms = room_repository.get_all_rooms()
            return {'rooms': rooms}
        except Exception as e:
            return {'error': str(e)}, 500

    @app.route('/debug/connections')
    @require_test_endpoints
    def debug_connections():
        """Endpoint de debug."""
        try:
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
        """Obtiene el estado actual de la sala TEST."""
        try:
            room_code = 'TEST'

            if not game_service.room_exists(room_code):
                return {'exists': False, 'message': 'Sala TEST no existe'}, 404

            game_state = game_service.get_game_state(room_code)
            if not game_state:
                return {'error': 'No se pudo obtener el estado del juego'}, 500

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
                        'is_connected': player.is_connected,
                        'has_live_tab': bool(player.is_connected and not str(getattr(player, 'socket_id', '')).startswith('test_socket_'))
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
        """Elimina la sala TEST si existe."""
        try:
            room_code = 'TEST'

            if game_service.room_exists(room_code):
                game_service._cancel_turn_timer(room_code)
                game_service._cancel_discussion_timer(room_code)
                game_service._cancel_voting_timer(room_code)
                room_repository.delete_game(room_code)
                print("🧪 Sala TEST eliminada")
                return {'message': 'Sala TEST eliminada exitosamente'}, 200
            else:
                return {'message': 'Sala TEST no existía'}, 200

        except Exception as e:
            print(f"Error en reset_test_room: {e}")
            return {'error': str(e)}, 500

    @app.route('/test/advance-turn', methods=['POST'])
    @require_test_endpoints
    def advance_test_turn():
        """Avanza manualmente el turno en la sala TEST (solo para debugging)."""
        try:
            room_code = 'TEST'

            if not game_service.room_exists(room_code):
                return {'error': 'Sala TEST no existe'}, 404

            game = room_repository.get_game(room_code)
            if not game:
                return {'error': 'No se pudo obtener el estado del juego'}, 500

            if game.phase.value != 'night_phase':
                return {'error': f'Solo se puede avanzar turno en night_phase, actual: {game.phase.value}'}, 400

            advanced = game_service.advance_turn(room_code)
            if advanced:
                game = room_repository.get_game(room_code)
                result = {
                    'message': 'Turno avanzado exitosamente',
                    'new_phase': game.phase.value if game else 'unknown',
                    'current_turn_role': game.get_current_turn_role() if game else None,
                    'night_finished': (game.phase.value == 'day_phase') if game else False
                }
                return result, 200
            else:
                return {'error': 'No se pudo avanzar el turno'}, 400

        except Exception as e:
            print(f"Error en advance_test_turn: {e}")
            return {'error': str(e)}, 500

    @app.route('/test/start-game', methods=['POST'])
    @require_test_endpoints
    def start_test_game():
        """Inicia manualmente la partida en la sala TEST cuando ya están conectadas las pestañas."""
        try:
            room_code = 'TEST'
            if not game_service.room_exists(room_code):
                return {'error': 'Sala TEST no existe'}, 404

            game = room_repository.get_game(room_code)
            if not game:
                return {'error': 'No se pudo obtener la sala TEST'}, 500

            host_player = next((p for p in game.players.values() if p.is_host), None)
            if not host_player:
                return {'error': 'No se encontró un host en la sala TEST'}, 400

            if game.phase.value not in ('lobby', 'role_selection'):
                return {'error': f'La partida ya está en fase {game.phase.value}'}, 400

            success = game_service.start_game(room_code, host_player.player_id)
            if not success:
                return {'error': 'No se pudo iniciar la partida en la sala TEST'}, 400

            return {
                'message': 'Partida iniciada en sala TEST',
                'phase': game.phase.value,
                'current_turn_role': game.get_current_turn_role()
            }, 200
        except Exception as e:
            print(f"Error en start_test_game: {e}")
            return {'error': str(e)}, 500

    @app.route('/test/presets')
    @require_test_endpoints
    def test_presets():
        """Devuelve configuraciones predefinidas para testing."""
        presets = {
            'hunter_vs_wolf': {
                'name': 'Cazador vs Lobo (4J)',
                'description': '1 cazador, 1 lobo, 1 vidente, 1 aldeano',
                'role_distribution': {
                    'players': ['hunter', 'werewolf', 'seer', 'villager'],
                    'center': ['robber', 'mason', 'villager']
                }
            },
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
        """Desactiva el modo de prueba para una sala."""
        try:
            success = game_service.disable_test_mode(room_code)
            if success:
                return {'message': 'Modo de prueba desactivado'}, 200
            else:
                return {'error': 'No se pudo desactivar el modo de prueba'}, 400
        except Exception as e:
            return {'error': str(e)}, 500

