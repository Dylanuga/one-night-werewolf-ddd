import secrets
import string
from typing import Dict, Optional, Tuple

from infrastructure.room_repository import RoomRepository

# Mapeo de socket_id a player_id estable
connected_players: Dict[str, str] = {}


def generate_room_code() -> str:
    """Genera un código de sala aleatorio de 4 caracteres."""
    return ''.join(secrets.choice(string.ascii_uppercase) for _ in range(4))


def get_stable_player_id(player_name: str, room_code: str) -> str:
    """Genera un player_id estable basado en nombre y sala."""
    return f"player_{room_code}_{player_name}".replace(" ", "_")


def find_existing_player_in_room(
    room_repository: RoomRepository,
    room_code: str,
    player_name: str
) -> Optional[str]:
    """Busca si ya existe un jugador con ese nombre en la sala."""
    try:
        game = room_repository.get_game(room_code)
        if not game:
            return None

        for player_id, player in game.players.items():
            if player.name == player_name:
                print(f"🔧 JUGADOR EXISTENTE ENCONTRADO: {player_id} ({player_name})")
                return player_id

        return None
    except Exception as e:
        print(f"Error buscando jugador existente: {e}")
        return None


def recover_player_by_socket_or_host(
    room_repository: RoomRepository,
    request_sid: str
) -> Tuple[Optional[str], Optional[str]]:
    """
    Intenta recuperar un player_id basado en el socket_id o asumiendo que es el host.
    Retorna (player_id, room_code) o (None, None) si no se puede recuperar.
    """
    try:
        all_rooms = room_repository.get_all_rooms()
        print(f"🔍 Buscando en {len(all_rooms)} salas...")
        for room_code in all_rooms:
            game = room_repository.get_game(room_code)
            if not game:
                continue
            print(f"🔍 Revisando sala {room_code} con {len(game.players)} jugadores...")
            for player_id, player in game.players.items():
                print(f"🔍   - Jugador {player_id}: socket_id={getattr(player, 'socket_id', 'NONE')}, is_host={player.is_host}")

                # Estrategia 1: Coincidencia exacta de socket_id
                if hasattr(player, 'socket_id') and player.socket_id == request_sid:
                    print(f"🔧 RECUPERADO POR SOCKET: {player_id} en sala {room_code}")
                    return player_id, room_code

                # Estrategia 2: Si es host y no hay socket_id válido, asumir reconexión
                if player.is_host and (not hasattr(player, 'socket_id') or player.socket_id != request_sid):
                    print(f"🔧 CANDIDATO HOST ENCONTRADO: {player_id} ({player.name}) en sala {room_code}")
                    player.socket_id = request_sid
                    room_repository.save_game(room_code, game)
                    print(f"🔧 RECUPERADO POR HOST: {player_id} actualizado con nuevo socket {request_sid}")
                    return player_id, room_code

        return None, None
    except Exception as e:
        print(f"❌ Error en recuperación: {e}")
        return None, None

