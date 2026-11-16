from typing import Any, Dict, List

from .roles import RoleFactory


def submit_vote(game: Any, voter_id: str, target_id: str) -> Dict[str, Any]:
    """Registra el voto de un jugador."""
    if game.phase.value != "voting":
        return {"success": False, "message": "No es la fase de votación"}
    if voter_id not in game.players:
        return {"success": False, "message": "Jugador no encontrado"}
    if target_id not in game.players:
        return {"success": False, "message": "Objetivo inválido"}
    if voter_id == target_id:
        return {"success": False, "message": "No puedes votarte a ti mismo"}

    game.votes[voter_id] = target_id
    all_voted = all(v is not None for v in game.votes.values())

    connected_pids = [pid for pid, p in game.players.items() if p.is_connected]
    all_connected_voted = bool(connected_pids) and all(game.votes.get(pid) is not None for pid in connected_pids)

    return {
        "success": True,
        "all_voted": all_voted,
        "all_connected_voted": all_connected_voted
    }


def can_finalize(game: Any, allow_partial: bool = False) -> bool:
    """Indica si todos han votado o se permite revelar."""
    if game.phase.value != "voting":
        return False
    if allow_partial:
        return any(v is not None for v in game.votes.values()) if game.votes else True

    connected_pids = [pid for pid, p in game.players.items() if p.is_connected]
    if connected_pids and all(game.votes.get(pid) is not None for pid in connected_pids):
        return True

    return bool(game.votes) and all(v is not None for v in game.votes.values())


def finalize_game(game: Any, game_end_phase: Any):
    """
    Motor de resolución de partida en 3 fases:
    1. Recuento de votos y linchamientos iniciales.
    2. Resolución de efectos al morir (ej. disparo del Cazador en cadena).
    3. Evaluación de condiciones de victoria por prioridad de bandos.
    """
    # Snapshot de roles finales
    game.final_roles = {pid: p.get_role_name() for pid, p in game.players.items()}

    # Fase 1: Recuento de votos
    vote_counts: Dict[str, int] = {}
    for target_id in game.votes.values():
        if target_id is None:
            continue
        vote_counts[target_id] = vote_counts.get(target_id, 0) + 1

    initial_eliminated: List[str] = []
    if vote_counts:
        max_votes = max(vote_counts.values())
        initial_eliminated = [pid for pid, count in vote_counts.items() if count == max_votes]

    # Fase 2: Efectos encadenados al morir (p. ej. Cazador / Hunter)
    eliminated_set: List[str] = list(initial_eliminated)
    chain_eliminated: List[str] = []
    hunter_shots: List[Dict[str, Any]] = []
    queue: List[str] = list(initial_eliminated)

    while queue:
        dead_pid = queue.pop(0)
        dead_role_name = game.final_roles.get(dead_pid)
        if not dead_role_name:
            continue
        try:
            role_obj = RoleFactory.create_role(dead_role_name)
            extra_targets = role_obj.on_death_trigger(game, dead_pid, game.votes)
            for extra_pid in extra_targets:
                if extra_pid not in eliminated_set:
                    eliminated_set.append(extra_pid)
                    chain_eliminated.append(extra_pid)
                    queue.append(extra_pid)
                    dead_name = game.players[dead_pid].name if dead_pid in game.players else dead_pid
                    extra_name = game.players[extra_pid].name if extra_pid in game.players else extra_pid
                    target_role = game.final_roles.get(extra_pid)
                    hunter_shots.append({
                        "hunter_id": dead_pid,
                        "hunter_name": dead_name,
                        "target_id": extra_pid,
                        "target_name": extra_name,
                        "target_role": target_role
                    })
                    game.add_log(f"🏹 {dead_name} (Cazador) cayó y disparó a {extra_name}.")
        except ValueError:
            continue

    game.eliminated_ids = eliminated_set
    game.chain_eliminated_ids = chain_eliminated

    # Fase 3: Evaluación de victoria por equipos
    werewolves_in_final = [pid for pid, role in game.final_roles.items() if role == "werewolf"]
    eliminated_werewolves = [pid for pid in game.eliminated_ids if game.final_roles.get(pid) == "werewolf"]
    direct_lynched_wolves = [pid for pid in initial_eliminated if game.final_roles.get(pid) == "werewolf"]
    wolf_killed_by_hunter = [s for s in hunter_shots if s.get("target_role") == "werewolf"]
    eliminated_tanners = [pid for pid in game.eliminated_ids if game.final_roles.get(pid) == "tanner"]
    villager_team_pids = [pid for pid, r in game.final_roles.items() if r not in ("werewolf", "tanner")]

    if eliminated_tanners and eliminated_werewolves:
        team = "tanner"
        if not direct_lynched_wolves and wolf_killed_by_hunter:
            shot = wolf_killed_by_hunter[0]
            message = (
                f"🏹 Ganan el Curtidor y los Aldeanos (el Cazador {shot['hunter_name']} "
                f"abatió al lobo {shot['target_name']} antes de morir)."
            )
        else:
            message = "Ganan el Curtidor y los Aldeanos (murieron el Curtidor y un Hombre Lobo)."
        winning_player_ids = eliminated_tanners + villager_team_pids
    elif eliminated_tanners:
        team = "tanner"
        message = "Gana el Curtidor (consiguió ser linchado)."
        winning_player_ids = eliminated_tanners
    elif eliminated_werewolves:
        team = "villagers"
        if not direct_lynched_wolves and wolf_killed_by_hunter:
            shot = wolf_killed_by_hunter[0]
            message = (
                f"🏹 El cazador ({shot['hunter_name']}) pudo dar con el lobo "
                f"({shot['target_name']}) antes de que lo linchen. ¡La aldea gana!"
            )
        else:
            message = "Los aldeanos ganan (eliminaron a un hombre lobo)."
        winning_player_ids = villager_team_pids
    else:
        if len(werewolves_in_final) == 0:
            team = "villagers"
            message = "Los aldeanos ganan (no había lobos en el pueblo)."
            winning_player_ids = villager_team_pids
        else:
            team = "werewolves"
            message = "Los lobos ganan (ningún lobo fue eliminado)."
            winning_player_ids = werewolves_in_final

    game.winners = {
        "team": team,
        "message": message,
        "eliminated_ids": game.eliminated_ids,
        "chain_eliminated_ids": game.chain_eliminated_ids,
        "hunter_shots": hunter_shots,
        "winning_player_ids": winning_player_ids
    }

    game.phase = game_end_phase
    game.add_log("🏁 Fin de partida")


def get_reveal_data(game: Any) -> Dict[str, Any]:
    """Retorna los datos de revelación final."""
    return {
        "final_roles": {pid: {"role": game.final_roles.get(pid), "name": p.name} for pid, p in game.players.items()},
        "original_roles": {pid: {"role": p.original_role, "name": p.name} for pid, p in game.players.items()},
        "eliminated_ids": game.eliminated_ids,
        "chain_eliminated_ids": game.chain_eliminated_ids,
        "hunter_shots": game.winners.get("hunter_shots", []),
        "votes": game.votes,
        "winners": game.winners
    }

