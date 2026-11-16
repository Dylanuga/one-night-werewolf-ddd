from typing import Any, Dict, List, Optional

from .roles import RoleFactory


def calculate_night_turns(game: Any) -> List[str]:
    """Calcula el orden de turnos nocturnos basado en roles únicos con acciones."""
    roles_in_play = {p.get_role_name() for p in game.players.values()}.union(set(game.center_cards))

    roles_with_turns = {}
    for role_name in roles_in_play:
        role_instance = RoleFactory.create_role(role_name)
        if role_instance and role_instance.can_act_at_night():
            roles_with_turns[role_name] = role_instance.get_turn_order()

    sorted_roles = sorted(roles_with_turns.items(), key=lambda item: item[1])
    night_turns = [role for role, _ in sorted_roles]
    print(f"🔧 TURNOS NOCTURNOS CALCULADOS (POR ROL): {night_turns}")
    return night_turns


def get_night_action_data_for_player(game: Any, player_id: str) -> Optional[Dict[str, Any]]:
    """Retorna los datos de acción nocturna para un jugador específico (y registra info pasiva)."""
    if game.phase.value != "night_phase" or player_id not in game.players:
        return None

    player = game.players[player_id]
    if not player.original_role:
        return None

    game_state = game._get_game_state()
    original_role_class = RoleFactory.create_role(player.original_role)
    data = original_role_class.get_night_action_data(player_id, game_state)

    # Si es información pasiva (ej. 2 lobos, masones, insomne) y es su turno, guardar en el resumen nocturno
    if data and data.get("interaction_type") == "passive_info" and game.get_current_turn_role() == player.original_role:
        game.record_player_night_action(player_id, {
            "role": player.original_role,
            "interaction_type": "passive_info",
            "message": data.get("message", ""),
            "summary_text": data.get("summary_text", data.get("message", "")),
            "revealed_cards": data.get("revealed_cards", []),
            "auto": False
        })

    return data


def execute_night_action(
    game: Any,
    player_id: str,
    action_data: Dict[str, Any],
    role_names_es: Dict[str, str]
) -> Dict[str, Any]:
    """Ejecuta una acción nocturna delegando polimórficamente en la clase de rol."""
    if game.phase.value != "night_phase":
        return {"success": False, "message": "No es la fase nocturna"}
    if player_id not in game.players:
        return {"success": False, "message": "Jugador no encontrado"}

    player = game.players[player_id]
    current_role = game.get_current_turn_role()

    if player.original_role != current_role:
        return {"success": False, "message": "No es el turno de tu rol"}
    if not player.role:
        return {"success": False, "message": "No tienes rol asignado"}

    role_instance = RoleFactory.create_role(current_role)
    result = role_instance.execute_night_action_on_game(game, player_id, action_data, is_auto=False)

    if result.get("success") and game.test_mode:
        role_es = role_names_es.get(player.original_role, player.original_role)
        game.add_log(f"🎯 {player.name} ({role_es}) ejecutó su acción.")
    return result


def execute_current_turn_auto_action(game: Any) -> Dict[str, Any]:
    """Ejecuta polimórficamente la acción automática aleatoria del rol cuyo turno expira."""
    current_role = game.get_current_turn_role()
    if not current_role:
        return {"success": False, "message": "No hay turno activo"}

    role_instance = RoleFactory.create_role(current_role)
    return role_instance.execute_auto_action_on_game(game)


def advance_night_turn(game: Any, role_names_es: Dict[str, str]) -> bool:
    """Avanza al siguiente turno nocturno."""
    if game.phase.value != "night_phase":
        return False

    game.current_turn_index += 1

    if game.current_turn_index >= len(game.night_turns):
        game.night_finished = True
        return True

    current_role = game.get_current_turn_role()
    if current_role:
        game.add_log(f"--- Fase: {role_names_es.get(current_role, current_role)} ---")
        game.mark_role_acted(current_role, False)
    return True

