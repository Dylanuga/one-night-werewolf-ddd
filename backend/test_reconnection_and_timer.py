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

if __name__ == '__main__':
    test_reconnection_during_phases()
    test_timer_configuration()
    test_voting_with_disconnected_or_missing_votes()
    print("\n🎉 TODOS LOS TESTS DE RECONEXIÓN Y TEMPORIZADOR PASARON CON ÉXITO")
