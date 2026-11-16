import os
import sys
from pathlib import Path

import pytest

# Asegurar que backend/ esté en sys.path para todos los tests
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _cleanup_backend_state():
    """Limpia salas, temporizadores y sesiones conectadas entre tests."""
    from main.app import connected_players, game_service, room_repository

    for room_code in list(room_repository.get_all_rooms().keys()):
        game_service._cancel_turn_timer(room_code)
        game_service._cancel_discussion_timer(room_code)
        game_service._cancel_voting_timer(room_code)
        room_repository.delete_game(room_code)

    connected_players.clear()


@pytest.fixture
def app_instance():
    """Instancia de la aplicación Flask con estado limpio por test."""
    os.environ["ENABLE_TEST_ENDPOINTS"] = "true"
    from main.app import app

    _cleanup_backend_state()
    yield app
    _cleanup_backend_state()


@pytest.fixture
def client(app_instance):
    """Cliente HTTP de pruebas de Flask (sin servidor externo)."""
    with app_instance.test_client() as test_client:
        yield test_client


@pytest.fixture
def socketio_app(app_instance):
    """Instancia de Flask-SocketIO asociada a la app de pruebas."""
    from main.app import socketio

    return socketio


@pytest.fixture
def socket_client(app_instance, socketio_app):
    """Cliente Socket.IO de pruebas conectado a la app."""
    sc = socketio_app.test_client(app_instance)
    yield sc
    if sc.is_connected():
        sc.disconnect()

