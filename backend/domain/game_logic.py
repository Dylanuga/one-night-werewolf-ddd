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

ROLE_NAMES_ES = {
    'werewolf': 'Lobo',
    'villager': 'Aldeano',
    'seer': 'Vidente',
    'robber': 'Ladrón',
    'troublemaker': 'Alborotadora',
    'drunk': 'Borracho',
    'insomniac': 'Insomne',
    'hunter': 'Cazador',
    'mason': 'Masón',
    'tanner': 'Curtidor',
    'doppelganger': 'Doppelgänger',
    'minion': 'Esbirro',
    'open_eyes': 'Abrid los ojos todos'
}

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
        self.troublemaker_action_taken = False
        self.troublemaker_last_swap_by_player: Dict[str, Dict[str, Any]] = {}
        self.votes: Dict[str, Optional[str]] = {}
        self.final_roles: Dict[str, str] = {}
        self.eliminated_ids: List[str] = []
        self.winners: Dict[str, Any] = {}
        self.night_finished = False
        self.drunk_action_taken = False
        self.drunk_last_center_by_player: Dict[str, int] = {}
    
    def add_player(self, player_id: str, name: str, socket_id: str, is_host: bool = False) -> bool:
        """Añade un jugador a la sala"""
        if len(self.players) >= self.max_players:
            return False
        
        if self.phase != GamePhase.LOBBY and self.phase != GamePhase.ROLE_SELECTION:
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
        """Establece los roles seleccionados para la partida (draft/sincronización)"""
        if self.phase != GamePhase.LOBBY and self.phase != GamePhase.ROLE_SELECTION:
            return False
        
        # Sincronizar directamente los roles sin validación estricta de cantidad o presencia de lobo.
        # Esto permite al host configurar los roles dinámicamente y reflejarlo a los demás en tiempo real.
        # La validación estricta de cantidad y lobo se realiza en el start_game del GameService.
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
            if self.test_mode:
                self.add_log(f"Rol asignado: {self.players[player_id].name} -> {ROLE_NAMES_ES.get(role, role)}")
        
        # Asignar roles al centro
        self.center_cards = shuffled_roles[len(player_ids):]
        werewolf_count_in_center = self.center_cards.count('werewolf')
        
        print(f"🔍 CENTRO: {self.center_cards}")
        print(f"🔍 LOBOS EN JUGADORES: {werewolf_count_in_players}")
        print(f"🔍 LOBOS EN CENTRO: {werewolf_count_in_center}")
        
        if self.test_mode:
            translated_center = [ROLE_NAMES_ES.get(r, r) for r in self.center_cards]
            self.add_log(f"Cartas del centro: {', '.join(translated_center)}")
            self.add_log(f"🐺 Lobos entre jugadores: {werewolf_count_in_players}")
        
        # Preparar turnos nocturnos (ordenados por turn_order)
        self.night_turns = self._calculate_night_turns()
        self.current_turn_index = 0
        
        # Cambiar a fase nocturna
        self.phase = GamePhase.NIGHT_PHASE
        self.robber_action_taken = False
        self.robber_last_target_by_player = {}
        self.troublemaker_action_taken = False
        self.troublemaker_last_swap_by_player = {}
        self.votes = {}
        self.final_roles = {}
        self.eliminated_ids = []
        self.winners = {}
        self.night_finished = False
        self.drunk_action_taken = False
        self.drunk_last_center_by_player = {}
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
        if not player.original_role:
            return None
        
        game_state = self._get_game_state()
        # Se obtiene el rol original para calcular la acción que debe realizar
        original_role_class = RoleFactory.create_role(player.original_role)
        return original_role_class.get_night_action_data(player_id, game_state)
    
    def execute_night_action(self, player_id: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta una acción nocturna."""
        if self.phase != GamePhase.NIGHT_PHASE:
            return {'success': False, 'message': 'No es la fase nocturna'}
        if player_id not in self.players:
            return {'success': False, 'message': 'Jugador no encontrado'}

        player = self.players[player_id]
        current_role = self.get_current_turn_role()

        # 🔧 FIX: La validación ahora es por ROL ORIGINAL
        if player.original_role != current_role:
            return {'success': False, 'message': 'No es el turno de tu rol'}
        if not player.role:
            return {'success': False, 'message': 'No tienes rol asignado'}

        if current_role == 'robber':
            result = self._execute_robber_action(player_id, action_data)
        elif current_role == 'troublemaker':
            result = self._execute_troublemaker_action(player_id, action_data)
        elif current_role == 'drunk':
            result = self._execute_drunk_action(player_id, action_data)
        else:
            game_state = self._get_game_state()
            original_role_class = RoleFactory.create_role(player.original_role)
            result = original_role_class.execute_action(player_id, action_data, game_state)
        if result.get('success'):
            if self.test_mode:
                role_es = ROLE_NAMES_ES.get(player.original_role, player.original_role)
                self.add_log(f"🎯 {player.name} ({role_es}) ejecutó su acción.")
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
        new_role_es = ROLE_NAMES_ES.get(new_role, new_role)
        return {
            'success': True,
            'message': f'Has robado el rol de {target.name}. Tu nuevo rol es {new_role_es}.',
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
            if player.original_role == 'robber':
                robber_id = pid
                break

        if not robber_id:
            return {'success': False, 'message': 'No hay ladrón activo'}

        possible_targets = [pid for pid in self.players.keys() if pid != robber_id]
        if not possible_targets:
            return {'success': False, 'message': 'No hay objetivos válidos'}

        target_player_id = random.choice(possible_targets)
        return self._execute_robber_action(robber_id, {'target_player_id': target_player_id})

    def _execute_troublemaker_action(self, player_id: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta la acción de la alborotadora: intercambia roles de dos jugadores (no centro)."""
        if self.troublemaker_action_taken:
            return {'success': False, 'message': 'Acción de alborotadora ya ejecutada'}

        target_a = action_data.get('target_player_id_a')
        target_b = action_data.get('target_player_id_b')

        if not target_a or not target_b:
            return {'success': False, 'message': 'Debes elegir dos jugadores'}
        if target_a == target_b:
            return {'success': False, 'message': 'Debes elegir dos jugadores distintos'}
        if target_a not in self.players or target_b not in self.players:
            return {'success': False, 'message': 'Jugador no válido'}

        player_a = self.players[target_a]
        player_b = self.players[target_b]

        # Intercambiar roles actuales (sin revelar)
        player_a.role, player_b.role = player_b.role, player_a.role
        self.troublemaker_action_taken = True
        self.troublemaker_last_swap_by_player[player_id] = {
            'a': {'id': target_a, 'name': player_a.name},
            'b': {'id': target_b, 'name': player_b.name}
        }

        target_names = self.troublemaker_last_swap_by_player[player_id]
        return {
            'success': True,
            'message': f"Has cambiado a {target_names['a']['name']} con {target_names['b']['name']}.",
            'troublemaker_player_id': player_id,
            'swapped_players': self.troublemaker_last_swap_by_player[player_id]
        }

    def execute_troublemaker_auto_action(self) -> Dict[str, Any]:
        """Ejecuta acción automática de la alborotadora al expirar el turno."""
        if self.troublemaker_action_taken:
            return {'success': False, 'message': 'Acción de alborotadora ya ejecutada'}

        troublemaker_id = None
        for pid, player in self.players.items():
            if player.original_role == 'troublemaker':
                troublemaker_id = pid
                break

        if not troublemaker_id:
            return {'success': False, 'message': 'No hay alborotadora activa'}

        player_ids = list(self.players.keys())
        if len(player_ids) < 2:
            return {'success': False, 'message': 'No hay suficientes jugadores para intercambiar'}

        target_a, target_b = random.sample(player_ids, 2)
        return self._execute_troublemaker_action(troublemaker_id, {
            'target_player_id_a': target_a,
            'target_player_id_b': target_b
        })

    def _execute_drunk_action(self, player_id: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta la acción del borracho: intercambia su rol con una carta del centro sin verla."""
        if self.drunk_action_taken:
            return {'success': False, 'message': 'Acción de borracho ya ejecutada'}

        center_pos = action_data.get('center_position')
        if center_pos is None or not isinstance(center_pos, int) or not (0 <= center_pos <= 2):
            return {'success': False, 'message': 'Posición de centro inválida'}

        if center_pos >= len(self.center_cards):
            return {'success': False, 'message': 'Posición de centro inválida'}

        player = self.players[player_id]
        # Intercambiar rol actual con la carta del centro elegida
        center_role = self.center_cards[center_pos]
        self.center_cards[center_pos] = player.get_role_name()
        player.role = RoleFactory.create_role(center_role)

        self.drunk_action_taken = True
        self.drunk_last_center_by_player[player_id] = center_pos

        return {
            'success': True,
            'message': f'Has intercambiado tu carta con la del centro {center_pos + 1}.',
            'center_position': center_pos,
            'drunk_player_id': player_id
        }

    def execute_drunk_auto_action(self) -> Dict[str, Any]:
        """Ejecuta acción automática del borracho al expirar el turno."""
        if self.drunk_action_taken:
            return {'success': False, 'message': 'Acción de borracho ya ejecutada'}

        drunk_id = None
        for pid, player in self.players.items():
            if player.original_role == 'drunk':
                drunk_id = pid
                break

        if not drunk_id:
            return {'success': False, 'message': 'No hay borracho activo'}

        # Elegir una posición del centro aleatoria
        center_pos = random.randint(0, len(self.center_cards) - 1)
        return self._execute_drunk_action(drunk_id, {'center_position': center_pos})

    def advance_night_turn(self) -> bool:
        """Avanza al siguiente turno nocturno."""
        if self.phase != GamePhase.NIGHT_PHASE:
            return False
        
        self.current_turn_index += 1
        
        if self.current_turn_index >= len(self.night_turns):
            self.night_finished = True
            return True
        
        current_role = self.get_current_turn_role()
        if current_role:
            self.add_log(f"--- Fase: {ROLE_NAMES_ES.get(current_role, current_role)} ---")
            if current_role == 'robber':
                self.robber_action_taken = False
            if current_role == 'troublemaker':
                self.troublemaker_action_taken = False
            if current_role == 'drunk':
                self.drunk_action_taken = False
        return True

    def start_voting_phase(self) -> bool:
        """Inicia la fase de votación (solo desde día)."""
        if self.phase != GamePhase.DAY_PHASE:
            return False
        self.phase = GamePhase.VOTING
        self.votes = {pid: None for pid in self.players.keys()}
        self.add_log("🗳️ Votación iniciada")
        return True

    def submit_vote(self, voter_id: str, target_id: str) -> Dict[str, Any]:
        """Registra el voto de un jugador."""
        if self.phase != GamePhase.VOTING:
            return {'success': False, 'message': 'No es la fase de votación'}
        if voter_id not in self.players:
            return {'success': False, 'message': 'Jugador no encontrado'}
        if target_id not in self.players:
            return {'success': False, 'message': 'Objetivo inválido'}

        self.votes[voter_id] = target_id
        all_voted = all(v is not None for v in self.votes.values())

        return {
            'success': True,
            'all_voted': all_voted
        }

    def can_finalize(self) -> bool:
        """Indica si todos han votado y se puede revelar."""
        if self.phase != GamePhase.VOTING:
            return False
        return bool(self.votes) and all(v is not None for v in self.votes.values())

    def _finalize_game(self):
        """Calcula resultados finales y define ganadores."""
        # Snapshot de roles finales
        self.final_roles = {pid: p.get_role_name() for pid, p in self.players.items()}

        # Conteo de votos
        vote_counts: Dict[str, int] = {}
        for target_id in self.votes.values():
            if target_id is None:
                continue
            vote_counts[target_id] = vote_counts.get(target_id, 0) + 1

        self.eliminated_ids = []
        if vote_counts:
            max_votes = max(vote_counts.values())
            self.eliminated_ids = [pid for pid, count in vote_counts.items() if count == max_votes]

        # Ganadores (borrador simple)
        werewolves_in_final = [pid for pid, role in self.final_roles.items() if role == 'werewolf']
        eliminated_werewolves = [pid for pid in self.eliminated_ids if self.final_roles.get(pid) == 'werewolf']

        eliminated_tanner = [pid for pid in self.eliminated_ids if self.final_roles.get(pid) == 'tanner']

        if eliminated_tanner:
            team = 'tanner'
            message = 'Gana el Curtidor (consiguió ser linchado).'
            winning_player_ids = eliminated_tanner
        elif eliminated_werewolves:
            team = 'villagers'
            message = 'Los aldeanos ganan (eliminaron a un hombre lobo).'
            winning_player_ids = [pid for pid, r in self.final_roles.items() if r not in ('werewolf', 'tanner')]
        else:
            if len(werewolves_in_final) == 0:
                team = 'villagers'
                message = 'Los aldeanos ganan (no había lobos en el pueblo).'
                winning_player_ids = [pid for pid, r in self.final_roles.items() if r not in ('werewolf', 'tanner')]
            else:
                team = 'werewolves'
                message = 'Los lobos ganan (ningún lobo fue eliminado).'
                winning_player_ids = werewolves_in_final

        self.winners = {
            'team': team,
            'message': message,
            'eliminated_ids': self.eliminated_ids,
            'winning_player_ids': winning_player_ids
        }

        self.phase = GamePhase.GAME_END
        self.add_log("🏁 Fin de partida")

    def reset_game(self, to_phase: str) -> bool:
        """Reinicia la partida a LOBBY o ROLE_SELECTION"""
        if self.phase != GamePhase.GAME_END:
            return False
        
        # Limpiar roles de los jugadores
        for player in self.players.values():
            player.role = None
            player.original_role = None
            
        # Limpiar variables de la partida
        self.center_cards = []
        self.current_turn_index = 0
        self.night_turns = []
        self.robber_action_taken = False
        self.robber_last_target_by_player = {}
        self.troublemaker_action_taken = False
        self.troublemaker_last_swap_by_player = {}
        self.drunk_action_taken = False
        self.drunk_last_center_by_player = {}
        self.votes = {}
        self.final_roles = {}
        self.eliminated_ids = []
        self.winners = {}
        self.night_finished = False
        
        if to_phase == "lobby":
            self.phase = GamePhase.LOBBY
            self.selected_roles = []
            self.add_log("El host ha reiniciado el juego al Lobby")
        elif to_phase == "role_selection":
            self.phase = GamePhase.ROLE_SELECTION
            self.add_log("El host ha reiniciado el juego a la Selección de Roles")
        else:
            return False
            
        return True

    def get_reveal_data(self) -> Dict[str, Any]:
        """Retorna los datos de revelación final."""
        return {
            'final_roles': {pid: {'role': self.final_roles.get(pid), 'name': p.name} for pid, p in self.players.items()},
            'original_roles': {pid: {'role': p.original_role, 'name': p.name} for pid, p in self.players.items()},
            'eliminated_ids': self.eliminated_ids,
            'votes': self.votes,
            'winners': self.winners
        }

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
            'votes': self.votes if self.phase == GamePhase.VOTING else {},
            'logs': self.game_logs[-10:]
        }

    def get_private_state_for_player(self, player_id: str) -> Dict[str, Any]:
        """Retorna el estado privado para un jugador específico."""
        public_state = self.get_public_state()
        if player_id not in self.players:
            return public_state

        player = self.players[player_id]
        current_turn_role = self.get_current_turn_role()
        
        # 🔧 FIX: La validación de turno es por ROL ORIGINAL
        is_your_turn = player.original_role == current_turn_role
        
        your_role = player.get_role_name() if player.role else None
        if self.phase in (GamePhase.NIGHT_PHASE, GamePhase.DAY_PHASE, GamePhase.VOTING) and player.original_role:
            if self.phase == GamePhase.NIGHT_PHASE and player.original_role == 'robber':
                # El ladrón ve su rol actual durante la noche
                your_role = player.get_role_name()
            else:
                your_role = player.original_role

        private_data = {
            'your_role': your_role,
            'your_original_role': player.original_role,
            'is_your_turn': is_your_turn
        }

        if self.phase == GamePhase.NIGHT_PHASE and player.original_role == 'robber':
            robber_last_target = self.robber_last_target_by_player.get(player_id)
            if robber_last_target:
                private_data['robber_last_target'] = robber_last_target
        if self.phase == GamePhase.NIGHT_PHASE and player.original_role == 'troublemaker':
            troublemaker_last_swap = self.troublemaker_last_swap_by_player.get(player_id)
            if troublemaker_last_swap:
                private_data['troublemaker_last_swap'] = troublemaker_last_swap
        if self.phase == GamePhase.NIGHT_PHASE and player.original_role == 'drunk':
            drunk_center = self.drunk_last_center_by_player.get(player_id)
            if drunk_center is not None:
                private_data['drunk_last_center'] = drunk_center
        
        if is_your_turn:
            night_action_data = self.get_night_action_data_for_player(player_id)
            if night_action_data:
                private_data['night_action'] = night_action_data
        
        return {**public_state, **private_data}
