import random
from typing import Any, Dict, Optional

from .base import POS_NAMES_ES, ROLE_METADATA, ROLE_NAMES_ES, Role, RoleType


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

