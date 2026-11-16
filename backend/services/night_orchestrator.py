import time
import traceback
from typing import Any, Callable, Dict

from domain.game_logic import GamePhase
from infrastructure.room_repository import RoomRepository
from services.state_emitter import StateEmitter
from services.timer_manager import TimerManager


class NightOrchestrator:
    """Orquesta el flujo de turnos nocturnos, acciones y transición al día."""

    def __init__(
        self,
        room_repository: RoomRepository,
        state_emitter: StateEmitter,
        timer_manager: TimerManager,
        on_discussion_timeout: Callable[[str], None]
    ):
        self.room_repository = room_repository
        self.state_emitter = state_emitter
        self.timer_manager = timer_manager
        self.on_discussion_timeout = on_discussion_timeout

    def start_first_night_turn(self, room_code: str):
        """Inicia el primer turno nocturno."""
        try:
            print(f"🔧 _start_first_night_turn INICIADO para sala {room_code}")

            game = self.room_repository.get_game(room_code)
            if not game or game.phase != GamePhase.NIGHT_PHASE:
                print("🔧 ERROR: Game no válido o no en night_phase")
                return

            current_role = game.get_current_turn_role()
            print(f"🔧 PRIMER TURNO: role={current_role}")

            if not current_role:
                print("🔧 No hay turnos nocturnos, avanzando a día")
                self.start_open_eyes_phase(room_code)
                return

            print(f"🔧 Emitiendo turn_start para rol: {current_role}")
            self.state_emitter.emit_turn_start(room_code, current_role)

            print("🔧 Iniciando timer para el turno")
            self.timer_manager.start_turn_timer(room_code, self.auto_advance_turn)

            print(f"🔧 PRIMER TURNO INICIADO CORRECTAMENTE para rol: {current_role}")
        except Exception as e:
            print(f"❌ Error en start_first_night_turn: {e}")
            traceback.print_exc()

    def execute_night_action(self, room_code: str, player_id: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Un jugador ejecuta su acción nocturna."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return {'success': False, 'message': 'Sala no encontrada'}

            result = game.execute_night_action(player_id, action_data)

            if result.get('success'):
                self.room_repository.save_game(room_code, game)
                self.state_emitter.emit_to_player(room_code, player_id, 'action_result', result)
                private_state = game.get_private_state_for_player(player_id)
                self.state_emitter.emit_to_player(room_code, player_id, 'private_update', private_state)

            return result
        except Exception as e:
            print(f"Error en execute_night_action: {e}")
            return {'success': False, 'message': 'Error interno del servidor'}

    def auto_advance_turn(self, room_code: str):
        """Avanza automáticamente al siguiente turno cuando expira el timer."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game or game.phase != GamePhase.NIGHT_PHASE:
                return

            current_role_before = game.get_current_turn_role()
            print(f"[TIMER] fin sala {room_code} rol={current_role_before}")

            if current_role_before:
                auto_result = game.execute_current_turn_auto_action()
                if auto_result.get('success'):
                    target_pid = (
                        auto_result.get('player_id')
                        or auto_result.get(f'{current_role_before}_player_id')
                    )
                    if target_pid:
                        self.state_emitter.emit_to_player(room_code, target_pid, 'action_result', auto_result)

            advanced = game.advance_night_turn()
            self.room_repository.save_game(room_code, game)

            if not advanced:
                return

            if game.night_finished:
                self.room_repository.save_game(room_code, game)
                self.start_open_eyes_phase(room_code)
            else:
                current_role = game.get_current_turn_role()
                if not current_role:
                    return

                self.state_emitter.emit_turn_start(room_code, current_role)
                self.timer_manager.start_turn_timer(room_code, self.auto_advance_turn)

        except Exception as e:
            print(f"🔴 ERROR EN AUTO-AVANCE: {str(e)}")
            traceback.print_exc()

    def advance_turn(self, room_code: str) -> bool:
        """Avanza manualmente al siguiente turno."""
        try:
            print(f"🔧 AVANCE MANUAL DE TURNO para sala {room_code}")
            self.timer_manager.cancel_turn_timer(room_code)
            self.auto_advance_turn(room_code)
            return True
        except Exception as e:
            print(f"🔴 ERROR EN AVANCE MANUAL: {str(e)}")
            return False

    def start_open_eyes_phase(self, room_code: str):
        """Muestra mensaje de transición antes del día."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return

            game.open_eyes_active = True
            self.room_repository.save_game(room_code, game)

            self.state_emitter.emit_turn_start(room_code, 'open_eyes', duration_override=6)

            def finish_transition():
                try:
                    game_after = self.room_repository.get_game(room_code)
                    if not game_after:
                        return
                    game_after.open_eyes_active = False
                    game_after.phase = GamePhase.DAY_PHASE
                    game_after.night_finished = False
                    self.room_repository.save_game(room_code, game_after)
                    self.advance_to_day_phase(room_code)
                except Exception as e:
                    print(f"Error en finish_transition: {e}")

            def transition_task():
                game_now = self.room_repository.get_game(room_code)
                wait_sec = (
                    max(0.0, game_now.turn_end_timestamp - time.time())
                    if (game_now and game_now.turn_end_timestamp)
                    else 6
                )
                self.timer_manager.sleep_fn(wait_sec)
                finish_transition()

            self.timer_manager.start_background_task(transition_task)
        except Exception as e:
            print(f"Error en start_open_eyes_phase: {e}")

    def advance_to_day_phase(self, room_code: str):
        """Avanza a la fase de día e inicia el temporizador de debate."""
        try:
            self.timer_manager.cancel_turn_timer(room_code)
            game = self.room_repository.get_game(room_code)
            if not game:
                return

            game.phase = GamePhase.DAY_PHASE
            game.discussion_end_timestamp = time.time() + game.discussion_duration
            self.room_repository.save_game(room_code, game)
            self.state_emitter.emit_game_update(room_code)
            print(f"[PHASE] día en sala {room_code}, duración={game.discussion_duration}s")

            self.timer_manager.start_discussion_timer(room_code, self.on_discussion_timeout)
        except Exception as e:
            print(f"Error en advance_to_day_phase: {e}")

