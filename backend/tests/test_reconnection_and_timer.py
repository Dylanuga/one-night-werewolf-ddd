# backend/tests/test_reconnection_and_timer.py
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domain.game_logic import GameLogic, GamePhase
from domain.roles import RoleFactory


def test_reconnection_during_phases():
    print("🧪 TEST 1: Reconexión durante diferentes fases del juego...")
    game = GameLogic("RECON")
    assert game.add_player("p1", "HostPlayer", "socket_1", is_host=True)
    assert game.add_player("p2", "PlayerTwo", "socket_2")
    assert game.add_player("p3", "PlayerThree", "socket_3")

    roles = ['werewolf', 'villager', 'seer', 'robber', 'villager', 'villager']
    assert game.set_selected_roles(roles)
    assert game.start_game()
    assert game.phase == GamePhase.NIGHT_PHASE

    game.players["p2"].disconnect()
    assert not game.players["p2"].is_connected

    success = game.add_player("p2", "PlayerTwo", "socket_2_new")
    assert success, "La reconexión durante la noche debe permitirse"
    assert game.players["p2"].is_connected
    assert game.players["p2"].socket_id == "socket_2_new"

    game.phase = GamePhase.DAY_PHASE
    game.players["p3"].disconnect()
    success = game.add_player("p3", "PlayerThree", "socket_3_new")
    assert success, "La reconexión durante el día debe permitirse"
    assert game.players["p3"].socket_id == "socket_3_new"

    assert game.start_voting_phase()
    assert game.phase == GamePhase.VOTING
    game.players["p1"].disconnect()
    success = game.add_player("p1", "HostPlayer", "socket_1_new")
    assert success, "La reconexión durante votación debe permitirse"
    assert game.players["p1"].socket_id == "socket_1_new"


def test_timer_configuration():
    print("\n🧪 TEST 2: Configuración de temporizadores de debate...")
    game = GameLogic("TIMER")
    assert game.discussion_duration == 300, "Duración por defecto debe ser 300s (5 min)"

    assert game.set_discussion_duration(120)
    assert game.discussion_duration == 120, "Debe aceptar 120s (2 min)"

    assert game.set_discussion_duration(600)
    assert game.discussion_duration == 600, "Debe aceptar 600s (10 min)"

    assert not game.set_discussion_duration(999)
    assert game.discussion_duration == 600, "Valor inválido debe mantener el anterior"


def test_voting_with_disconnected_or_missing_votes():
    print("\n🧪 TEST 3: Votación con jugadores caídos o votos parciales...")
    game = GameLogic("VOTE")
    game.add_player("p1", "Host", "s1", is_host=True)
    game.add_player("p2", "Player2", "s2")
    game.add_player("p3", "Player3", "s3")

    game.phase = GamePhase.DAY_PHASE
    assert game.start_voting_phase()

    res = game.submit_vote("p1", "p2")
    assert res['success']
    assert not res['all_voted']
    assert not res['all_connected_voted']

    assert not game.can_finalize(allow_partial=False)
    assert game.can_finalize(allow_partial=True)

    game.players["p3"].disconnect()
    res2 = game.submit_vote("p2", "p1")
    assert res2['success']
    assert not res2['all_voted'], "p3 no ha votado aún"
    assert res2['all_connected_voted'], "Todos los conectados (p1 y p2) ya votaron"

    assert game.can_finalize(allow_partial=False)

    game._finalize_game()
    assert game.eliminated_ids in (["p1", "p2"], ["p2", "p1"])


def test_auto_actions_and_reset_to_lobby():
    print("\n🧪 TEST 4: Acciones automáticas aleatorias (Vidente y Lobo Solitario) y Volver al Lobby...")
    game = GameLogic("AUTO")
    game.add_player("p1", "HostSeer", "s1", is_host=True)
    game.add_player("p2", "LoneWolf", "s2")
    game.add_player("p3", "VillagerP", "s3")

    roles = ['seer', 'werewolf', 'villager', 'robber', 'troublemaker', 'drunk']
    assert game.set_selected_roles(roles)
    game.enable_test_mode({'players': ['seer', 'werewolf', 'villager'], 'center': ['robber', 'troublemaker', 'drunk']})
    assert game.start_game()

    assert game.get_current_turn_role() == "werewolf"
    ww_auto = game.execute_werewolf_auto_action()
    assert ww_auto and ww_auto.get("success") and ww_auto.get("auto") is True
    assert ww_auto.get("werewolf_player_id") == "p2"
    assert ww_auto.get("center_position") in (0, 1, 2)
    assert ww_auto.get("center_role") in ("robber", "troublemaker", "drunk")
    p2_priv = game.get_private_state_for_player("p2")
    assert p2_priv.get("werewolf_last_center") is not None

    game.advance_night_turn()
    assert game.get_current_turn_role() == "seer"
    seer_auto = game.execute_seer_auto_action()
    assert seer_auto and seer_auto.get("success") and seer_auto.get("auto") is True
    assert seer_auto.get("seer_player_id") == "p1"
    assert "seen_player" in seer_auto or "seen_center" in seer_auto
    p1_priv = game.get_private_state_for_player("p1")
    assert p1_priv.get("seer_last_result") is not None

    game.phase = GamePhase.GAME_END
    assert game.reset_game("role_selection")
    assert game.phase == GamePhase.ROLE_SELECTION
    assert game.reset_game("lobby")
    assert game.phase == GamePhase.LOBBY
    assert game.selected_roles == []


def test_polymorphic_roles_catalog_and_death_triggers():
    print("\n🧪 TEST 5: Catálogo centralizado, contrato unificado y disparo del Cazador (Hunter)...")
    catalog = RoleFactory.get_catalog()
    assert "werewolf" in catalog and "seer" in catalog and "hunter" in catalog and "tanner" in catalog
    assert catalog["seer"]["interaction_type"] == "select_player_or_center"

    game = GameLogic("POLY")
    game.add_player("p1", "HunterPlayer", "s1", is_host=True)
    game.add_player("p2", "WolfPlayer", "s2")
    game.add_player("p3", "SeerPlayer", "s3")

    roles = ["hunter", "werewolf", "seer", "villager", "robber", "drunk"]
    assert game.set_selected_roles(roles)
    game.enable_test_mode({
        "players": ["hunter", "werewolf", "seer"],
        "center": ["villager", "robber", "drunk"]
    })
    assert game.start_game()

    assert game.get_current_turn_role() == "werewolf"
    res_ww = game.execute_current_turn_auto_action()
    assert res_ww["success"] and res_ww["auto"] is True
    assert res_ww.get("summary_text") and isinstance(res_ww.get("revealed_cards"), list)
    p2_priv = game.get_private_state_for_player("p2")
    assert p2_priv.get("night_summary") == res_ww["summary_text"]

    game.advance_night_turn()
    assert game.get_current_turn_role() == "seer"
    res_seer = game.execute_current_turn_auto_action()
    assert res_seer["success"] and res_seer["auto"] is True
    assert res_seer.get("summary_text") and isinstance(res_seer.get("revealed_cards"), list)
    p3_priv = game.get_private_state_for_player("p3")
    assert p3_priv.get("night_summary") == res_seer["summary_text"]

    game.phase = GamePhase.DAY_PHASE
    assert game.start_voting_phase()
    self_vote = game.submit_vote("p1", "p1")
    assert self_vote["success"] is False, "No debe permitirse el autovoto"
    game.submit_vote("p2", "p1")
    game.submit_vote("p3", "p1")
    game.submit_vote("p1", "p2")  # Cazador apunta al Lobo

    game._finalize_game()
    assert "p1" in game.eliminated_ids, "El Cazador fue el más votado"
    assert "p2" in game.eliminated_ids, "El Lobo debe morir por el disparo del Cazador"
    assert "p2" in game.chain_eliminated_ids
    assert game.winners["team"] == "villagers", "Los aldeanos ganan gracias al disparo del Cazador"
    assert "pudo dar con el lobo" in game.winners["message"].lower()
    reveal = game.get_reveal_data()
    assert len(reveal.get("hunter_shots", [])) == 1
    assert reveal["hunter_shots"][0]["target_id"] == "p2"


if __name__ == '__main__':
    test_reconnection_during_phases()
    test_timer_configuration()
    test_voting_with_disconnected_or_missing_votes()
    test_auto_actions_and_reset_to_lobby()
    test_polymorphic_roles_catalog_and_death_triggers()

