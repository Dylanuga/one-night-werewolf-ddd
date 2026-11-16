import traceback
from typing import Callable, Dict, List, Optional

from domain.game_logic import GameLogic
from domain.roles import ROLE_METADATA
from infrastructure.room_repository import RoomRepository
from services.state_emitter import StateEmitter
from services.timer_manager import TimerManager


class RoomManager:
    """Gestiona el ciclo de vida de salas, jugadores, roles y configuración de partida."""

    VALID_ROLES = set(ROLE_METADATA.keys())

    def __init__(
        self,
        room_repository: RoomRepository,
        state_emitter: StateEmitter,
        timer_manager: TimerManager,
        emit_callback: Callable
    ):
        self.room_repository = room_repository
        self.state_emitter = state_emitter
        self.timer_manager = timer_manager
        self.emit_callback = emit_callback

    def create_room(self, room_code: str, host_id: str, host_name: str, socket_id: str) -> bool:
        """Crea una nueva sala de juego."""
        try:
            if self.room_repository.room_exists(room_code):
                return False

            game = GameLogic(room_code)
            success = game.add_player(host_id, host_name, socket_id, is_host=True)

            if success:
                self.room_repository.save_game(room_code, game)
                self.state_emitter.emit_game_update(room_code)
                print(f"[ROOM] creada {room_code} host={host_name} ({host_id})")
                return True
            return False
        except Exception as e:
            print(f"❌ ERROR en create_room: {e}")
            traceback.print_exc()
            return False

    def join_room(self, room_code: str, player_id: str, player_name: str, socket_id: str) -> bool:
        """Un jugador se une a una sala existente."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return False

            success = game.add_player(player_id, player_name, socket_id)
            if success:
                self.room_repository.save_game(room_code, game)
                self.state_emitter.emit_game_update(room_code)
                print(f"[ROOM] join {room_code} player={player_name} ({player_id})")
                return True
            return False
        except Exception as e:
            print(f"Error en join_room: {e}")
            return False

    def leave_room(self, room_code: str, player_id: str) -> bool:
        """Un jugador abandona la sala."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return False

            success = game.remove_player(player_id)
            if success:
                if not game.players:
                    self.room_repository.delete_game(room_code)
                    self.timer_manager.cancel_turn_timer(room_code)
                    self.timer_manager.cancel_discussion_timer(room_code)
                    self.timer_manager.cancel_voting_timer(room_code)
                else:
                    self.room_repository.save_game(room_code, game)
                    self.state_emitter.emit_game_update(room_code)
                return True
            return False
        except Exception as e:
            print(f"Error en leave_room: {e}")
            return False

    def set_selected_roles(self, room_code: str, player_id: str, roles: List[str]) -> bool:
        """El host selecciona los roles para la partida (validación relajada)."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                print(f"🔧 ERROR: Sala {room_code} no encontrada")
                return False

            if player_id not in game.players or not game.players[player_id].is_host:
                print(f"🔧 ERROR: {player_id} no es host o no existe")
                return False

            print("🔧 SINCRONIZANDO ROLES (sin validación estricta):")
            print(f"   Roles recibidos: {len(roles)} -> {roles}")

            if not roles:
                print("⏭️ SKIP: Lista de roles vacía, no actualizando")
                return True

            invalid_roles = [role for role in roles if role not in self.VALID_ROLES]
            if invalid_roles:
                print(f"❌ ERROR: Roles inválidos: {invalid_roles}")
                return False

            print("✅ ROLES VÁLIDOS - SINCRONIZANDO...")

            success = game.set_selected_roles(roles)
            if success:
                self.room_repository.save_game(room_code, game)
                self.state_emitter.emit_game_update(room_code)
                print(f"✅ ROLES SINCRONIZADOS EN {room_code}")
                return True

            print("❌ ERROR: game.set_selected_roles falló")
            return False
        except Exception as e:
            print(f"❌ ERROR en set_selected_roles: {e}")
            return False

    def start_game(self, room_code: str, player_id: str, on_game_started: Callable[[str], None]) -> bool:
        """El host inicia la partida aplicando validación estricta."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                print(f"❌ ERROR: Sala {room_code} no encontrada")
                return False

            if player_id not in game.players or not game.players[player_id].is_host:
                print(f"❌ ERROR: {player_id} no es host o no existe")
                return False

            player_count = len(game.players)
            required_roles = player_count + 3
            current_roles = game.selected_roles or []

            if len(current_roles) != required_roles:
                return False

            werewolf_count = current_roles.count('werewolf')
            if werewolf_count < 1:
                return False

            max_werewolves = max(1, player_count // 2)
            if werewolf_count > max_werewolves:
                return False

            success = game.start_game()
            if success:
                self.room_repository.save_game(room_code, game)
                self.state_emitter.emit_game_update(room_code)
                print(f"[GAME] iniciado sala {room_code} por {player_id}")
                on_game_started(room_code)
                return True

            print("❌ ERROR: game.start_game() falló")
            return False
        except Exception as e:
            print(f"❌ ERROR en start_game: {e}")
            return False

    def set_discussion_timer(self, room_code: str, host_id: str, duration: int) -> bool:
        """Configura la duración del debate en segundos (120, 300 o 600)."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return False
            if host_id not in game.players or not game.players[host_id].is_host:
                return False
            success = game.set_discussion_duration(duration)
            if success:
                self.room_repository.save_game(room_code, game)
                self.state_emitter.emit_game_update(room_code)
                print(f"⏱️ Duración de discusión actualizada a {duration}s en sala {room_code}")
            return success
        except Exception as e:
            print(f"Error en set_discussion_timer: {e}")
            return False

    def reset_game(self, room_code: str, player_id: str, to_phase: str) -> bool:
        """El host reinicia la partida a LOBBY o ROLE_SELECTION."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return False

            if player_id not in game.players or not game.players[player_id].is_host:
                return False

            success = game.reset_game(to_phase)
            if success:
                self.timer_manager.cancel_turn_timer(room_code)
                self.timer_manager.cancel_discussion_timer(room_code)
                self.timer_manager.cancel_voting_timer(room_code)
                self.room_repository.save_game(room_code, game)
                self.state_emitter.emit_game_update(room_code)
                self.emit_callback('game_reset', {'room_code': room_code, 'to_phase': to_phase}, room=room_code)
                if to_phase == "role_selection" and game.selected_roles:
                    self.emit_callback('roles_set', {'roles': game.selected_roles}, room=room_code)
                return True
            return False
        except Exception as e:
            print(f"Error en reset_game de GameService: {e}")
            return False

    def room_exists(self, room_code: str) -> bool:
        """Verifica si existe una sala."""
        try:
            return self.room_repository.room_exists(room_code)
        except Exception as e:
            print(f"Error en room_exists: {e}")
            return False

    def get_player_room(self, player_id: str) -> Optional[str]:
        """Encuentra la sala donde está un jugador."""
        try:
            return self.room_repository.find_player_room(player_id)
        except Exception as e:
            print(f"Error en get_player_room: {e}")
            return None

    def enable_test_mode(self, room_code: str, role_distribution: Dict[str, List[str]]) -> bool:
        """Activa el modo de prueba para una sala específica."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return False

            game.enable_test_mode(role_distribution)
            self.room_repository.save_game(room_code, game)
            return True
        except Exception as e:
            print(f"Error en enable_test_mode: {e}")
            return False

    def disable_test_mode(self, room_code: str) -> bool:
        """Desactiva el modo de prueba para una sala específica."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return False

            game.disable_test_mode()
            self.room_repository.save_game(room_code, game)
            return True
        except Exception as e:
            print(f"Error en disable_test_mode: {e}")
            return False

