# backend/services/game_service.py
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from infrastructure.room_repository import RoomRepository
from services.night_orchestrator import NightOrchestrator
from services.room_manager import RoomManager
from services.state_emitter import StateEmitter
from services.timer_manager import TimerManager
from services.voting_orchestrator import VotingOrchestrator


def _default_background_task(target: Callable, *args: Any, **kwargs: Any):
    """Fallback seguro basado en hilos daemon cuando no se inyecta Socket.IO."""
    thread = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True)
    thread.start()
    return thread


class GameService:
    """Fachada de aplicación que coordina los módulos de gestión, fases y emisión."""

    def __init__(
        self,
        room_repository: RoomRepository,
        emit_callback: Callable,
        start_background_task: Optional[Callable] = None,
        sleep_fn: Optional[Callable] = None
    ):
        self.room_repository = room_repository
        self.emit_callback = emit_callback
        self.start_background_task = start_background_task or _default_background_task
        self.sleep_fn = sleep_fn or time.sleep
        self.TURN_DURATION = 12  # segundos (default)

        self.timer_manager = TimerManager(
            room_repository=room_repository,
            start_background_task=self.start_background_task,
            sleep_fn=self.sleep_fn,
            default_turn_duration_getter=lambda: self.TURN_DURATION
        )
        # Alias directos para compatibilidad con inspecciones o tests existentes
        self.turn_timer_tokens = self.timer_manager.turn_timer_tokens
        self.discussion_timer_tokens = self.timer_manager.discussion_timer_tokens
        self.voting_timer_tokens = self.timer_manager.voting_timer_tokens
        self.turn_duration_by_room = self.timer_manager.turn_duration_by_room

        self.state_emitter = StateEmitter(
            room_repository=room_repository,
            emit_callback=emit_callback,
            get_turn_duration=self.timer_manager.get_turn_duration
        )
        self.voting_orchestrator = VotingOrchestrator(
            room_repository=room_repository,
            state_emitter=self.state_emitter,
            timer_manager=self.timer_manager,
            emit_callback=emit_callback
        )
        self.night_orchestrator = NightOrchestrator(
            room_repository=room_repository,
            state_emitter=self.state_emitter,
            timer_manager=self.timer_manager,
            on_discussion_timeout=lambda rc: self.voting_orchestrator.start_voting_phase(rc, host_id=None, auto=True)
        )
        self.room_manager = RoomManager(
            room_repository=room_repository,
            state_emitter=self.state_emitter,
            timer_manager=self.timer_manager,
            emit_callback=emit_callback
        )

    # --- Gestión de salas y jugadores ---

    def create_room(self, room_code: str, host_id: str, host_name: str, socket_id: str) -> bool:
        """Crea una nueva sala de juego."""
        return self.room_manager.create_room(room_code, host_id, host_name, socket_id)

    def join_room(self, room_code: str, player_id: str, player_name: str, socket_id: str) -> bool:
        """Un jugador se une a una sala existente."""
        return self.room_manager.join_room(room_code, player_id, player_name, socket_id)

    def leave_room(self, room_code: str, player_id: str) -> bool:
        """Un jugador abandona la sala."""
        return self.room_manager.leave_room(room_code, player_id)

    def set_selected_roles(self, room_code: str, player_id: str, roles: List[str]) -> bool:
        """El host selecciona los roles para la partida."""
        return self.room_manager.set_selected_roles(room_code, player_id, roles)

    def start_game(self, room_code: str, player_id: str) -> bool:
        """El host inicia la partida."""
        return self.room_manager.start_game(
            room_code,
            player_id,
            on_game_started=self.night_orchestrator.start_first_night_turn
        )

    def set_discussion_timer(self, room_code: str, host_id: str, duration: int) -> bool:
        """Configura la duración del debate en segundos (120, 300 o 600)."""
        return self.room_manager.set_discussion_timer(room_code, host_id, duration)

    def reset_game(self, room_code: str, player_id: str, to_phase: str) -> bool:
        """El host reinicia la partida a LOBBY o ROLE_SELECTION."""
        return self.room_manager.reset_game(room_code, player_id, to_phase)

    def room_exists(self, room_code: str) -> bool:
        """Verifica si existe una sala."""
        return self.room_manager.room_exists(room_code)

    def get_player_room(self, player_id: str) -> Optional[str]:
        """Encuentra la sala donde está un jugador."""
        return self.room_manager.get_player_room(player_id)

    def enable_test_mode(self, room_code: str, role_distribution: Dict[str, List[str]]) -> bool:
        """Activa el modo de prueba para una sala específica."""
        return self.room_manager.enable_test_mode(room_code, role_distribution)

    def disable_test_mode(self, room_code: str) -> bool:
        """Desactiva el modo de prueba para una sala específica."""
        return self.room_manager.disable_test_mode(room_code)

    # --- Temporizadores ---

    def set_turn_duration(self, room_code: str, duration_seconds: int) -> bool:
        """Ajusta la duración del turno para una sala específica."""
        return self.timer_manager.set_turn_duration(room_code, duration_seconds)

    def _get_turn_duration(self, room_code: str) -> int:
        return self.timer_manager.get_turn_duration(room_code)

    def _start_turn_timer(self, room_code: str):
        self.timer_manager.start_turn_timer(room_code, self._auto_advance_turn)

    def _cancel_turn_timer(self, room_code: str):
        self.timer_manager.cancel_turn_timer(room_code)

    def _start_discussion_timer(self, room_code: str):
        self.timer_manager.start_discussion_timer(
            room_code,
            lambda rc: self.start_voting_phase(rc, host_id=None, auto=True)
        )

    def _cancel_discussion_timer(self, room_code: str):
        self.timer_manager.cancel_discussion_timer(room_code)

    def _start_voting_timer(self, room_code: str):
        self.timer_manager.start_voting_timer(
            room_code,
            lambda rc: self.end_voting_phase(rc, host_id=None, force=True)
        )

    def _cancel_voting_timer(self, room_code: str):
        self.timer_manager.cancel_voting_timer(room_code)

    # --- Orquestación nocturna ---

    def _start_first_night_turn(self, room_code: str):
        self.night_orchestrator.start_first_night_turn(room_code)

    def execute_night_action(self, room_code: str, player_id: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Un jugador ejecuta su acción nocturna."""
        return self.night_orchestrator.execute_night_action(room_code, player_id, action_data)

    def _auto_advance_turn(self, room_code: str):
        self.night_orchestrator.auto_advance_turn(room_code)

    def advance_turn(self, room_code: str):
        """Avanza manualmente al siguiente turno."""
        return self.night_orchestrator.advance_turn(room_code)

    def _start_open_eyes_phase(self, room_code: str):
        self.night_orchestrator.start_open_eyes_phase(room_code)

    def _advance_to_day_phase(self, room_code: str):
        self.night_orchestrator.advance_to_day_phase(room_code)

    # --- Orquestación de votación ---

    def start_voting_phase(self, room_code: str, host_id: Optional[str] = None, auto: bool = False) -> bool:
        """El host finaliza discusión o el temporizador expira e inicia votación."""
        return self.voting_orchestrator.start_voting_phase(room_code, host_id=host_id, auto=auto)

    def submit_vote(self, room_code: str, player_id: str, target_id: str) -> Dict[str, Any]:
        """Registra un voto y finaliza partida si todos votaron."""
        return self.voting_orchestrator.submit_vote(room_code, player_id, target_id)

    def end_voting_phase(self, room_code: str, host_id: Optional[str] = None, force: bool = False) -> bool:
        """El host (o temporizador) finaliza votación y revela resultados."""
        return self.voting_orchestrator.end_voting_phase(room_code, host_id=host_id, force=force)

    # --- Emisión y consulta de estado ---

    def _emit_game_update(self, room_code: str):
        self.state_emitter.emit_game_update(room_code)

    def _emit_turn_start(self, room_code: str, role: str, duration_override: Optional[int] = None):
        self.state_emitter.emit_turn_start(room_code, role, duration_override=duration_override)

    def _emit_werewolf_turn_data(self, room_code: str):
        self.state_emitter.emit_werewolf_turn_data(room_code)

    def _emit_mason_turn_data(self, room_code: str):
        self.state_emitter.emit_mason_turn_data(room_code)

    def _emit_to_player(self, room_code: str, player_id: str, event: str, data: Any):
        self.state_emitter.emit_to_player(room_code, player_id, event, data)

    def get_game_state(self, room_code: str, player_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Obtiene el estado del juego."""
        return self.state_emitter.get_game_state(room_code, player_id=player_id)

    def get_private_state(self, room_code: str, player_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el estado privado de un jugador específico."""
        return self.state_emitter.get_private_state(room_code, player_id)
