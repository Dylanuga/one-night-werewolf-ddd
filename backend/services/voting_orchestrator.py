from typing import Any, Callable, Dict, Optional

from domain.game_logic import GamePhase
from infrastructure.room_repository import RoomRepository
from services.state_emitter import StateEmitter
from services.timer_manager import TimerManager


class VotingOrchestrator:
    """Orquesta la fase de votación, recepción de votos y revelación de resultados."""

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

    def start_voting_phase(self, room_code: str, host_id: Optional[str] = None, auto: bool = False) -> bool:
        """El host finaliza discusión o el temporizador expira e inicia votación."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return False
            if not auto:
                if not host_id or host_id not in game.players or not game.players[host_id].is_host:
                    return False

            self.timer_manager.cancel_discussion_timer(room_code)
            if not game.start_voting_phase():
                return False

            self.room_repository.save_game(room_code, game)
            self.state_emitter.emit_game_update(room_code)
            self.emit_callback('voting_started', {'room_code': room_code}, room=room_code)

            self.timer_manager.start_voting_timer(
                room_code,
                lambda rc: self.end_voting_phase(rc, host_id=None, force=True)
            )
            return True
        except Exception as e:
            print(f"Error en start_voting_phase: {e}")
            return False

    def submit_vote(self, room_code: str, player_id: str, target_id: str) -> Dict[str, Any]:
        """Registra un voto y finaliza partida si todos votaron."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return {'success': False, 'message': 'Sala no encontrada'}

            result = game.submit_vote(player_id, target_id)
            if result.get('success'):
                self.room_repository.save_game(room_code, game)
                self.state_emitter.emit_game_update(room_code)

                if result.get('all_connected_voted') or result.get('all_voted'):
                    def auto_finalize():
                        self.timer_manager.sleep_fn(1)
                        self.end_voting_phase(room_code, host_id=None, force=True)

                    self.timer_manager.start_background_task(auto_finalize)

            return result
        except Exception as e:
            print(f"Error en submit_vote: {e}")
            return {'success': False, 'message': 'Error interno del servidor'}

    def end_voting_phase(self, room_code: str, host_id: Optional[str] = None, force: bool = False) -> bool:
        """El host (o temporizador) finaliza votación y revela resultados."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return False
            if game.phase == GamePhase.GAME_END:
                return True
            if not force:
                if not host_id or host_id not in game.players or not game.players[host_id].is_host:
                    return False
                if not game.can_finalize(allow_partial=True):
                    return False

            self.timer_manager.cancel_voting_timer(room_code)
            game._finalize_game()
            self.room_repository.save_game(room_code, game)
            self.state_emitter.emit_game_update(room_code)
            reveal_data = game.get_reveal_data()
            self.emit_callback('reveal', reveal_data, room=room_code)
            self.emit_callback('game_end', reveal_data, room=room_code)
            return True
        except Exception as e:
            print(f"Error en end_voting_phase: {e}")
            return False

