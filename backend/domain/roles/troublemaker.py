import random
from typing import Any, Dict, Optional

from .base import ROLE_METADATA, Role, RoleType


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

