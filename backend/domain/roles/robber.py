import random
from typing import Any, Dict, Optional

from .base import ROLE_METADATA, ROLE_NAMES_ES, Role, RoleType


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

