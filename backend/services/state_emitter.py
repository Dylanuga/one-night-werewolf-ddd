import time
import traceback
from typing import Any, Callable, Dict, Optional

from domain.game_logic import GamePhase
from infrastructure.room_repository import RoomRepository


class StateEmitter:
    """Gestiona la emisión y lectura de estados públicos y privados hacia Socket.IO."""

    def __init__(
        self,
        room_repository: RoomRepository,
        emit_callback: Callable,
        get_turn_duration: Callable[[str], int]
    ):
        self.room_repository = room_repository
        self.emit_callback = emit_callback
        self.get_turn_duration = get_turn_duration

    def emit_game_update(self, room_code: str):
        """Emite actualización del estado del juego a todos los jugadores."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return

            public_state = game.get_public_state()
            self.emit_callback('game_update', public_state, room=room_code)

            current_turn_role = game.get_current_turn_role()

            for player_id, player in game.players.items():
                if not (player.is_connected and player.socket_id):
                    continue
                try:
                    private_state = game.get_private_state_for_player(player_id)

                    if (
                        current_turn_role in ('werewolf', 'mason', 'seer')
                        and player.original_role == current_turn_role
                        and game.phase == GamePhase.NIGHT_PHASE
                    ):
                        night_action_data = game.get_night_action_data_for_player(player_id)
                        if night_action_data:
                            private_state['night_action'] = night_action_data
                            private_state['current_turn_role'] = current_turn_role
                            private_state['is_your_turn'] = True
                            self.emit_callback('private_update', private_state, room=player.socket_id)
                            self.emit_callback('night_action', night_action_data, room=player.socket_id)
                            continue

                    self.emit_callback('private_update', private_state, room=player.socket_id)

                except Exception as player_error:
                    print(f"❌ Error emitiendo a jugador {player_id}: {player_error}")
                    traceback.print_exc()
                    continue
        except Exception as e:
            print(f"❌ Error en emit_game_update: {e}")
            traceback.print_exc()

    def emit_turn_start(self, room_code: str, role: str, duration_override: Optional[int] = None):
        """Emite el evento de inicio de turno y actualiza estados privados de manera unificada."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return

            turn_timestamp = time.time()
            duration = duration_override if duration_override is not None else self.get_turn_duration(room_code)
            game.turn_duration = duration
            game.turn_start_timestamp = turn_timestamp
            game.turn_end_timestamp = turn_timestamp + duration
            self.room_repository.save_game(room_code, game)

            turn_data = {
                'role': role,
                'phase': f'Fase: {role}',
                'duration': duration,
                'timestamp': turn_timestamp,
                'end_timestamp': game.turn_end_timestamp,
                'server_time': turn_timestamp,
                'remaining': float(duration)
            }

            self.emit_callback('turn_start', turn_data, room=room_code)

            for player_id, player in game.players.items():
                if not (player.is_connected and player.socket_id):
                    continue
                try:
                    private_state = game.get_private_state_for_player(player_id)

                    private_state['turn_timestamp'] = turn_timestamp
                    private_state['turn_end_timestamp'] = game.turn_end_timestamp
                    private_state['turn_duration'] = duration
                    private_state['turn_remaining'] = max(0.0, game.turn_end_timestamp - time.time())
                    private_state['current_turn_role'] = role
                    private_state['is_your_turn'] = (player.original_role == role) and (role != 'open_eyes')

                    if private_state['is_your_turn']:
                        night_action_data = game.get_night_action_data_for_player(player_id)
                        if night_action_data:
                            private_state['night_action'] = night_action_data

                    self.emit_callback('private_update', private_state, room=player.socket_id)

                except Exception as player_error:
                    print(f"⚠️ Error emitiendo private_update unificado a {player_id}: {str(player_error)}")
                    continue

        except Exception as e:
            print(f"Error en emit_turn_start: {e}")

    def _emit_role_turn_data(self, room_code: str, role_name: str):
        """Emite datos específicos de acción nocturna para todos los jugadores con un rol dado."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return

            role_players = [
                player_id for player_id, player in game.players.items()
                if player.get_role_name() == role_name
            ]

            for player_id in role_players:
                try:
                    night_action_data = game.get_night_action_data_for_player(player_id)
                    if night_action_data:
                        self.emit_to_player(room_code, player_id, 'night_action', night_action_data)

                        private_state = game.get_private_state_for_player(player_id)
                        if private_state:
                            private_state['night_action'] = night_action_data
                            private_state['current_turn_role'] = role_name
                            private_state['is_your_turn'] = True
                            self.emit_to_player(room_code, player_id, 'private_update', private_state)
                except Exception as player_error:
                    print(f"❌ Error emitiendo acción nocturna ({role_name}) a {player_id}: {player_error}")
                    continue
        except Exception as e:
            print(f"❌ Error en _emit_role_turn_data ({role_name}): {e}")

    def emit_werewolf_turn_data(self, room_code: str):
        """Emite datos específicos para el turno de los lobos."""
        self._emit_role_turn_data(room_code, 'werewolf')

    def emit_mason_turn_data(self, room_code: str):
        """Emite datos específicos para el turno de los masones."""
        self._emit_role_turn_data(room_code, 'mason')

    def emit_to_player(self, room_code: str, player_id: str, event: str, data: Any):
        """Emite un evento a un jugador específico."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game or player_id not in game.players:
                return

            player = game.players[player_id]
            if player.is_connected and player.socket_id:
                print(f"🔧 EMITIENDO {event} A JUGADOR {player_id} (socket: {player.socket_id})")
                self.emit_callback(event, data, room=player.socket_id)
        except Exception as e:
            print(f"Error en emit_to_player para {player_id}: {e}")

    def get_game_state(self, room_code: str, player_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Obtiene el estado del juego."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return None

            if player_id and player_id in game.players:
                return game.get_private_state_for_player(player_id)
            return game.get_public_state()
        except Exception as e:
            print(f"Error en get_game_state: {e}")
            return None

    def get_private_state(self, room_code: str, player_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el estado privado de un jugador específico."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game or player_id not in game.players:
                return None

            private_state = game.get_private_state_for_player(player_id)

            if game.phase == GamePhase.NIGHT_PHASE:
                current_turn_role = game.get_current_turn_role()
                if current_turn_role:
                    private_state['current_turn_role'] = current_turn_role
                    player_role = game.players[player_id].original_role
                    private_state['is_your_turn'] = (player_role == current_turn_role)

                    if private_state['is_your_turn']:
                        night_action_data = game.get_night_action_data_for_player(player_id)
                        if night_action_data:
                            private_state['night_action'] = night_action_data

            return private_state
        except Exception as e:
            print(f"Error en get_private_state: {e}")
            return None

