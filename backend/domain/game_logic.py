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
        self.robber_action_taken = False
        self.robber_last_target_by_player: Dict[str, Dict[str, Any]] = {}
    
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
        self.robber_action_taken = False
        self.robber_last_target_by_player = {}
        self.add_log("🌙 El juego ha comenzado. Es de noche...")
        
        return True
    
    def _calculate_night_turns(self) -> List[str]:
        """Calcula el orden de turnos nocturnos basado en roles únicos con acciones."""
        roles_in_play = {p.get_role_name() for p in self.players.values()} \
                        .union(set(self.center_cards))

        roles_with_turns = {}
        for role_name in roles_in_play:
            role_instance = RoleFactory.create_role(role_name)
            if role_instance and role_instance.can_act_at_night():
                roles_with_turns[role_name] = role_instance.get_turn_order()

        # Ordenar los roles por su número de turno
        sorted_roles = sorted(roles_with_turns.items(), key=lambda item: item[1])
        
        night_turns = [role for role, order in sorted_roles]
        print(f"🔧 TURNOS NOCTURNOS CALCULADOS (POR ROL): {night_turns}")
        return night_turns
    
    def get_current_turn_role(self) -> Optional[str]:
        """Retorna el rol que está actuando en el turno actual."""
        if self.phase != GamePhase.NIGHT_PHASE or self.current_turn_index >= len(self.night_turns):
            return None
        return self.night_turns[self.current_turn_index]
    
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
        """Ejecuta una acción nocturna."""
        if self.phase != GamePhase.NIGHT_PHASE:
            return {'success': False, 'message': 'No es la fase nocturna'}
        if player_id not in self.players:
            return {'success': False, 'message': 'Jugador no encontrado'}

        player = self.players[player_id]
        current_role = self.get_current_turn_role()

        # 🔧 FIX: La validación ahora es por ROL
        if player.get_role_name() != current_role:
            return {'success': False, 'message': 'No es el turno de tu rol'}
        if not player.role:
            return {'success': False, 'message': 'No tienes rol asignado'}

        if current_role == 'robber':
            result = self._execute_robber_action(player_id, action_data)
        else:
            game_state = self._get_game_state()
            result = player.role.execute_action(player_id, action_data, game_state)
        if result.get('success'):
            self.add_log(f"🎯 {player.name} ({player.get_role_name()}) ejecutó su acción.")
        return result

    def _execute_robber_action(self, player_id: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta la acción del ladrón: roba el rol de otro jugador (no centro)."""
        if self.robber_action_taken:
            return {'success': False, 'message': 'Acción de ladrón ya ejecutada'}

        target_player_id = action_data.get('target_player_id')
        if not target_player_id:
            return {'success': False, 'message': 'Debes elegir un jugador'}
        if target_player_id == player_id:
            return {'success': False, 'message': 'No puedes robarte a ti mismo'}
        if target_player_id not in self.players:
            return {'success': False, 'message': 'Jugador no válido'}

        robber = self.players[player_id]
        target = self.players[target_player_id]

        # Intercambiar roles actuales
        robber.role, target.role = target.role, robber.role
        self.robber_action_taken = True
        self.robber_last_target_by_player[player_id] = {
            'id': target_player_id,
            'name': target.name
        }

        new_role = robber.get_role_name()
        return {
            'success': True,
            'message': f'Has robado el rol de {target.name}. Tu nuevo rol es {new_role}.',
            'robbed_player': {'id': target_player_id, 'name': target.name},
            'new_role': new_role,
            'robber_player_id': player_id
        }

    def execute_robber_auto_action(self) -> Dict[str, Any]:
        """Ejecuta acción automática del ladrón al expirar el turno."""
        if self.robber_action_taken:
            return {'success': False, 'message': 'Acción de ladrón ya ejecutada'}

        robber_id = None
        for pid, player in self.players.items():
            if player.get_role_name() == 'robber':
                robber_id = pid
                break

        if not robber_id:
            return {'success': False, 'message': 'No hay ladrón activo'}

        possible_targets = [pid for pid in self.players.keys() if pid != robber_id]
        if not possible_targets:
            return {'success': False, 'message': 'No hay objetivos válidos'}

        target_player_id = random.choice(possible_targets)
        return self._execute_robber_action(robber_id, {'target_player_id': target_player_id})

    def advance_night_turn(self) -> bool:
        """Avanza al siguiente turno nocturno."""
        if self.phase != GamePhase.NIGHT_PHASE:
            return False
        
        self.current_turn_index += 1
        
        if self.current_turn_index >= len(self.night_turns):
            self.phase = GamePhase.DAY_PHASE
            self.add_log("☀️ Amanecer. Fase de discusión iniciada")
            return True
        
        current_role = self.get_current_turn_role()
        if current_role:
            self.add_log(f"--- Fase: {current_role} ---")
            if current_role == 'robber':
                self.robber_action_taken = False
        return True

    def _get_game_state(self) -> Dict[str, Any]:
        """Retorna el estado actual del juego para las reglas de dominio."""
        return {
            'room_code': self.room_code,
            'phase': self.phase.value,
            'players': {pid: {'name': p.name, 'role': p.get_role_name()} 
                       for pid, p in self.players.items()},
            'center_cards': self.center_cards.copy(),
            'current_turn_index': self.current_turn_index,
            'current_turn_role': self.get_current_turn_role()
        }

    def add_log(self, message: str):
        """Añade un evento al log del juego."""
        import time
        timestamp = int(time.time())
        log_entry = {'timestamp': timestamp, 'message': message, 'phase': self.phase.value}
        self.game_logs.append(log_entry)

    def get_public_state(self) -> Dict[str, Any]:
        """Retorna el estado público del juego (sin información sensible)."""
        return {
            'room_code': self.room_code,
            'phase': self.phase.value,
            'players': [p.to_dict() for p in self.players.values()],
            'player_count': len(self.players),
            'selected_roles_count': len(self.selected_roles),
            'current_turn_role': self.get_current_turn_role(),
            'logs': self.game_logs[-10:]
        }

    def get_private_state_for_player(self, player_id: str) -> Dict[str, Any]:
        """Retorna el estado privado para un jugador específico."""
        public_state = self.get_public_state()
        if player_id not in self.players:
            return public_state

        player = self.players[player_id]
        current_turn_role = self.get_current_turn_role()
        
        # 🔧 FIX: La validación de turno es por ROL
        is_your_turn = player.get_role_name() == current_turn_role
        
        your_role = player.get_role_name() if player.role else None
        if self.phase == GamePhase.NIGHT_PHASE and player.original_role:
            if player.original_role != 'robber':
                your_role = player.original_role
            else:
                # El ladrón ve su rol actual durante la noche
                your_role = player.get_role_name()

        private_data = {
            'your_role': your_role,
            'your_original_role': player.original_role,
            'is_your_turn': is_your_turn
        }

        if self.phase == GamePhase.NIGHT_PHASE and player.original_role == 'robber':
            robber_last_target = self.robber_last_target_by_player.get(player_id)
            if robber_last_target:
                private_data['robber_last_target'] = robber_last_target
        
        if is_your_turn:
            night_action_data = self.get_night_action_data_for_player(player_id)
            if night_action_data:
                private_data['night_action'] = night_action_data
        
        return {**public_state, **private_data}
