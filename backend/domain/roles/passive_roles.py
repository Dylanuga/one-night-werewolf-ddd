from typing import Any, Dict, List, Optional

from .base import ROLE_METADATA, Role, RoleType


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

