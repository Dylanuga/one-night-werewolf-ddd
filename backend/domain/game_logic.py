# GameLogic: reglas del juego, turnos polimórficos y resolución de partida

import random
import time
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from .player import Player
from .roles import RoleFactory, ROLE_METADATA, ROLE_NAMES_ES as CATALOG_ROLE_NAMES_ES


class GamePhase(Enum):
    LOBBY = "lobby"
    ROLE_SELECTION = "role_selection"
    NIGHT_PHASE = "night_phase"
    DAY_PHASE = "day_phase"
    VOTING = "voting"
    GAME_END = "game_end"


ROLE_NAMES_ES: Dict[str, str] = {
    **CATALOG_ROLE_NAMES_ES,
    "doppelganger": "Doppelgänger",
    "minion": "Esbirro",
    "open_eyes": "Abrid los ojos todos"
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
        self.night_turns: List[str] = []
        self.game_logs: List[Dict[str, Any]] = []
        self.max_players = 8
        self.test_mode = False
        self.test_role_distribution = None

        # Estado nocturno unificado (polimórfico) + alias de compatibilidad
        self.roles_acted: Set[str] = set()
        self.night_actions_by_player: Dict[str, Dict[str, Any]] = {}

        self.werewolf_action_taken = False
        self.werewolf_last_center_by_player: Dict[str, Dict[str, Any]] = {}
        self.seer_action_taken = False
        self.seer_last_result_by_player: Dict[str, Dict[str, Any]] = {}
        self.robber_action_taken = False
        self.robber_last_target_by_player: Dict[str, Dict[str, Any]] = {}
        self.troublemaker_action_taken = False
        self.troublemaker_last_swap_by_player: Dict[str, Dict[str, Any]] = {}
        self.drunk_action_taken = False
        self.drunk_last_center_by_player: Dict[str, int] = {}

        # Estado de votación y resolución
        self.votes: Dict[str, Optional[str]] = {}
        self.final_roles: Dict[str, str] = {}
        self.eliminated_ids: List[str] = []
        self.chain_eliminated_ids: List[str] = []
        self.winners: Dict[str, Any] = {}
        self.night_finished = False
        self.open_eyes_active = False

        # Temporizadores configurables
        self.turn_duration: int = 12
        self.turn_start_timestamp: Optional[float] = None
        self.turn_end_timestamp: Optional[float] = None
        self.discussion_duration: int = 300  # 5 minutos por defecto (120, 300, 600 segundos)
        self.discussion_end_timestamp: Optional[float] = None
        self.voting_duration: int = 60  # 60 segundos para votación
        self.voting_end_timestamp: Optional[float] = None

    def _reset_night_tracking(self):
        """Limpia el estado de acciones nocturnas entre partidas"""
        self.roles_acted.clear()
        self.night_actions_by_player.clear()
        self.werewolf_action_taken = False
        self.werewolf_last_center_by_player = {}
        self.seer_action_taken = False
        self.seer_last_result_by_player = {}
        self.robber_action_taken = False
        self.robber_last_target_by_player = {}
        self.troublemaker_action_taken = False
        self.troublemaker_last_swap_by_player = {}
        self.drunk_action_taken = False
        self.drunk_last_center_by_player = {}

    def mark_role_acted(self, role_name: str, acted: bool = True):
        """Marca o desmarca que un rol ya ejecutó su acción nocturna y sincroniza flags legacy"""
        if acted:
            self.roles_acted.add(role_name)
        else:
            self.roles_acted.discard(role_name)

        flag_attr = f"{role_name}_action_taken"
        if hasattr(self, flag_attr):
            setattr(self, flag_attr, acted)

    def record_player_night_action(self, player_id: str, action_record: Dict[str, Any]):
        """Guarda el resultado estandarizado de la acción nocturna de un jugador"""
        self.night_actions_by_player[player_id] = action_record

    def add_player(self, player_id: str, name: str, socket_id: str, is_host: bool = False) -> bool:
        """Añade un jugador a la sala o reconecta uno existente"""
        if player_id in self.players:
            self.players[player_id].reconnect(socket_id)
            self.add_log(f"{name} se ha reconectado a la partida")
            return True

        if len(self.players) >= self.max_players:
            return False

        if self.phase != GamePhase.LOBBY and self.phase != GamePhase.ROLE_SELECTION:
            return False

        self.players[player_id] = Player(player_id, name, socket_id, is_host)
        self.add_log(f"{name} se unió a la sala")
        return True

    def remove_player(self, player_id: str) -> bool:
        """Remueve un jugador de la sala"""
        if player_id not in self.players:
            return False

        player = self.players[player_id]
        self.add_log(f"{player.name} salió de la sala")

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

        self.selected_roles = roles.copy()
        self.phase = GamePhase.ROLE_SELECTION
        return True

    def enable_test_mode(self, role_distribution: Dict[str, List[str]] = None):
        """Activa el modo de prueba y opcionalmente establece una distribución específica de roles."""
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

        print(f"🔍 ROLES ORIGINALES: {self.selected_roles}")

        if self.test_mode and self.test_role_distribution:
            shuffled_roles = (
                self.test_role_distribution["players"] +
                self.test_role_distribution["center"]
            )
        else:
            shuffled_roles = self.selected_roles.copy()
            random.shuffle(shuffled_roles)

        print(f"🔍 ROLES MEZCLADOS: {shuffled_roles}")

        player_ids = list(self.players.keys())
        print(f"🔍 JUGADORES ({len(player_ids)}): {[self.players[pid].name for pid in player_ids]}")

        werewolf_count_in_players = 0
        for i, player_id in enumerate(player_ids):
            role = shuffled_roles[i]
            self.players[player_id].assign_role(role)
            if role == "werewolf":
                werewolf_count_in_players += 1
            print(f"🔍 JUGADOR {i}: {self.players[player_id].name} -> {role}")
            if self.test_mode:
                self.add_log(f"Rol asignado: {self.players[player_id].name} -> {ROLE_NAMES_ES.get(role, role)}")

        self.center_cards = shuffled_roles[len(player_ids):]
        werewolf_count_in_center = self.center_cards.count("werewolf")

        print(f"🔍 CENTRO: {self.center_cards}")
        print(f"🔍 LOBOS EN JUGADORES: {werewolf_count_in_players}")
        print(f"🔍 LOBOS EN CENTRO: {werewolf_count_in_center}")

        if self.test_mode:
            translated_center = [ROLE_NAMES_ES.get(r, r) for r in self.center_cards]
            self.add_log(f"Cartas del centro: {', '.join(translated_center)}")
            self.add_log(f"🐺 Lobos entre jugadores: {werewolf_count_in_players}")

        self.night_turns = self._calculate_night_turns()
        self.current_turn_index = 0

        self.phase = GamePhase.NIGHT_PHASE
        self._reset_night_tracking()
        self.votes = {}
        self.final_roles = {}
        self.eliminated_ids = []
        self.chain_eliminated_ids = []
        self.winners = {}
        self.night_finished = False
        self.open_eyes_active = False
        self.turn_start_timestamp = None
        self.turn_end_timestamp = None
        self.add_log("🌙 El juego ha comenzado. Es de noche...")

        return True

    def _calculate_night_turns(self) -> List[str]:
        """Calcula el orden de turnos nocturnos basado en roles únicos con acciones."""
        roles_in_play = {p.get_role_name() for p in self.players.values()}.union(set(self.center_cards))

        roles_with_turns = {}
        for role_name in roles_in_play:
            role_instance = RoleFactory.create_role(role_name)
            if role_instance and role_instance.can_act_at_night():
                roles_with_turns[role_name] = role_instance.get_turn_order()

        sorted_roles = sorted(roles_with_turns.items(), key=lambda item: item[1])
        night_turns = [role for role, _ in sorted_roles]
        print(f"🔧 TURNOS NOCTURNOS CALCULADOS (POR ROL): {night_turns}")
        return night_turns

    def get_current_turn_role(self) -> Optional[str]:
        """Retorna el rol que está actuando en el turno actual."""
        if self.phase != GamePhase.NIGHT_PHASE or self.current_turn_index >= len(self.night_turns):
            return None
        return self.night_turns[self.current_turn_index]

    def get_night_action_data_for_player(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Retorna los datos de acción nocturna para un jugador específico (y registra info pasiva)"""
        if self.phase != GamePhase.NIGHT_PHASE or player_id not in self.players:
            return None

        player = self.players[player_id]
        if not player.original_role:
            return None

        game_state = self._get_game_state()
        original_role_class = RoleFactory.create_role(player.original_role)
        data = original_role_class.get_night_action_data(player_id, game_state)

        # Si es información pasiva (ej. 2 lobos, masones, insomne) y es su turno, guardar en el resumen nocturno
        if data and data.get("interaction_type") == "passive_info" and self.get_current_turn_role() == player.original_role:
            self.record_player_night_action(player_id, {
                "role": player.original_role,
                "interaction_type": "passive_info",
                "message": data.get("message", ""),
                "summary_text": data.get("summary_text", data.get("message", "")),
                "revealed_cards": data.get("revealed_cards", []),
                "auto": False
            })

        return data

    def execute_night_action(self, player_id: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta una acción nocturna delegando polimórficamente en la clase de rol."""
        if self.phase != GamePhase.NIGHT_PHASE:
            return {"success": False, "message": "No es la fase nocturna"}
        if player_id not in self.players:
            return {"success": False, "message": "Jugador no encontrado"}

        player = self.players[player_id]
        current_role = self.get_current_turn_role()

        if player.original_role != current_role:
            return {"success": False, "message": "No es el turno de tu rol"}
        if not player.role:
            return {"success": False, "message": "No tienes rol asignado"}

        role_instance = RoleFactory.create_role(current_role)
        result = role_instance.execute_night_action_on_game(self, player_id, action_data, is_auto=False)

        if result.get("success") and self.test_mode:
            role_es = ROLE_NAMES_ES.get(player.original_role, player.original_role)
            self.add_log(f"🎯 {player.name} ({role_es}) ejecutó su acción.")
        return result

    def execute_current_turn_auto_action(self) -> Dict[str, Any]:
        """Ejecuta polimórficamente la acción automática aleatoria del rol cuyo turno expira."""
        current_role = self.get_current_turn_role()
        if not current_role:
            return {"success": False, "message": "No hay turno activo"}

        role_instance = RoleFactory.create_role(current_role)
        return role_instance.execute_auto_action_on_game(self)

    # Métodos delegados por compatibilidad con llamadas directas y tests existentes
    def _execute_werewolf_action(self, player_id: str, action_data: Dict[str, Any], is_auto: bool = False) -> Dict[str, Any]:
        return RoleFactory.create_role("werewolf").execute_night_action_on_game(self, player_id, action_data, is_auto=is_auto)

    def execute_werewolf_auto_action(self) -> Dict[str, Any]:
        return RoleFactory.create_role("werewolf").execute_auto_action_on_game(self)

    def _execute_seer_action(self, player_id: str, action_data: Dict[str, Any], is_auto: bool = False) -> Dict[str, Any]:
        return RoleFactory.create_role("seer").execute_night_action_on_game(self, player_id, action_data, is_auto=is_auto)

    def execute_seer_auto_action(self) -> Dict[str, Any]:
        return RoleFactory.create_role("seer").execute_auto_action_on_game(self)

    def _execute_robber_action(self, player_id: str, action_data: Dict[str, Any], is_auto: bool = False) -> Dict[str, Any]:
        return RoleFactory.create_role("robber").execute_night_action_on_game(self, player_id, action_data, is_auto=is_auto)

    def execute_robber_auto_action(self) -> Dict[str, Any]:
        return RoleFactory.create_role("robber").execute_auto_action_on_game(self)

    def _execute_troublemaker_action(self, player_id: str, action_data: Dict[str, Any], is_auto: bool = False) -> Dict[str, Any]:
        return RoleFactory.create_role("troublemaker").execute_night_action_on_game(self, player_id, action_data, is_auto=is_auto)

    def execute_troublemaker_auto_action(self) -> Dict[str, Any]:
        return RoleFactory.create_role("troublemaker").execute_auto_action_on_game(self)

    def _execute_drunk_action(self, player_id: str, action_data: Dict[str, Any], is_auto: bool = False) -> Dict[str, Any]:
        return RoleFactory.create_role("drunk").execute_night_action_on_game(self, player_id, action_data, is_auto=is_auto)

    def execute_drunk_auto_action(self) -> Dict[str, Any]:
        return RoleFactory.create_role("drunk").execute_auto_action_on_game(self)

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
            self.mark_role_acted(current_role, False)
        return True

    def set_discussion_duration(self, duration: int) -> bool:
        """Establece la duración del debate en segundos (120, 300, 600)"""
        if duration in (120, 300, 600):
            self.discussion_duration = duration
            return True
        return False

    def start_voting_phase(self) -> bool:
        """Inicia la fase de votación (solo desde día)."""
        if self.phase != GamePhase.DAY_PHASE:
            return False
        self.phase = GamePhase.VOTING
        self.votes = {pid: None for pid in self.players.keys()}
        self.voting_end_timestamp = time.time() + self.voting_duration
        self.add_log("🗳️ Votación iniciada")
        return True

    def submit_vote(self, voter_id: str, target_id: str) -> Dict[str, Any]:
        """Registra el voto de un jugador."""
        if self.phase != GamePhase.VOTING:
            return {"success": False, "message": "No es la fase de votación"}
        if voter_id not in self.players:
            return {"success": False, "message": "Jugador no encontrado"}
        if target_id not in self.players:
            return {"success": False, "message": "Objetivo inválido"}

        self.votes[voter_id] = target_id
        all_voted = all(v is not None for v in self.votes.values())

        connected_pids = [pid for pid, p in self.players.items() if p.is_connected]
        all_connected_voted = bool(connected_pids) and all(self.votes.get(pid) is not None for pid in connected_pids)

        return {
            "success": True,
            "all_voted": all_voted,
            "all_connected_voted": all_connected_voted
        }

    def can_finalize(self, allow_partial: bool = False) -> bool:
        """Indica si todos han votado o se permite revelar."""
        if self.phase != GamePhase.VOTING:
            return False
        if allow_partial:
            return any(v is not None for v in self.votes.values()) if self.votes else True

        connected_pids = [pid for pid, p in self.players.items() if p.is_connected]
        if connected_pids and all(self.votes.get(pid) is not None for pid in connected_pids):
            return True

        return bool(self.votes) and all(v is not None for v in self.votes.values())

    def _finalize_game(self):
        """
        Motor de resolución de partida en 3 fases:
        1. Recuento de votos y linchamientos iniciales.
        2. Resolución de efectos al morir (ej. disparo del Cazador en cadena).
        3. Evaluación de condiciones de victoria por prioridad de bandos.
        """
        # Snapshot de roles finales
        self.final_roles = {pid: p.get_role_name() for pid, p in self.players.items()}

        # Fase 1: Recuento de votos
        vote_counts: Dict[str, int] = {}
        for target_id in self.votes.values():
            if target_id is None:
                continue
            vote_counts[target_id] = vote_counts.get(target_id, 0) + 1

        initial_eliminated: List[str] = []
        if vote_counts:
            max_votes = max(vote_counts.values())
            initial_eliminated = [pid for pid, count in vote_counts.items() if count == max_votes]

        # Fase 2: Efectos encadenados al morir (p. ej. Cazador / Hunter)
        eliminated_set: List[str] = list(initial_eliminated)
        chain_eliminated: List[str] = []
        queue: List[str] = list(initial_eliminated)

        while queue:
            dead_pid = queue.pop(0)
            dead_role_name = self.final_roles.get(dead_pid)
            if not dead_role_name:
                continue
            try:
                role_obj = RoleFactory.create_role(dead_role_name)
                extra_targets = role_obj.on_death_trigger(self, dead_pid, self.votes)
                for extra_pid in extra_targets:
                    if extra_pid not in eliminated_set:
                        eliminated_set.append(extra_pid)
                        chain_eliminated.append(extra_pid)
                        queue.append(extra_pid)
                        dead_name = self.players[dead_pid].name if dead_pid in self.players else dead_pid
                        extra_name = self.players[extra_pid].name if extra_pid in self.players else extra_pid
                        self.add_log(f"🏹 {dead_name} (Cazador) cayó y disparó a {extra_name}.")
            except ValueError:
                continue

        self.eliminated_ids = eliminated_set
        self.chain_eliminated_ids = chain_eliminated

        # Fase 3: Evaluación de victoria por equipos
        werewolves_in_final = [pid for pid, role in self.final_roles.items() if role == "werewolf"]
        eliminated_werewolves = [pid for pid in self.eliminated_ids if self.final_roles.get(pid) == "werewolf"]
        eliminated_tanners = [pid for pid in self.eliminated_ids if self.final_roles.get(pid) == "tanner"]
        villager_team_pids = [pid for pid, r in self.final_roles.items() if r not in ("werewolf", "tanner")]

        if eliminated_tanners and eliminated_werewolves:
            team = "tanner"
            message = "Ganan el Curtidor y los Aldeanos (murieron el Curtidor y un Hombre Lobo)."
            winning_player_ids = eliminated_tanners + villager_team_pids
        elif eliminated_tanners:
            team = "tanner"
            message = "Gana el Curtidor (consiguió ser linchado)."
            winning_player_ids = eliminated_tanners
        elif eliminated_werewolves:
            team = "villagers"
            message = "Los aldeanos ganan (eliminaron a un hombre lobo)."
            winning_player_ids = villager_team_pids
        else:
            if len(werewolves_in_final) == 0:
                team = "villagers"
                message = "Los aldeanos ganan (no había lobos en el pueblo)."
                winning_player_ids = villager_team_pids
            else:
                team = "werewolves"
                message = "Los lobos ganan (ningún lobo fue eliminado)."
                winning_player_ids = werewolves_in_final

        self.winners = {
            "team": team,
            "message": message,
            "eliminated_ids": self.eliminated_ids,
            "chain_eliminated_ids": self.chain_eliminated_ids,
            "winning_player_ids": winning_player_ids
        }

        self.phase = GamePhase.GAME_END
        self.add_log("🏁 Fin de partida")

    def reset_game(self, to_phase: str) -> bool:
        """Reinicia la partida a LOBBY o ROLE_SELECTION"""
        if self.phase not in (GamePhase.GAME_END, GamePhase.ROLE_SELECTION, GamePhase.LOBBY):
            return False

        for player in self.players.values():
            player.role = None
            player.original_role = None

        self.center_cards = []
        self.current_turn_index = 0
        self.night_turns = []
        self._reset_night_tracking()
        self.votes = {}
        self.final_roles = {}
        self.eliminated_ids = []
        self.chain_eliminated_ids = []
        self.winners = {}
        self.night_finished = False
        self.open_eyes_active = False
        self.turn_start_timestamp = None
        self.turn_end_timestamp = None

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
            "final_roles": {pid: {"role": self.final_roles.get(pid), "name": p.name} for pid, p in self.players.items()},
            "original_roles": {pid: {"role": p.original_role, "name": p.name} for pid, p in self.players.items()},
            "eliminated_ids": self.eliminated_ids,
            "chain_eliminated_ids": self.chain_eliminated_ids,
            "votes": self.votes,
            "winners": self.winners
        }

    def _get_game_state(self) -> Dict[str, Any]:
        """Retorna el estado actual del juego para las reglas de dominio."""
        return {
            "room_code": self.room_code,
            "phase": self.phase.value,
            "players": {
                pid: {
                    "name": p.name,
                    "role": p.get_role_name(),
                    "original_role": p.original_role
                }
                for pid, p in self.players.items()
            },
            "center_cards": self.center_cards.copy(),
            "current_turn_index": self.current_turn_index,
            "current_turn_role": self.get_current_turn_role()
        }

    def add_log(self, message: str):
        """Añade un evento al log del juego."""
        timestamp = int(time.time())
        log_entry = {"timestamp": timestamp, "message": message, "phase": self.phase.value}
        self.game_logs.append(log_entry)

    def get_public_state(self) -> Dict[str, Any]:
        """Retorna el estado público del juego (sin información sensible)."""
        now = time.time()
        effective_turn_role = "open_eyes" if (self.phase == GamePhase.NIGHT_PHASE and self.open_eyes_active) else self.get_current_turn_role()
        turn_remaining = None
        if self.phase == GamePhase.NIGHT_PHASE and self.turn_end_timestamp is not None:
            turn_remaining = max(0.0, self.turn_end_timestamp - now)
        discussion_remaining = None
        if self.phase == GamePhase.DAY_PHASE and self.discussion_end_timestamp is not None:
            discussion_remaining = max(0.0, self.discussion_end_timestamp - now)
        voting_remaining = None
        if self.phase == GamePhase.VOTING and self.voting_end_timestamp is not None:
            voting_remaining = max(0.0, self.voting_end_timestamp - now)

        return {
            "room_code": self.room_code,
            "phase": self.phase.value,
            "players": [p.to_dict() for p in self.players.values()],
            "player_count": len(self.players),
            "selected_roles_count": len(self.selected_roles),
            "current_turn_role": effective_turn_role,
            "votes": self.votes if self.phase == GamePhase.VOTING else {},
            "logs": self.game_logs[-10:],
            "server_time": now,
            "turn_timestamp": self.turn_start_timestamp,
            "turn_end_timestamp": self.turn_end_timestamp,
            "turn_duration": self.turn_duration,
            "turn_remaining": turn_remaining,
            "discussion_duration": self.discussion_duration,
            "discussion_end_timestamp": self.discussion_end_timestamp,
            "discussion_remaining": discussion_remaining,
            "voting_duration": self.voting_duration,
            "voting_end_timestamp": self.voting_end_timestamp,
            "voting_remaining": voting_remaining,
            "role_catalog": ROLE_METADATA
        }

    def get_private_state_for_player(self, player_id: str) -> Dict[str, Any]:
        """Retorna el estado privado para un jugador específico."""
        public_state = self.get_public_state()
        if player_id not in self.players:
            return public_state

        player = self.players[player_id]
        current_turn_role = public_state.get("current_turn_role")

        is_your_turn = (player.original_role == current_turn_role) and not self.open_eyes_active

        your_role = player.get_role_name() if player.role else None
        if self.phase in (GamePhase.NIGHT_PHASE, GamePhase.DAY_PHASE, GamePhase.VOTING) and player.original_role:
            if self.phase == GamePhase.NIGHT_PHASE and player.original_role == "robber":
                your_role = player.get_role_name()
            else:
                your_role = player.original_role

        private_data: Dict[str, Any] = {
            "your_role": your_role,
            "your_original_role": player.original_role,
            "is_your_turn": is_your_turn
        }

        if is_your_turn:
            night_action_data = self.get_night_action_data_for_player(player_id)
            if night_action_data:
                private_data["night_action"] = night_action_data

        if self.phase in (GamePhase.NIGHT_PHASE, GamePhase.DAY_PHASE, GamePhase.VOTING):
            # Resumen nocturno unificado (cualquier rol con información o acción nocturna)
            night_record = self.night_actions_by_player.get(player_id)
            if night_record:
                private_data["night_action_record"] = night_record
                if night_record.get("summary_text"):
                    private_data["night_summary"] = night_record["summary_text"]

            # Campos legacy por rol para máxima compatibilidad
            if player.original_role == "werewolf":
                werewolf_last_center = self.werewolf_last_center_by_player.get(player_id)
                if werewolf_last_center:
                    private_data["werewolf_last_center"] = werewolf_last_center
            if player.original_role == "seer":
                seer_last_result = self.seer_last_result_by_player.get(player_id)
                if seer_last_result:
                    private_data["seer_last_result"] = seer_last_result
            if player.original_role == "robber":
                robber_last_target = self.robber_last_target_by_player.get(player_id)
                if robber_last_target:
                    private_data["robber_last_target"] = robber_last_target
            if player.original_role == "troublemaker":
                troublemaker_last_swap = self.troublemaker_last_swap_by_player.get(player_id)
                if troublemaker_last_swap:
                    private_data["troublemaker_last_swap"] = troublemaker_last_swap
            if player.original_role == "drunk":
                drunk_center = self.drunk_last_center_by_player.get(player_id)
                if drunk_center is not None:
                    private_data["drunk_last_center"] = drunk_center

        return {**public_state, **private_data}
