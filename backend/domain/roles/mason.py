from typing import Any, Dict, Optional

from .base import ROLE_METADATA, Role, RoleType


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

