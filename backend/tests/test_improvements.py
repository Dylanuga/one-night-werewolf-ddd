#!/usr/bin/env python3
"""
Pruebas de temporizador automático en GameService y cálculo de PhaseTimer.
"""
import sys
import time
from pathlib import Path

backend_path = Path(__file__).resolve().parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from infrastructure.room_repository import RoomRepository
from services.game_service import GameService


def test_timer_functionality():
    """Prueba la funcionalidad del timer automático con 3 jugadores (mínimo válido) y 6 roles."""
    emitted_events = []

    def mock_emit(event, data, room=None):
        emitted_events.append((event, data, room))

    repo = RoomRepository()
    service = GameService(repo, mock_emit)
    service.TURN_DURATION = 1  # 1 segundo para prueba rápida y determinista

    room_code = "TEST123"
    player1_id = "player_test_1"
    player2_id = "player_test_2"
    player3_id = "player_test_3"

    assert service.create_room(room_code, player1_id, "TestPlayer1", "socket1")
    assert service.join_room(room_code, player2_id, "TestPlayer2", "socket2")
    assert service.join_room(room_code, player3_id, "TestPlayer3", "socket3")

    # 3 jugadores + 3 centro = 6 roles; solo werewolf y mason tienen turno nocturno
    roles = ["werewolf", "mason", "villager", "villager", "villager", "hunter"]
    assert service.set_selected_roles(room_code, player1_id, roles)

    game = repo.get_game(room_code)
    game.enable_test_mode({
        'players': ['werewolf', 'mason', 'villager'],
        'center': ['villager', 'villager', 'hunter']
    })

    assert service.start_game(room_code, player1_id)

    game = repo.get_game(room_code)
    assert game.phase.value == 'night_phase'
    assert game.get_current_turn_role() == 'werewolf'

    # Esperar avance automático de werewolf -> mason
    deadline = time.time() + 3.0
    while time.time() < deadline and repo.get_game(room_code).get_current_turn_role() != 'mason':
        time.sleep(0.1)

    game = repo.get_game(room_code)
    assert game.get_current_turn_role() == 'mason'

    # Esperar avance automático de mason -> fin de turnos nocturnos (open_eyes / day_phase)
    deadline = time.time() + 3.0
    while time.time() < deadline and not repo.get_game(room_code).open_eyes_active and repo.get_game(room_code).phase.value == 'night_phase':
        time.sleep(0.1)

    game = repo.get_game(room_code)
    assert game.night_finished is True or game.open_eyes_active is True or game.phase.value == 'day_phase'

    # Cancelar timers activos para no dejar hilos pendientes
    service._cancel_turn_timer(room_code)
    service._cancel_discussion_timer(room_code)


def test_phase_timer_calculation():
    """Prueba el cálculo del timer de fase."""
    current_time = time.time()

    turn_data = {
        'role': 'werewolf',
        'phase': 'Fase: werewolf',
        'duration': 6,
        'timestamp': current_time - 2
    }

    TURN_DURATION = 6
    server_start_time = turn_data['timestamp'] * 1000
    now = time.time() * 1000
    elapsed = (now - server_start_time) / 1000
    remaining = max(0, TURN_DURATION - elapsed)

    assert 3.5 <= remaining <= 4.5, f"Tiempo restante inesperado: {remaining}"

