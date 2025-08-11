# backend/infrastructure/room_repository.py
import json
from typing import Dict, Optional
from domain.game_logic import GameLogic

class RoomRepository:
    """Repositorio para persistir el estado de las salas de juego"""
    
    def __init__(self):
        # En memoria para desarrollo - usar Redis en producción
        self._games: Dict[str, GameLogic] = {}
    
    def save_game(self, room_code: str, game: GameLogic):
        """Guarda el estado de una partida"""
        self._games[room_code] = game
    
    def get_game(self, room_code: str) -> Optional[GameLogic]:
        """Obtiene una partida por código de sala"""
        return self._games.get(room_code)
    
    def delete_game(self, room_code: str) -> bool:
        """Elimina una partida"""
        if room_code in self._games:
            del self._games[room_code]
            return True
        return False
    
    def room_exists(self, room_code: str) -> bool:
        """Verifica si existe una sala"""
        return room_code in self._games
    
    def find_player_room(self, player_id: str) -> Optional[str]:
        """Encuentra en qué sala está un jugador"""
        for room_code, game in self._games.items():
            if player_id in game.players:
                return room_code
        return None
    
    def get_all_rooms(self) -> Dict[str, Dict]:
        """Obtiene un resumen de todas las salas (para debug)"""
        rooms = {}
        for room_code, game in self._games.items():
            rooms[room_code] = {
                'phase': game.phase.value,
                'player_count': len(game.players),
                'players': [p.name for p in game.players.values()],
                'current_turn': game.get_current_turn_role()
            }
        return rooms

# Implementación con Redis para producción (FUTURO)
class RedisRoomRepository(RoomRepository):
    """Implementación del repositorio usando Redis para producción"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.key_prefix = "werewolf_game:"
    
    def save_game(self, room_code: str, game: GameLogic):
        """Guarda el estado de una partida en Redis"""
        key = f"{self.key_prefix}{room_code}"
        
        # Serializar el estado del juego
        game_state = {
            'room_code': game.room_code,
            'phase': game.phase.value,
            'players': {pid: self._serialize_player(p) for pid, p in game.players.items()},
            'selected_roles': game.selected_roles,
            'center_cards': game.center_cards,
            'current_turn_index': game.current_turn_index,
            'night_turns': game.night_turns,
            'game_logs': game.game_logs,
            'max_players': game.max_players
        }
        
        # Guardar en Redis con expiración de 24 horas
        self.redis.setex(key, 86400, json.dumps(game_state))
    
    def get_game(self, room_code: str) -> Optional[GameLogic]:
        """Obtiene una partida desde Redis"""
        key = f"{self.key_prefix}{room_code}"
        data = self.redis.get(key)
        
        if not data:
            return None
        
        try:
            game_state = json.loads(data)
            return self._deserialize_game(game_state)
        except (json.JSONDecodeError, KeyError):
            return None
    
    def delete_game(self, room_code: str) -> bool:
        """Elimina una partida de Redis"""
        key = f"{self.key_prefix}{room_code}"
        return self.redis.delete(key) > 0
    
    def room_exists(self, room_code: str) -> bool:
        """Verifica si existe una sala en Redis"""
        key = f"{self.key_prefix}{room_code}"
        return self.redis.exists(key)
    
    def find_player_room(self, player_id: str) -> Optional[str]:
        """Encuentra en qué sala está un jugador (búsqueda en Redis)"""
        pattern = f"{self.key_prefix}*"
        for key in self.redis.scan_iter(pattern):
            try:
                data = self.redis.get(key)
                if data:
                    game_state = json.loads(data)
                    if player_id in game_state.get('players', {}):
                        return game_state['room_code']
            except (json.JSONDecodeError, KeyError):
                continue
        return None
    
    def get_all_rooms(self) -> Dict[str, Dict]:
        """Obtiene un resumen de todas las salas desde Redis"""
        rooms = {}
        pattern = f"{self.key_prefix}*"
        for key in self.redis.scan_iter(pattern):
            try:
                data = self.redis.get(key)
                if data:
                    game_state = json.loads(data)
                    room_code = game_state['room_code']
                    rooms[room_code] = {
                        'phase': game_state['phase'],
                        'player_count': len(game_state['players']),
                        'players': [p['name'] for p in game_state['players'].values()]
                    }
            except (json.JSONDecodeError, KeyError):
                continue
        return rooms
    
    def _serialize_player(self, player) -> Dict:
        """Serializa un objeto Player"""
        return {
            'player_id': player.player_id,
            'name': player.name,
            'socket_id': player.socket_id,
            'is_host': player.is_host,
            'role': player.get_role_name() if player.role else None,
            'original_role': player.original_role,
            'is_connected': player.is_connected
        }
    
    def _deserialize_game(self, game_state: Dict) -> GameLogic:
        """Deserializa el estado del juego desde JSON"""
        from domain.game_logic import GamePhase
        from domain.player import Player
        
        game = GameLogic(game_state['room_code'])
        game.phase = GamePhase(game_state['phase'])
        game.selected_roles = game_state['selected_roles']
        game.center_cards = game_state['center_cards']
        game.current_turn_index = game_state['current_turn_index']
        game.night_turns = game_state['night_turns']
        game.game_logs = game_state['game_logs']
        game.max_players = game_state['max_players']
        
        # Recrear jugadores
        for pid, pdata in game_state['players'].items():
            player = Player(
                pdata['player_id'],
                pdata['name'],
                pdata['socket_id'],
                pdata['is_host']
            )
            player.original_role = pdata['original_role']
            player.is_connected = pdata['is_connected']
            
            if pdata['role'] and pdata['role'] != 'sin_rol':
                player.assign_role(pdata['role'])
            
            game.players[pid] = player
        
        return game