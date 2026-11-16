import random
from typing import Any, Dict, Optional

from .base import POS_NAMES_ES, ROLE_METADATA, Role, RoleType


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

        from .factory import RoleFactory

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

