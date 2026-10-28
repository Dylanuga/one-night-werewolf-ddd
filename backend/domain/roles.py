# Definiciones de roles, catálogo centralizado y habilidades polimórficas
from abc import ABC, abstractmethod
import random
from typing import Dict, Any, Optional, List
from enum import Enum


class RoleType(Enum):
    WEREWOLF = "werewolf"
    VILLAGER = "villager"
    SEER = "seer"
    ROBBER = "robber"
    TROUBLEMAKER = "troublemaker"
    TANNER = "tanner"
    DRUNK = "drunk"
    MASON = "mason"
    HUNTER = "hunter"
    INSOMNIAC = "insomniac"


POS_NAMES_ES: Dict[int, str] = {
    0: "izquierda",
    1: "centro",
    2: "derecha"
}

# Catálogo único de metadatos de roles (fuente de verdad para dominio y API)
ROLE_METADATA: Dict[str, Dict[str, Any]] = {
    "werewolf": {
        "id": "werewolf",
        "name": "Lobo",
        "team": "werewolves",
        "turn_order": 1,
        "max_count": 2,
        "emoji": "🐺",
        "color": "#dc2626",
        "interaction_type": "select_center_cards",
        "description": "Se conocen entre ellos. Si está solo, ve una carta del centro."
    },
    "mason": {
        "id": "mason",
        "name": "Masón",
        "team": "villagers",
        "turn_order": 2,
        "max_count": 2,
        "emoji": "🔨",
        "color": "#0891b2",
        "interaction_type": "passive_info",
        "description": "Se conocen entre ellos (siempre van de 2 en 2)."
    },
    "seer": {
        "id": "seer",
        "name": "Vidente",
        "team": "villagers",
        "turn_order": 3,
        "max_count": 1,
        "emoji": "🔮",
        "color": "#7c3aed",
        "interaction_type": "select_player_or_center",
        "description": "Ve la carta de otro jugador o dos cartas del centro."
    },
    "robber": {
        "id": "robber",
        "name": "Ladrón",
        "team": "villagers",
        "turn_order": 4,
        "max_count": 1,
        "emoji": "🥷",
        "color": "#ea580c",
        "interaction_type": "select_one_player",
        "description": "Intercambia su carta con la de otro jugador y ve su nuevo rol."
    },
    "troublemaker": {
        "id": "troublemaker",
        "name": "Alborotadora",
        "team": "villagers",
        "turn_order": 5,
        "max_count": 1,
        "emoji": "🃏",
        "color": "#db2777",
        "interaction_type": "select_two_players",
        "description": "Intercambia las cartas de dos jugadores sin verlas."
    },
    "drunk": {
        "id": "drunk",
        "name": "Borracho",
        "team": "villagers",
        "turn_order": 6,
        "max_count": 1,
        "emoji": "🍺",
        "color": "#ca8a04",
        "interaction_type": "select_center_cards",
        "description": "Intercambia su carta con una del centro sin verla."
    },
    "insomniac": {
        "id": "insomniac",
        "name": "Insomne",
        "team": "villagers",
        "turn_order": 7,
        "max_count": 1,
        "emoji": "😴",
        "color": "#6366f1",
        "interaction_type": "passive_info",
        "description": "Al final de la noche, ve su propia carta (que pudo haber cambiado)."
    },
    "villager": {
        "id": "villager",
        "name": "Aldeano",
        "team": "villagers",
        "turn_order": 999,
        "max_count": 8,
        "emoji": "👨‍🌾",
        "color": "#16a34a",
        "interaction_type": "none",
        "description": "Sin habilidad especial. Debe deducir quiénes son los lobos."
    },
    "hunter": {
        "id": "hunter",
        "name": "Cazador",
        "team": "villagers",
        "turn_order": 999,
        "max_count": 1,
        "emoji": "🏹",
        "color": "#059669",
        "interaction_type": "none",
        "description": "Si muere linchado, también muere el jugador al que haya votado."
    },
    "tanner": {
        "id": "tanner",
        "name": "Curtidor",
        "team": "tanner",
        "turn_order": 999,
        "max_count": 1,
        "emoji": "🪣",
        "color": "#8b5cf6",
        "interaction_type": "none",
        "description": "Gana únicamente si consigue ser linchado."
    }
}

ROLE_NAMES_ES: Dict[str, str] = {
    role_id: meta["name"] for role_id, meta in ROLE_METADATA.items()
}


class Role(ABC):
    """Clase base abstracta para todos los roles del juego"""

    def __init__(self, role_type: RoleType):
        self.role_type = role_type
        self.turn_order = self._get_turn_order()

    @abstractmethod
    def _get_turn_order(self) -> int:
        """Define el orden de turnos en la noche"""
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """Retorna los metadatos estáticos del rol desde el catálogo central"""
        return ROLE_METADATA.get(self.role_type.value, {})

    def can_act_at_night(self) -> bool:
        """Determina si este rol tiene turno durante la noche"""
        return self.get_turn_order() < 999

    def get_turn_order(self) -> int:
        """Retorna el orden de turno de este rol"""
        return self.turn_order

    @abstractmethod
    def get_night_action_data(self, player_id: str, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retorna los datos que necesita ver el jugador en su turno nocturno"""
        pass

    @abstractmethod
    def execute_action(self, player_id: str, action_data: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta la acción nocturna sobre un snapshot de estado (compatibilidad)"""
        pass

    def execute_night_action_on_game(
        self,
        game: Any,
        player_id: str,
        action_data: Dict[str, Any],
        is_auto: bool = False
    ) -> Dict[str, Any]:
        """Ejecuta la acción nocturna directamente sobre la instancia de GameLogic"""
        return self.execute_action(player_id, action_data, game._get_game_state())

    def execute_auto_action_on_game(self, game: Any) -> Dict[str, Any]:
        """Ejecuta la acción automática aleatoria al expirar el tiempo del turno"""
        return {"success": False, "message": "Este rol no tiene acción automática"}

    def on_death_trigger(
        self,
        game: Any,
        dead_player_id: str,
        votes: Dict[str, Optional[str]]
    ) -> List[str]:
        """Hook polimórfico al morir en la votación (p. ej. disparo del Cazador)"""
        return []

    def __str__(self):
        return self.role_type.value


class WerewolfRole(Role):
    """Rol del hombre lobo"""

    def __init__(self):
        super().__init__(RoleType.WEREWOLF)

    def _get_turn_order(self) -> int:
        return ROLE_METADATA["werewolf"]["turn_order"]

    def get_night_action_data(self, player_id: str, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        werewolves_in_game = [
            pid for pid, player in game_state["players"].items()
            if player.get("original_role", player.get("role")) == "werewolf"
        ]

        # Caso A: Dos o más lobos entre jugadores
        if len(werewolves_in_game) >= 2:
            others = [wid for wid in werewolves_in_game if wid != player_id]
            other_werewolf = others[0]
            other_werewolf_name = game_state["players"][other_werewolf]["name"]
            return {
                "type": "show_other_werewolf",
                "interaction_type": "passive_info",
                "other_werewolf_name": other_werewolf_name,
                "message": f"El otro lobo es: {other_werewolf_name}",
                "summary_text": f"Tu compañero lobo es {other_werewolf_name}."
            }

        # Caso B: Lobo solitario (puede ver una carta del centro)
        if len(werewolves_in_game) == 1:
            return {
                "type": "can_view_center",
                "interaction_type": "select_center_cards",
                "message": "Eres el único lobo. Puedes ver una carta del centro.",
                "center_positions": [0, 1, 2]
            }

        return None

    def execute_action(self, player_id: str, action_data: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        werewolves_in_game = [
            pid for pid, player in game_state["players"].items()
            if player.get("original_role", player.get("role")) == "werewolf"
        ]

        if len(werewolves_in_game) == 1 and "center_position" in action_data:
            center_pos = action_data["center_position"]
            if isinstance(center_pos, int) and 0 <= center_pos < len(game_state["center_cards"]):
                center_role = game_state["center_cards"][center_pos]
                role_es = ROLE_NAMES_ES.get(center_role, center_role)
                pos_name = POS_NAMES_ES.get(center_pos, str(center_pos + 1))
                msg = f"Has visto {role_es} en la carta {pos_name}."
                return {
                    "success": True,
                    "role": "werewolf",
                    "player_id": player_id,
                    "werewolf_player_id": player_id,
                    "interaction_type": "select_center_cards",
                    "message": msg,
                    "summary_text": f"Lobo solitario - Carta del centro ({pos_name.capitalize()}): {role_es}",
                    "center_position": center_pos,
                    "center_role": center_role,
                    "revealed_cards": [
                        {"source": "center", "position": center_pos, "label": f"Carta {pos_name}", "role": center_role}
                    ]
                }

        return {"success": False, "message": "Acción no válida"}

    def execute_night_action_on_game(
        self,
        game: Any,
        player_id: str,
        action_data: Dict[str, Any],
        is_auto: bool = False
    ) -> Dict[str, Any]:
        if "werewolf" in game.roles_acted or game.werewolf_action_taken:
            return {"success": False, "message": "Acción de lobo ya ejecutada"}

        werewolves_in_game = [
            pid for pid, p in game.players.items()
            if p.original_role == "werewolf"
        ]
        if len(werewolves_in_game) != 1 or player_id not in werewolves_in_game:
            return {"success": False, "message": "Solo el lobo solitario puede ver una carta del centro"}

        center_pos = action_data.get("center_position")
        if center_pos is None or not isinstance(center_pos, int) or not (0 <= center_pos < len(game.center_cards)):
            return {"success": False, "message": "Posición de centro inválida"}

        center_role = game.center_cards[center_pos]
        role_es = ROLE_NAMES_ES.get(center_role, center_role)
        pos_name = POS_NAMES_ES.get(center_pos, str(center_pos + 1))
        prefix = "Acción aleatoria: " if is_auto else ""
        auto_tag = "🎲 (Aleatoria) " if is_auto else ""
        msg = f"{prefix}Has visto {role_es} en la carta {pos_name}."
        summary_text = f"{auto_tag}Lobo solitario - Carta del centro ({pos_name.capitalize()}): {role_es}"

        game.mark_role_acted("werewolf")
        record = {
            "role": "werewolf",
            "position": center_pos,
            "center_position": center_pos,
            "center_role": center_role,
            "message": msg,
            "summary_text": summary_text,
            "auto": is_auto,
            "revealed_cards": [
                {"source": "center", "position": center_pos, "label": f"Carta {pos_name}", "role": center_role}
            ]
        }
        game.werewolf_last_center_by_player[player_id] = {
            "position": center_pos,
            "role": center_role,
            "message": msg,
            "summary_text": summary_text,
            "auto": is_auto
        }
        game.record_player_night_action(player_id, record)

        return {
            "success": True,
            "role": "werewolf",
            "player_id": player_id,
            "werewolf_player_id": player_id,
            "interaction_type": "select_center_cards",
            "message": msg,
            "summary_text": summary_text,
            "center_position": center_pos,
            "center_role": center_role,
            "revealed_cards": record["revealed_cards"],
            "auto": is_auto
        }

    def execute_auto_action_on_game(self, game: Any) -> Dict[str, Any]:
        if "werewolf" in game.roles_acted or game.werewolf_action_taken:
            return {"success": False, "message": "Acción de lobo ya ejecutada"}

        werewolves_in_game = [
            pid for pid, p in game.players.items()
            if p.original_role == "werewolf"
        ]
        if len(werewolves_in_game) != 1 or not game.center_cards:
            return {"success": False, "message": "No hay lobo solitario activo"}

        werewolf_id = werewolves_in_game[0]
        center_pos = random.randint(0, len(game.center_cards) - 1)
        return self.execute_night_action_on_game(game, werewolf_id, {"center_position": center_pos}, is_auto=True)


class MasonRole(Role):
    """Rol del masón - se conocen entre ellos"""

    def __init__(self):
        super().__init__(RoleType.MASON)

    def _get_turn_order(self) -> int:
        return ROLE_METADATA["mason"]["turn_order"]

    def get_night_action_data(self, player_id: str, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        masons_in_game = [
            pid for pid, player in game_state["players"].items()
            if player.get("original_role", player.get("role")) == "mason"
        ]

        if len(masons_in_game) >= 2:
            others = [mid for mid in masons_in_game if mid != player_id]
            other_mason = others[0]
            other_mason_name = game_state["players"][other_mason]["name"]
            return {
                "type": "show_other_mason",
                "interaction_type": "passive_info",
                "other_mason_name": other_mason_name,
                "message": f"Tu compañero masón es: {other_mason_name}",
                "summary_text": f"Tu compañero masón es {other_mason_name}."
            }
        elif len(masons_in_game) == 1:
            return {
                "type": "alone",
                "interaction_type": "passive_info",
                "message": "Estás solo. Tu compañero masón no está en juego.",
                "summary_text": "Eres el único masón (el otro está en el centro)."
            }
        return None

    def execute_action(self, player_id: str, action_data: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True, "message": "Los masones se han reconocido"}


class SeerRole(Role):
    """Rol de la vidente/pitonisa"""

    def __init__(self):
        super().__init__(RoleType.SEER)

    def _get_turn_order(self) -> int:
        return ROLE_METADATA["seer"]["turn_order"]

    def get_night_action_data(self, player_id: str, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        players = [
            {"id": pid, "name": player["name"]}
            for pid, player in game_state["players"].items()
            if pid != player_id
        ]
        return {
            "type": "seer_choose",
            "interaction_type": "select_player_or_center",
            "message": "Puedes ver la carta de otro jugador o dos cartas del centro.",
            "players": players,
            "center_positions": [0, 1, 2]
        }

    def execute_action(self, player_id: str, action_data: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        target_player_id = action_data.get("target_player_id")
        if target_player_id:
            if target_player_id == player_id:
                return {"success": False, "message": "No puedes ver tu propia carta"}
            target_player = game_state["players"].get(target_player_id)
            if not target_player:
                return {"success": False, "message": "Jugador no válido"}
            target_role = target_player["role"]
            target_name = target_player["name"]
            role_es = ROLE_NAMES_ES.get(target_role, target_role)
            return {
                "success": True,
                "message": f"{target_name} es {role_es}.",
                "seen_player": {
                    "id": target_player_id,
                    "name": target_name,
                    "role": target_role
                }
            }

        center_positions = action_data.get("center_positions")
        if isinstance(center_positions, list) and len(center_positions) == 2:
            pos_a, pos_b = center_positions[0], center_positions[1]
            if pos_a == pos_b:
                return {"success": False, "message": "Debes elegir dos cartas distintas"}
            if not all(isinstance(pos, int) and 0 <= pos < len(game_state["center_cards"]) for pos in [pos_a, pos_b]):
                return {"success": False, "message": "Posiciones de centro inválidas"}

            role_a = game_state["center_cards"][pos_a]
            role_b = game_state["center_cards"][pos_b]
            role_a_es = ROLE_NAMES_ES.get(role_a, role_a)
            role_b_es = ROLE_NAMES_ES.get(role_b, role_b)
            pos_a_name = POS_NAMES_ES.get(pos_a, str(pos_a + 1))
            pos_b_name = POS_NAMES_ES.get(pos_b, str(pos_b + 1))
            return {
                "success": True,
                "message": f"Has visto {role_a_es} en la {pos_a_name} y {role_b_es} en la {pos_b_name}.",
                "seen_center": [
                    {"position": pos_a, "role": role_a},
                    {"position": pos_b, "role": role_b}
                ]
            }

        return {"success": False, "message": "Acción no válida"}

    def execute_night_action_on_game(
        self,
        game: Any,
        player_id: str,
        action_data: Dict[str, Any],
        is_auto: bool = False
    ) -> Dict[str, Any]:
        if "seer" in game.roles_acted or game.seer_action_taken:
            return {"success": False, "message": "Acción de vidente ya ejecutada"}

        prefix = "Acción aleatoria: " if is_auto else ""
        auto_tag = "🎲 (Aleatoria) " if is_auto else ""

        target_player_id = action_data.get("target_player_id")
        if target_player_id:
            if target_player_id == player_id:
                return {"success": False, "message": "No puedes ver tu propia carta"}
            if target_player_id not in game.players:
                return {"success": False, "message": "Jugador no válido"}

            target_player = game.players[target_player_id]
            target_role = target_player.get_role_name()
            target_name = target_player.name
            role_es = ROLE_NAMES_ES.get(target_role, target_role)
            msg = f"{prefix}{target_name} es {role_es}."
            summary_text = f"{auto_tag}Viste el rol de {target_name}: {role_es}"

            game.mark_role_acted("seer")
            seen_player_data = {
                "id": target_player_id,
                "name": target_name,
                "role": target_role
            }
            revealed = [
                {"source": "player", "player_id": target_player_id, "label": target_name, "role": target_role}
            ]
            record = {
                "role": "seer",
                "mode": "player",
                "seen_player": seen_player_data,
                "message": msg,
                "summary_text": summary_text,
                "revealed_cards": revealed,
                "auto": is_auto
            }
            game.seer_last_result_by_player[player_id] = record
            game.record_player_night_action(player_id, record)

            return {
                "success": True,
                "role": "seer",
                "player_id": player_id,
                "seer_player_id": player_id,
                "interaction_type": "select_player_or_center",
                "message": msg,
                "summary_text": summary_text,
                "seen_player": seen_player_data,
                "revealed_cards": revealed,
                "auto": is_auto
            }

        center_positions = action_data.get("center_positions")
        if isinstance(center_positions, list) and len(center_positions) == 2:
            pos_a, pos_b = center_positions[0], center_positions[1]
            if pos_a == pos_b:
                return {"success": False, "message": "Debes elegir dos cartas distintas"}
            if not all(isinstance(pos, int) and 0 <= pos < len(game.center_cards) for pos in [pos_a, pos_b]):
                return {"success": False, "message": "Posiciones de centro inválidas"}

            role_a = game.center_cards[pos_a]
            role_b = game.center_cards[pos_b]
            role_a_es = ROLE_NAMES_ES.get(role_a, role_a)
            role_b_es = ROLE_NAMES_ES.get(role_b, role_b)
            pos_a_name = POS_NAMES_ES.get(pos_a, str(pos_a + 1))
            pos_b_name = POS_NAMES_ES.get(pos_b, str(pos_b + 1))
            msg = f"{prefix}Has visto {role_a_es} en la {pos_a_name} y {role_b_es} en la {pos_b_name}."
            summary_text = f"{auto_tag}Cartas del centro vistas: {pos_a_name.capitalize()}: {role_a_es} | {pos_b_name.capitalize()}: {role_b_es}"

            game.mark_role_acted("seer")
            seen_center_data = [
                {"position": pos_a, "role": role_a},
                {"position": pos_b, "role": role_b}
            ]
            revealed = [
                {"source": "center", "position": pos_a, "label": f"Carta {pos_a_name}", "role": role_a},
                {"source": "center", "position": pos_b, "label": f"Carta {pos_b_name}", "role": role_b}
            ]
            record = {
                "role": "seer",
                "mode": "center",
                "seen_center": seen_center_data,
                "message": msg,
                "summary_text": summary_text,
                "revealed_cards": revealed,
                "auto": is_auto
            }
            game.seer_last_result_by_player[player_id] = record
            game.record_player_night_action(player_id, record)

            return {
                "success": True,
                "role": "seer",
                "player_id": player_id,
                "seer_player_id": player_id,
                "interaction_type": "select_player_or_center",
                "message": msg,
                "summary_text": summary_text,
                "seen_center": seen_center_data,
                "revealed_cards": revealed,
                "auto": is_auto
            }

        return {"success": False, "message": "Acción no válida"}

    def execute_auto_action_on_game(self, game: Any) -> Dict[str, Any]:
        if "seer" in game.roles_acted or game.seer_action_taken:
            return {"success": False, "message": "Acción de vidente ya ejecutada"}

        seer_id = next((pid for pid, p in game.players.items() if p.original_role == "seer"), None)
        if not seer_id:
            return {"success": False, "message": "No hay vidente activa"}

        possible_targets = [pid for pid in game.players.keys() if pid != seer_id]
        can_see_center = len(game.center_cards) >= 2

        if possible_targets and can_see_center:
            choice = random.choice(["player", "center"])
        elif possible_targets:
            choice = "player"
        elif can_see_center:
            choice = "center"
        else:
            return {"success": False, "message": "No hay objetivos válidos para vidente"}

        if choice == "player":
            target_id = random.choice(possible_targets)
            return self.execute_night_action_on_game(game, seer_id, {"target_player_id": target_id}, is_auto=True)
        else:
            positions = sorted(random.sample(range(len(game.center_cards)), 2))
            return self.execute_night_action_on_game(game, seer_id, {"center_positions": positions}, is_auto=True)


class RobberRole(Role):
    """Rol del ladrón - intercambia su rol con otro jugador y ve el nuevo rol"""

    def __init__(self):
        super().__init__(RoleType.ROBBER)

    def _get_turn_order(self) -> int:
        return ROLE_METADATA["robber"]["turn_order"]

    def get_night_action_data(self, player_id: str, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        players = [
            {"id": pid, "name": player["name"]}
            for pid, player in game_state["players"].items()
            if pid != player_id
        ]
        return {
            "type": "robber_choose",
            "interaction_type": "select_one_player",
            "message": "Elige un jugador para robar su rol (no puedes elegirte a ti mismo).",
            "players": players
        }

    def execute_action(self, player_id: str, action_data: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        target_player_id = action_data.get("target_player_id")
        if not target_player_id or target_player_id == player_id or target_player_id not in game_state["players"]:
            return {"success": False, "message": "Jugador no válido"}
        target = game_state["players"][target_player_id]
        new_role = target["role"]
        new_role_es = ROLE_NAMES_ES.get(new_role, new_role)
        return {
            "success": True,
            "message": f"Has robado el rol de {target['name']}. Tu nuevo rol es {new_role_es}.",
            "robbed_player": {"id": target_player_id, "name": target["name"]},
            "new_role": new_role
        }

    def execute_night_action_on_game(
        self,
        game: Any,
        player_id: str,
        action_data: Dict[str, Any],
        is_auto: bool = False
    ) -> Dict[str, Any]:
        if "robber" in game.roles_acted or game.robber_action_taken:
            return {"success": False, "message": "Acción de ladrón ya ejecutada"}

        target_player_id = action_data.get("target_player_id")
        if not target_player_id:
            return {"success": False, "message": "Debes elegir un jugador"}
        if target_player_id == player_id:
            return {"success": False, "message": "No puedes robarte a ti mismo"}
        if target_player_id not in game.players:
            return {"success": False, "message": "Jugador no válido"}

        robber = game.players[player_id]
        target = game.players[target_player_id]

        robber.role, target.role = target.role, robber.role
        game.mark_role_acted("robber")

        new_role = robber.get_role_name()
        new_role_es = ROLE_NAMES_ES.get(new_role, new_role)
        prefix = "Acción aleatoria: " if is_auto else ""
        auto_tag = "🎲 (Aleatoria) " if is_auto else ""
        msg = f"{prefix}Has robado el rol de {target.name}. Tu nuevo rol es {new_role_es}."
        summary_text = f"{auto_tag}Robaste la carta de {target.name} y tu nuevo rol es {new_role_es}."

        revealed = [
            {"source": "player", "player_id": target_player_id, "label": target.name, "role": new_role}
        ]
        record = {
            "role": "robber",
            "id": target_player_id,
            "name": target.name,
            "new_role": new_role,
            "message": msg,
            "summary_text": summary_text,
            "revealed_cards": revealed,
            "auto": is_auto
        }
        game.robber_last_target_by_player[player_id] = record
        game.record_player_night_action(player_id, record)

        return {
            "success": True,
            "role": "robber",
            "player_id": player_id,
            "robber_player_id": player_id,
            "interaction_type": "select_one_player",
            "message": msg,
            "summary_text": summary_text,
            "robbed_player": {"id": target_player_id, "name": target.name},
            "new_role": new_role,
            "revealed_cards": revealed,
            "auto": is_auto
        }

    def execute_auto_action_on_game(self, game: Any) -> Dict[str, Any]:
        if "robber" in game.roles_acted or game.robber_action_taken:
            return {"success": False, "message": "Acción de ladrón ya ejecutada"}

        robber_id = next((pid for pid, p in game.players.items() if p.original_role == "robber"), None)
        if not robber_id:
            return {"success": False, "message": "No hay ladrón activo"}

        possible_targets = [pid for pid in game.players.keys() if pid != robber_id]
        if not possible_targets:
            return {"success": False, "message": "No hay objetivos válidos"}

        target_player_id = random.choice(possible_targets)
        return self.execute_night_action_on_game(game, robber_id, {"target_player_id": target_player_id}, is_auto=True)


class TroublemakerRole(Role):
    """Rol de la alborotadora - intercambia cartas de dos jugadores sin verlas"""

    def __init__(self):
        super().__init__(RoleType.TROUBLEMAKER)

    def _get_turn_order(self) -> int:
        return ROLE_METADATA["troublemaker"]["turn_order"]

    def get_night_action_data(self, player_id: str, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        players = [
            {"id": pid, "name": player["name"]}
            for pid, player in game_state["players"].items()
        ]
        return {
            "type": "troublemaker_choose",
            "interaction_type": "select_two_players",
            "message": "Elige dos jugadores para intercambiar sus roles (puede incluirte).",
            "players": players
        }

    def execute_action(self, player_id: str, action_data: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        target_a = action_data.get("target_player_id_a")
        target_b = action_data.get("target_player_id_b")
        if not target_a or not target_b or target_a == target_b:
            return {"success": False, "message": "Debes elegir dos jugadores distintos"}
        if target_a not in game_state["players"] or target_b not in game_state["players"]:
            return {"success": False, "message": "Jugador no válido"}
        name_a = game_state["players"][target_a]["name"]
        name_b = game_state["players"][target_b]["name"]
        return {
            "success": True,
            "message": f"Has cambiado a {name_a} con {name_b}."
        }

    def execute_night_action_on_game(
        self,
        game: Any,
        player_id: str,
        action_data: Dict[str, Any],
        is_auto: bool = False
    ) -> Dict[str, Any]:
        if "troublemaker" in game.roles_acted or game.troublemaker_action_taken:
            return {"success": False, "message": "Acción de alborotadora ya ejecutada"}

        target_a = action_data.get("target_player_id_a")
        target_b = action_data.get("target_player_id_b")

        if not target_a or not target_b:
            return {"success": False, "message": "Debes elegir dos jugadores"}
        if target_a == target_b:
            return {"success": False, "message": "Debes elegir dos jugadores distintos"}
        if target_a not in game.players or target_b not in game.players:
            return {"success": False, "message": "Jugador no válido"}

        player_a = game.players[target_a]
        player_b = game.players[target_b]

        player_a.role, player_b.role = player_b.role, player_a.role
        game.mark_role_acted("troublemaker")

        prefix = "Acción aleatoria: " if is_auto else ""
        auto_tag = "🎲 (Aleatoria) " if is_auto else ""
        msg = f"{prefix}Has cambiado a {player_a.name} con {player_b.name}."
        summary_text = f"{auto_tag}Intercambiaste las cartas de {player_a.name} y {player_b.name}."

        record = {
            "role": "troublemaker",
            "a": {"id": target_a, "name": player_a.name},
            "b": {"id": target_b, "name": player_b.name},
            "message": msg,
            "summary_text": summary_text,
            "revealed_cards": [],
            "auto": is_auto
        }
        game.troublemaker_last_swap_by_player[player_id] = record
        game.record_player_night_action(player_id, record)

        return {
            "success": True,
            "role": "troublemaker",
            "player_id": player_id,
            "troublemaker_player_id": player_id,
            "interaction_type": "select_two_players",
            "message": msg,
            "summary_text": summary_text,
            "swapped_players": record,
            "revealed_cards": [],
            "auto": is_auto
        }

    def execute_auto_action_on_game(self, game: Any) -> Dict[str, Any]:
        if "troublemaker" in game.roles_acted or game.troublemaker_action_taken:
            return {"success": False, "message": "Acción de alborotadora ya ejecutada"}

        troublemaker_id = next((pid for pid, p in game.players.items() if p.original_role == "troublemaker"), None)
        if not troublemaker_id:
            return {"success": False, "message": "No hay alborotadora activa"}

        player_ids = list(game.players.keys())
        if len(player_ids) < 2:
            return {"success": False, "message": "No hay suficientes jugadores para intercambiar"}

        target_a, target_b = random.sample(player_ids, 2)
        return self.execute_night_action_on_game(
            game,
            troublemaker_id,
            {"target_player_id_a": target_a, "target_player_id_b": target_b},
            is_auto=True
        )


class DrunkRole(Role):
    """Rol del borracho - intercambia su carta con una del centro sin verla"""

    def __init__(self):
        super().__init__(RoleType.DRUNK)

    def _get_turn_order(self) -> int:
        return ROLE_METADATA["drunk"]["turn_order"]

    def get_night_action_data(self, player_id: str, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return {
            "type": "drunk_choose_center",
            "interaction_type": "select_center_cards",
            "message": "Elige una carta del centro para intercambiarla con la tuya (no la verás).",
            "center_positions": [0, 1, 2]
        }

    def execute_action(self, player_id: str, action_data: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        center_pos = action_data.get("center_position")
        if center_pos is None or not isinstance(center_pos, int) or not (0 <= center_pos < len(game_state["center_cards"])):
            return {"success": False, "message": "Posición de centro inválida"}
        pos_name = POS_NAMES_ES.get(center_pos, str(center_pos + 1))
        return {
            "success": True,
            "message": f"Has intercambiado tu carta con la del centro {center_pos + 1} ({pos_name}).",
            "center_position": center_pos
        }

    def execute_night_action_on_game(
        self,
        game: Any,
        player_id: str,
        action_data: Dict[str, Any],
        is_auto: bool = False
    ) -> Dict[str, Any]:
        if "drunk" in game.roles_acted or game.drunk_action_taken:
            return {"success": False, "message": "Acción de borracho ya ejecutada"}

        center_pos = action_data.get("center_position")
        if center_pos is None or not isinstance(center_pos, int) or not (0 <= center_pos < len(game.center_cards)):
            return {"success": False, "message": "Posición de centro inválida"}

        player = game.players[player_id]
        center_role = game.center_cards[center_pos]
        game.center_cards[center_pos] = player.get_role_name()
        player.role = RoleFactory.create_role(center_role)

        game.mark_role_acted("drunk")
        game.drunk_last_center_by_player[player_id] = center_pos

        pos_name = POS_NAMES_ES.get(center_pos, str(center_pos + 1))
        prefix = "Acción aleatoria: " if is_auto else ""
        auto_tag = "🎲 (Aleatoria) " if is_auto else ""
        msg = f"{prefix}Has intercambiado tu carta con la del centro {center_pos + 1} ({pos_name})."
        summary_text = f"{auto_tag}Intercambiaste tu carta con la carta {pos_name} del centro."

        record = {
            "role": "drunk",
            "center_position": center_pos,
            "message": msg,
            "summary_text": summary_text,
            "revealed_cards": [],
            "auto": is_auto
        }
        game.record_player_night_action(player_id, record)

        return {
            "success": True,
            "role": "drunk",
            "player_id": player_id,
            "drunk_player_id": player_id,
            "interaction_type": "select_center_cards",
            "message": msg,
            "summary_text": summary_text,
            "center_position": center_pos,
            "revealed_cards": [],
            "auto": is_auto
        }

    def execute_auto_action_on_game(self, game: Any) -> Dict[str, Any]:
        if "drunk" in game.roles_acted or game.drunk_action_taken:
            return {"success": False, "message": "Acción de borracho ya ejecutada"}

        drunk_id = next((pid for pid, p in game.players.items() if p.original_role == "drunk"), None)
        if not drunk_id or not game.center_cards:
            return {"success": False, "message": "No hay borracho activo"}

        center_pos = random.randint(0, len(game.center_cards) - 1)
        return self.execute_night_action_on_game(game, drunk_id, {"center_position": center_pos}, is_auto=True)


class InsomniacRole(Role):
    """Rol del insomne - al final de la noche, ve su propia carta"""

    def __init__(self):
        super().__init__(RoleType.INSOMNIAC)

    def _get_turn_order(self) -> int:
        return ROLE_METADATA["insomniac"]["turn_order"]

    def get_night_action_data(self, player_id: str, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        player = game_state["players"].get(player_id)
        if not player:
            return None
        current_role = player.get("role")
        role_name = ROLE_NAMES_ES.get(current_role, current_role)
        return {
            "type": "insomniac_reveal",
            "interaction_type": "passive_info",
            "message": f"Al despertarte antes de tiempo tu nuevo rol es: {role_name}.",
            "summary_text": f"Al final de la noche viste que tu carta era: {role_name}.",
            "current_role": current_role,
            "revealed_cards": [
                {"source": "self", "player_id": player_id, "label": "Tu carta final", "role": current_role}
            ]
        }

    def execute_action(self, player_id: str, action_data: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True, "message": "Insomne: información revelada"}


class VillagerRole(Role):
    """Rol del aldeano - sin acciones nocturnas"""

    def __init__(self):
        super().__init__(RoleType.VILLAGER)

    def _get_turn_order(self) -> int:
        return ROLE_METADATA["villager"]["turn_order"]

    def get_night_action_data(self, player_id: str, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return None

    def execute_action(self, player_id: str, action_data: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": False, "message": "Los aldeanos no tienen acciones nocturnas"}


class TannerRole(Role):
    """Rol del curtidor - gana si muere"""

    def __init__(self):
        super().__init__(RoleType.TANNER)

    def _get_turn_order(self) -> int:
        return ROLE_METADATA["tanner"]["turn_order"]

    def get_night_action_data(self, player_id: str, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return None

    def execute_action(self, player_id: str, action_data: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": False, "message": "El curtidor no tiene acciones nocturnas"}


class HunterRole(Role):
    """Rol del cazador - si muere linchado, también muere el jugador al que votó"""

    def __init__(self):
        super().__init__(RoleType.HUNTER)

    def _get_turn_order(self) -> int:
        return ROLE_METADATA["hunter"]["turn_order"]

    def get_night_action_data(self, player_id: str, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return None

    def execute_action(self, player_id: str, action_data: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": False, "message": "El cazador no tiene acciones nocturnas"}

    def on_death_trigger(
        self,
        game: Any,
        dead_player_id: str,
        votes: Dict[str, Optional[str]]
    ) -> List[str]:
        target_id = votes.get(dead_player_id)
        if target_id and target_id != dead_player_id and target_id in game.players:
            return [target_id]
        return []


class RoleFactory:
    """Factory para crear instancias de roles y consultar el catálogo"""

    _ROLE_CLASSES = {
        "werewolf": WerewolfRole,
        "villager": VillagerRole,
        "seer": SeerRole,
        "robber": RobberRole,
        "troublemaker": TroublemakerRole,
        "tanner": TannerRole,
        "drunk": DrunkRole,
        "mason": MasonRole,
        "hunter": HunterRole,
        "insomniac": InsomniacRole
    }

    @classmethod
    def create_role(cls, role_type: str) -> Role:
        if role_type not in cls._ROLE_CLASSES:
            raise ValueError(f"Tipo de rol desconocido: {role_type}")
        return cls._ROLE_CLASSES[role_type]()

    @classmethod
    def get_catalog(cls) -> Dict[str, Dict[str, Any]]:
        return ROLE_METADATA.copy()
