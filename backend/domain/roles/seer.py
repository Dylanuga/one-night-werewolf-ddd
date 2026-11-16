import random
from typing import Any, Dict, Optional

from .base import POS_NAMES_ES, ROLE_METADATA, ROLE_NAMES_ES, Role, RoleType


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

