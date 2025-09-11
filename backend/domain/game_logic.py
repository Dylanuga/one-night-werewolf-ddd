# GameLogic: reglas del juego y turnos

import random
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from .player import Player
from .roles import RoleFactory

class GamePhase(Enum):
    LOBBY = "lobby"
    ROLE_SELECTION = "role_selection"
    NIGHT_PHASE = "night_phase"
    DAY_PHASE = "day_phase"
    VOTING = "voting"
    GAME_END = "game_end"

class GameLogic:
    """Lógica de dominio pura para el juego One Night Werewolf"""
    
    def __init__(self, room_code: str):
        self.room_code = room_code
        self.phase = GamePhase.LOBBY
        self.players: Dict[str, Player] = {}
        self.selected_roles: List[str] = []
        self.center_cards: List[str] = []
        self.current_turn_index = 0
        self.night_turns: List[str] = []  # Lista ordenada de player_ids con turnos nocturnos
        self.game_logs: List[Dict[str, Any]] = []
        self.max_players = 8  # 🔧 Aumentado para más flexibilidad
        self.test_mode = False
        self.test_role_distribution = None  # Para asignar roles específicos en pruebas
    
    def add_player(self, player_id: str, name: str, socket_id: str, is_host: bool = False) -> bool:
        """Añade un jugador a la sala"""
        if len(self.players) >= self.max_players:
            return False
        
        if self.phase != GamePhase.LOBBY:
            return False
        
        if player_id in self.players:
            # Reconexión
            self.players[player_id].reconnect(socket_id)
            return True
        
        self.players[player_id] = Player(player_id, name, socket_id, is_host)
        self.add_log(f"{name} se unió a la sala")
        return True
    
    def remove_player(self, player_id: str) -> bool:
        """Remueve un jugador de la sala"""
        if player_id not in self.players:
            return False
        
        player = self.players[player_id]
        self.add_log(f"{player.name} salió de la sala")
        
        # Si era el host, transferir host al siguiente jugador
        if player.is_host and len(self.players) > 1:
            next_player = next(p for pid, p in self.players.items() if pid != player_id)
            next_player.is_host = True
            self.add_log(f"{next_player.name} es ahora el host")
        
        del self.players[player_id]
        return True
    
    def set_selected_roles(self, roles: List[str]) -> bool:
        """Establece los roles seleccionados para la partida"""
        if self.phase != GamePhase.LOBBY:
            return False
        
        # Validar que hay suficientes roles (jugadores + 3 cartas del centro)
        required_roles = len(self.players) + 3
        if len(roles) != required_roles:
            return False
        
        # 🔧 FIX: Permitir cualquier número de lobos (mínimo 1 para que el juego tenga sentido)
        werewolf_count = roles.count('werewolf')
        if werewolf_count < 1:
            return False
        
        self.selected_roles = roles.copy()
        self.phase = GamePhase.ROLE_SELECTION
        return True
    
    def enable_test_mode(self, role_distribution: Dict[str, List[str]] = None):
        """
        Activa el modo de prueba y opcionalmente establece una distribución específica de roles.
        
        Args:
            role_distribution: Diccionario con la distribución de roles.
                Ejemplo: {
                    'players': ['werewolf', 'villager', 'villager', 'villager'],
                    'center': ['werewolf', 'villager', 'villager']
                }
        """
        self.test_mode = True
        self.test_role_distribution = role_distribution
        self.add_log("🧪 Modo de prueba activado")
    
    def disable_test_mode(self):
        """Desactiva el modo de prueba"""
        self.test_mode = False
        self.test_role_distribution = None
        self.add_log("🎲 Modo de prueba desactivado")
    
    def start_game(self) -> bool:
        """Inicia la partida distribuyendo roles y comenzando la fase nocturna"""
        if self.phase != GamePhase.ROLE_SELECTION:
            return False
        
        if not self.selected_roles:
            return False
        
        # 🔧 DEBUG: Añadido para verificar distribución
        print(f"🔍 ROLES ORIGINALES: {self.selected_roles}")
        
        # Usar distribución de prueba o mezclar aleatoriamente
        if self.test_mode and self.test_role_distribution:
            shuffled_roles = (
                self.test_role_distribution['players'] + 
                self.test_role_distribution['center']
            )
        else:
            shuffled_roles = self.selected_roles.copy()
            random.shuffle(shuffled_roles)
        
        print(f"🔍 ROLES MEZCLADOS: {shuffled_roles}")
        
        # Asignar roles a jugadores
        player_ids = list(self.players.keys())
        print(f"🔍 JUGADORES ({len(player_ids)}): {[self.players[pid].name for pid in player_ids]}")
        
        werewolf_count_in_players = 0
        for i, player_id in enumerate(player_ids):
            role = shuffled_roles[i]
            self.players[player_id].assign_role(role)
            if role == 'werewolf':
                werewolf_count_in_players += 1
            print(f"🔍 JUGADOR {i}: {self.players[player_id].name} -> {role}")
            self.add_log(f"Rol asignado: {self.players[player_id].name} -> {role}")
        
        # Asignar roles al centro
        self.center_cards = shuffled_roles[len(player_ids):]
        werewolf_count_in_center = self.center_cards.count('werewolf')
        
        print(f"🔍 CENTRO: {self.center_cards}")
        print(f"🔍 LOBOS EN JUGADORES: {werewolf_count_in_players}")
        print(f"🔍 LOBOS EN CENTRO: {werewolf_count_in_center}")
        
        self.add_log(f"Cartas del centro: {', '.join(self.center_cards)}")
        self.add_log(f"🐺 Lobos entre jugadores: {werewolf_count_in_players}")
        
        # Preparar turnos nocturnos (ordenados por turn_order)
        self.night_turns = self._calculate_night_turns()
        self.current_turn_index = 0
        
        # Cambiar a fase nocturna
        self.phase = GamePhase.NIGHT_PHASE
        self.add_log("🌙 El juego ha comenzado. Es de noche...")
        
        return True
    
    def _calculate_night_turns(self) -> List[str]:
        """Calcula el orden de turnos nocturnos basado en los roles"""
        players_with_turns = []
        
        for player_id, player in self.players.items():
            if player.can_act_at_night():
                players_with_turns.append((player_id, player.get_turn_order()))
        
        # Ordenar por turn_order y retornar solo los player_ids
        players_with_turns.sort(key=lambda x: x[1])
        return [player_id for player_id, _ in players_with_turns]
    
    def get_current_turn_player(self) -> Optional[str]:
        """Retorna el player_id del jugador en el turno actual"""
        if (self.phase != GamePhase.NIGHT_PHASE or 
            self.current_turn_index >= len(self.night_turns)):
            return None
        
        return self.night_turns[self.current_turn_index]
    
    def get_current_turn_role(self) -> Optional[str]:
        """Retorna el rol que está actuando en el turno actual"""
        current_player = self.get_current_turn_player()
        if not current_player:
            return None
        
        return self.players[current_player].get_role_name()
    
    def get_night_action_data_for_player(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Retorna los datos de acción nocturna para un jugador específico"""
        if self.phase != GamePhase.NIGHT_PHASE:
            return None
        
        if player_id not in self.players:
            return None
        
        player = self.players[player_id]
        if not player.role:
            return None
        
        game_state = self._get_game_state()
        return player.role.get_night_action_data(player_id, game_state)
    
    def execute_night_action(self, player_id: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta una acción nocturna"""
        if self.phase != GamePhase.NIGHT_PHASE:
            return {'success': False, 'message': 'No es la fase nocturna'}
        
        if player_id not in self.players:
            return {'success': False, 'message': 'Jugador no encontrado'}
        
        current_turn_player = self.get_current_turn_player()
        if current_turn_player != player_id:
            return {'success': False, 'message': 'No es tu turno'}
        
        player = self.players[player_id]
        if not player.role:
            return {'success': False, 'message': 'No tienes rol asignado'}
        
        game_state = self._get_game_state()
        result = player.role.execute_action(player_id, action_data, game_state)
        
        if result.get('success'):
            self.add_log(f"🎯 {player.name} ejecutó su acción: {result.get('message', 'Acción realizada')}")
        
        return result
    
    def advance_night_turn(self) -> bool:
        """Avanza al siguiente turno nocturno"""
        if self.phase != GamePhase.NIGHT_PHASE:
            return False
        
        self.current_turn_index += 1
        
        # Si se terminaron todos los turnos nocturnos
        if self.current_turn_index >= len(self.night_turns):
            self.phase = GamePhase.DAY_PHASE
            self.add_log("☀️ Amanecer. Fase de discusión iniciada")
            return True
        
        # Siguiente turno
        current_player = self.get_current_turn_player()
        current_role = self.get_current_turn_role()
        if current_player and current_role:
            player_name = self.players[current_player].name
            self.add_log(f"--- Fase: {current_role} ---")
        
        return True
    
    def _get_game_state(self) -> Dict[str, Any]:
        """Retorna el estado actual del juego para las reglas de dominio"""
        return {
            'room_code': self.room_code,
            'phase': self.phase.value,
            'players': {pid: {'name': p.name, 'role': p.get_role_name()} 
                       for pid, p in self.players.items()},
            'center_cards': self.center_cards.copy(),
            'current_turn_index': self.current_turn_index,
            'current_turn_player': self.get_current_turn_player(),
            'current_turn_role': self.get_current_turn_role()
        }
    
    def add_log(self, message: str):
        """Añade un evento al log del juego"""
        import time
        timestamp = int(time.time())
        log_entry = {
            'timestamp': timestamp,
            'message': message,
            'phase': self.phase.value
        }
        self.game_logs.append(log_entry)
    
    def get_public_state(self) -> Dict[str, Any]:
        """Retorna el estado público del juego (sin información sensible)"""
        return {
            'room_code': self.room_code,
            'phase': self.phase.value,
            'players': [p.to_dict() for p in self.players.values()],
            'player_count': len(self.players),
            'selected_roles_count': len(self.selected_roles),
            'current_turn_role': self.get_current_turn_role(),
            'logs': self.game_logs[-10:]  # Últimos 10 logs
        }
    
    def get_private_state_for_player(self, player_id: str) -> Dict[str, Any]:
        """Retorna el estado privado para un jugador específico"""
        public_state = self.get_public_state()
        
        if player_id not in self.players:
            return public_state
        
        player = self.players[player_id]
        private_data = {
            'your_role': player.get_role_name() if player.role else None,
            'your_original_role': player.original_role,
            'is_your_turn': self.get_current_turn_player() == player_id
        }
        
        # Añadir datos de acción nocturna si es su turno
        if private_data['is_your_turn']:
            night_action_data = self.get_night_action_data_for_player(player_id)
            if night_action_data:
                private_data['night_action'] = night_action_data
        
        return {**public_state, **private_data}