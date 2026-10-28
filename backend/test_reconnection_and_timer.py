# backend/test_reconnection_and_timer.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from domain.game_logic import GameLogic, GamePhase
from infrastructure.room_repository import RoomRepository
from services.game_service import GameService

def test_reconnection_during_phases():
    print("🧪 TEST 1: Reconexión durante diferentes fases del juego...")
    game = GameLogic("RECON")
    assert game.add_player("p1", "HostPlayer", "socket_1", is_host=True)
    assert game.add_player("p2", "PlayerTwo", "socket_2")
    assert game.add_player("p3", "PlayerThree", "socket_3")

    # Iniciar juego con roles
    roles = ['werewolf', 'villager', 'seer', 'robber', 'villager', 'villager']
    assert game.set_selected_roles(roles)
    assert game.start_game()
    assert game.phase == GamePhase.NIGHT_PHASE

    # Simular que PlayerTwo se desconecta durante la noche (ej. llamada de la casera)
    game.players["p2"].disconnect()
    assert not game.players["p2"].is_connected

    # PlayerTwo vuelve con un NUEVO socket_id
    success = game.add_player("p2", "PlayerTwo", "socket_2_new")
    assert success, "La reconexión durante la noche debe permitirse"
    assert game.players["p2"].is_connected
    assert game.players["p2"].socket_id == "socket_2_new"
    print("   ✅ Reconexión en NIGHT_PHASE permitida")

    # Avanzar a DAY_PHASE
    game.phase = GamePhase.DAY_PHASE
    game.players["p3"].disconnect()
    success = game.add_player("p3", "PlayerThree", "socket_3_new")
    assert success, "La reconexión durante el día debe permitirse"
    assert game.players["p3"].socket_id == "socket_3_new"
    print("   ✅ Reconexión en DAY_PHASE permitida")

    # Avanzar a VOTING
    assert game.start_voting_phase()
    assert game.phase == GamePhase.VOTING
    game.players["p1"].disconnect()
    success = game.add_player("p1", "HostPlayer", "socket_1_new")
    assert success, "La reconexión durante votación debe permitirse"
    assert game.players["p1"].socket_id == "socket_1_new"
    print("   ✅ Reconexión en VOTING permitida")

def test_timer_configuration():
    print("\n🧪 TEST 2: Configuración de temporizadores de debate...")
    game = GameLogic("TIMER")
    assert game.discussion_duration == 300, "Duración por defecto debe ser 300s (5 min)"

    assert game.set_discussion_duration(120)
    assert game.discussion_duration == 120, "Debe aceptar 120s (2 min)"

    assert game.set_discussion_duration(600)
    assert game.discussion_duration == 600, "Debe aceptar 600s (10 min)"

    # Valor inválido debe ser rechazado
    assert not game.set_discussion_duration(999)
    assert game.discussion_duration == 600, "Valor inválido debe mantener el anterior"
    print("   ✅ Opciones de 2, 5 y 10 minutos validadas correctamente")

def test_voting_with_disconnected_or_missing_votes():
    print("\n🧪 TEST 3: Votación con jugadores caídos o votos parciales...")
    game = GameLogic("VOTE")
    game.add_player("p1", "Host", "s1", is_host=True)
    game.add_player("p2", "Player2", "s2")
    game.add_player("p3", "Player3", "s3")

    game.phase = GamePhase.DAY_PHASE
    assert game.start_voting_phase()

    # Solo p1 vota
    res = game.submit_vote("p1", "p2")
    assert res['success']
    assert not res['all_voted']
    assert not res['all_connected_voted']

    # Strict can_finalize debe ser False porque faltan votos
    assert not game.can_finalize(allow_partial=False)

    # Con allow_partial=True (ej. timer a 0 o forzado por host), se debe poder finalizar
    assert game.can_finalize(allow_partial=True)

    # Desconectar p3 (se le apagó el móvil)
    game.players["p3"].disconnect()
    # Ahora p2 vota
    res2 = game.submit_vote("p2", "p1")
    assert res2['success']
    assert not res2['all_voted'], "p3 no ha votado aún"
    assert res2['all_connected_voted'], "Todos los conectados (p1 y p2) ya votaron"

    # can_finalize() normal debe ser True porque todos los conectados votaron
    assert game.can_finalize(allow_partial=False)

    # Finalizar juego
    game._finalize_game()
    assert game.eliminated_ids in (["p1", "p2"], ["p2", "p1"])
    print("   ✅ Votación con desconectados y parciales funciona perfectamente")

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

    # Turno 0: Lobo solitario no hace nada -> auto acción
    assert game.get_current_turn_role() == "werewolf"
    ww_auto = game.execute_werewolf_auto_action()
    assert ww_auto and ww_auto.get("success") and ww_auto.get("auto") is True
    assert ww_auto.get("werewolf_player_id") == "p2"
    assert ww_auto.get("center_position") in (0, 1, 2)
    assert ww_auto.get("center_role") in ("robber", "troublemaker", "drunk")
    p2_priv = game.get_private_state_for_player("p2")
    assert p2_priv.get("werewolf_last_center") is not None
    print("   ✅ Acción aleatoria de Lobo Solitario ejecutada y visible en estado privado")

    # Turno 1: Vidente no hace nada -> auto acción
    game.advance_night_turn()
    assert game.get_current_turn_role() == "seer"
    seer_auto = game.execute_seer_auto_action()
    assert seer_auto and seer_auto.get("success") and seer_auto.get("auto") is True
    assert seer_auto.get("seer_player_id") == "p1"
    assert "seen_player" in seer_auto or "seen_center" in seer_auto
    p1_priv = game.get_private_state_for_player("p1")
    assert p1_priv.get("seer_last_result") is not None
    print("   ✅ Acción aleatoria de Vidente ejecutada y visible en estado privado")

    # Probar reset_game desde GAME_END a ROLE_SELECTION y luego a LOBBY (botón Volver al Lobby)
    game.phase = GamePhase.GAME_END
    assert game.reset_game("role_selection")
    assert game.phase == GamePhase.ROLE_SELECTION
    assert game.reset_game("lobby")
    assert game.phase == GamePhase.LOBBY
    assert game.selected_roles == []
    print("   ✅ Reset de ROLE_SELECTION a LOBBY ('Volver al Lobby') funciona correctamente")


def test_polymorphic_roles_catalog_and_death_triggers():
    print("\n🧪 TEST 5: Catálogo centralizado, contrato unificado y disparo del Cazador (Hunter)...")
    from domain.roles import RoleFactory, ROLE_METADATA

    catalog = RoleFactory.get_catalog()
    assert "werewolf" in catalog and "seer" in catalog and "hunter" in catalog and "tanner" in catalog
    assert catalog["seer"]["interaction_type"] == "select_player_or_center"
    print("   ✅ Catálogo centralizado de roles validado")

    # Probar polimorfismo execute_current_turn_auto_action y night_summary unificado
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

    # Turno 0: werewolf (lobo solitario) via execute_current_turn_auto_action()
    assert game.get_current_turn_role() == "werewolf"
    res_ww = game.execute_current_turn_auto_action()
    assert res_ww["success"] and res_ww["auto"] is True
    assert res_ww.get("summary_text") and isinstance(res_ww.get("revealed_cards"), list)
    p2_priv = game.get_private_state_for_player("p2")
    assert p2_priv.get("night_summary") == res_ww["summary_text"]

    # Turno 1: seer via execute_current_turn_auto_action()
    game.advance_night_turn()
    assert game.get_current_turn_role() == "seer"
    res_seer = game.execute_current_turn_auto_action()
    assert res_seer["success"] and res_seer["auto"] is True
    assert res_seer.get("summary_text") and isinstance(res_seer.get("revealed_cards"), list)
    p3_priv = game.get_private_state_for_player("p3")
    assert p3_priv.get("night_summary") == res_seer["summary_text"]
    print("   ✅ Contrato unificado (night_summary + revealed_cards) validado")

    # Fase de votación: p2 y p3 votan al Cazador (p1), pero el Cazador (p1) vota al Lobo (p2)
    game.phase = GamePhase.DAY_PHASE
    assert game.start_voting_phase()
    game.submit_vote("p2", "p1")
    game.submit_vote("p3", "p1")
    game.submit_vote("p1", "p2")  # Cazador apunta al Lobo

    game._finalize_game()
    assert "p1" in game.eliminated_ids, "El Cazador fue el más votado"
    assert "p2" in game.eliminated_ids, "El Lobo debe morir por el disparo del Cazador"
    assert "p2" in game.chain_eliminated_ids
    assert game.winners["team"] == "villagers", "Los aldeanos ganan gracias al disparo del Cazador"
    print("   ✅ Motor de resolución con efectos al morir (Cazador) funciona perfectamente")


if __name__ == '__main__':
    test_reconnection_during_phases()
    test_timer_configuration()
    test_voting_with_disconnected_or_missing_votes()
    test_auto_actions_and_reset_to_lobby()
    test_polymorphic_roles_catalog_and_death_triggers()
    print("\n🎉 TODOS LOS TESTS DE RECONEXIÓN Y TEMPORIZADOR PASARON CON ÉXITO")
