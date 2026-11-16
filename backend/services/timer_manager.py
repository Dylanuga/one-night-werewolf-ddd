import time
import traceback
from typing import Callable, Dict

from domain.game_logic import GamePhase
from infrastructure.room_repository import RoomRepository


class TimerManager:
    """Motor de temporizadores y tokens por sala (turnos nocturnos, debate y votación)."""

    def __init__(
        self,
        room_repository: RoomRepository,
        start_background_task: Callable,
        sleep_fn: Callable,
        default_turn_duration_getter: Callable[[], int]
    ):
        self.room_repository = room_repository
        self.start_background_task = start_background_task
        self.sleep_fn = sleep_fn
        self._get_default_turn_duration = default_turn_duration_getter
        self.turn_timer_tokens: Dict[str, int] = {}
        self.discussion_timer_tokens: Dict[str, int] = {}
        self.voting_timer_tokens: Dict[str, int] = {}
        self.turn_duration_by_room: Dict[str, int] = {}

    def set_turn_duration(self, room_code: str, duration_seconds: int) -> bool:
        """Ajusta la duración del turno para una sala específica."""
        try:
            if not isinstance(duration_seconds, int) or duration_seconds < 1:
                return False
            self.turn_timer_tokens[room_code] = self.turn_timer_tokens.get(room_code, 0)
            self.turn_duration_by_room[room_code] = duration_seconds
            print(f"🕒 TURN_DURATION actualizado a {duration_seconds}s para sala {room_code}")
            return True
        except Exception as e:
            print(f"Error en set_turn_duration: {e}")
            return False

    def get_turn_duration(self, room_code: str) -> int:
        return self.turn_duration_by_room.get(room_code, self._get_default_turn_duration())

    def start_turn_timer(self, room_code: str, on_timeout: Callable[[str], None]):
        """Inicia un timer compatible con eventlet/threading para avanzar turno."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game or game.phase != GamePhase.NIGHT_PHASE:
                return

            current_role = game.get_current_turn_role()
            if not current_role:
                return

            token = self.turn_timer_tokens.get(room_code, 0) + 1
            self.turn_timer_tokens[room_code] = token

            def timer_task(expected_token: int):
                try:
                    game_now = self.room_repository.get_game(room_code)
                    if game_now and game_now.turn_end_timestamp:
                        wait_sec = max(0.0, game_now.turn_end_timestamp - time.time())
                    else:
                        wait_sec = self.get_turn_duration(room_code)
                    self.sleep_fn(wait_sec)

                    if self.turn_timer_tokens.get(room_code) != expected_token:
                        print(f"⚠️ Timer invalidado para sala {room_code}, token {expected_token}")
                        return

                    on_timeout(room_code)
                except Exception as e:
                    print(f"🔴 ERROR en timer_task para {room_code}: {str(e)}")

            self.start_background_task(timer_task, token)

            start_time = time.strftime("%H:%M:%S", time.localtime())
            expected_end = time.strftime(
                "%H:%M:%S",
                time.localtime(time.time() + self.get_turn_duration(room_code))
            )
            print(f"[TIMER] inicio sala {room_code} rol={current_role} dur={self.get_turn_duration(room_code)}s ({start_time} -> {expected_end})")

        except Exception as e:
            print(f"🔴 ERROR iniciando timer para {room_code}: {str(e)}")
            traceback.print_exc()

    def cancel_turn_timer(self, room_code: str):
        """Cancela el timer de turno para una sala invalidando su token."""
        try:
            if room_code in self.turn_timer_tokens:
                del self.turn_timer_tokens[room_code]
                print(f"🔧 TIMER CANCELADO (token invalidado) para sala {room_code}")
        except Exception as e:
            print(f"🔴 ERROR cancelando timer para {room_code}: {str(e)}")
            if room_code in self.turn_timer_tokens:
                del self.turn_timer_tokens[room_code]

    def start_discussion_timer(self, room_code: str, on_timeout: Callable[[str], None]):
        """Inicia el temporizador de debate en segundo plano."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game or game.phase != GamePhase.DAY_PHASE:
                return

            token = self.discussion_timer_tokens.get(room_code, 0) + 1
            self.discussion_timer_tokens[room_code] = token
            duration = game.discussion_duration

            def discussion_task(expected_token: int, wait_seconds: int):
                try:
                    self.sleep_fn(wait_seconds)
                    if self.discussion_timer_tokens.get(room_code) != expected_token:
                        return

                    print(f"⏰ [TIMER] Debate terminado en sala {room_code}. Iniciando votación automáticamente.")
                    on_timeout(room_code)
                except Exception as e:
                    print(f"Error en discussion_task: {e}")

            self.start_background_task(discussion_task, token, duration)
        except Exception as e:
            print(f"Error en start_discussion_timer: {e}")

    def cancel_discussion_timer(self, room_code: str):
        """Cancela el temporizador de debate."""
        try:
            if room_code in self.discussion_timer_tokens:
                del self.discussion_timer_tokens[room_code]
        except Exception as e:
            print(f"Error en cancel_discussion_timer: {e}")

    def start_voting_timer(self, room_code: str, on_timeout: Callable[[str], None]):
        """Inicia el temporizador de votación en segundo plano."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game or game.phase != GamePhase.VOTING:
                return

            token = self.voting_timer_tokens.get(room_code, 0) + 1
            self.voting_timer_tokens[room_code] = token
            duration = game.voting_duration

            def voting_task(expected_token: int, wait_seconds: int):
                try:
                    self.sleep_fn(wait_seconds)
                    if self.voting_timer_tokens.get(room_code) != expected_token:
                        return

                    print(f"⏰ [TIMER] Tiempo de votación terminado en sala {room_code}. Finalizando con votos emitidos.")
                    on_timeout(room_code)
                except Exception as e:
                    print(f"Error en voting_task: {e}")

            self.start_background_task(voting_task, token, duration)
        except Exception as e:
            print(f"Error en start_voting_timer: {e}")

    def cancel_voting_timer(self, room_code: str):
        """Cancela el temporizador de votación."""
        try:
            if room_code in self.voting_timer_tokens:
                del self.voting_timer_tokens[room_code]
        except Exception as e:
            print(f"Error en cancel_voting_timer: {e}")

