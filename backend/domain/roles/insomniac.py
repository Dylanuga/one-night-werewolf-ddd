from typing import Any, Dict, Optional

from .base import ROLE_METADATA, ROLE_NAMES_ES, Role, RoleType


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

