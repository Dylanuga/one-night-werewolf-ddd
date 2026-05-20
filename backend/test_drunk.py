#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test específico para el rol de Borracho (Drunk) y su interacción con otros roles (ej. Ladrón)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from domain.game_logic import GameLogic
from domain.roles import RoleFactory

def test_drunk_flow():
    print("🔧 TEST: Borracho (Drunk) inicial y flujo estándar")
    game = GameLogic("TEST_DRUNK_01")
    
    # Agregar jugadores
    game.add_player("p1", "Dilan", "s1", is_host=True) # Será Robber
    game.add_player("p2", "Player2", "s2")             # Será Drunk
    game.add_player("p3", "Player3", "s3")             # Será Villager
    
    # 3 jugadores, por lo que 6 roles (3 jugadores + 3 centro)
    roles = ['robber', 'drunk', 'villager', 'werewolf', 'werewolf', 'seer']
    game.set_selected_roles(roles)
    
    # Distribución fija
    game.enable_test_mode({
        'players': ['robber', 'drunk', 'villager'],
        'center': ['werewolf', 'werewolf', 'seer']
    })
    
    # Iniciar juego
    success = game.start_game()
    assert success, "El juego debe iniciarse"
    
    # Verificar roles iniciales y orden de turnos
    assert game.players['p1'].original_role == 'robber'
    assert game.players['p2'].original_role == 'drunk'
    
    print(f"🌙 Turnos nocturnos calculados: {game.night_turns}")
    assert 'robber' in game.night_turns
    assert 'drunk' in game.night_turns
    
    # Turno 1: Werewolf (no hay lobos activos, se salta o se avanza)
    # Avancemos los turnos hasta llegar al Robber
    while game.get_current_turn_role() != 'robber':
        game.advance_night_turn()
        
    print(f"🎭 Turno actual: {game.get_current_turn_role()}")
    # Ladrón (p1) roba del borracho (p2)
    action_robber = game.execute_night_action('p1', {'target_player_id': 'p2'})
    assert action_robber['success']
    print(f"   Ladrón ejecutado: {action_robber['message']}")
    
    # Verificar roles intercambiados
    assert game.players['p1'].get_role_name() == 'drunk'
    assert game.players['p2'].get_role_name() == 'robber'
    # Roles originales permanecen intactos
    assert game.players['p1'].original_role == 'robber'
    assert game.players['p2'].original_role == 'drunk'
    
    # Avanzar al turno del Borracho
    while game.get_current_turn_role() != 'drunk':
        game.advance_night_turn()
        
    print(f"🎭 Turno actual: {game.get_current_turn_role()}")
    # Intentar que p1 (quien es actualmente drunk pero original_role == 'robber') actúe
    action_wrong = game.execute_night_action('p1', {'center_position': 2})
    assert not action_wrong['success'], "p1 no debería poder actuar porque su original_role no es drunk"
    
    # Hacer que p2 (original_role == 'drunk') actúe
    # Recuerda: p2 actualmente tiene la carta 'robber' (que le robó p1), pero no lo sabe
    # p2 intercambia su carta ('robber') con la carta del centro 2 ('seer')
    action_correct = game.execute_night_action('p2', {'center_position': 2})
    assert action_correct['success']
    print(f"   Borracho ejecutado: {action_correct['message']}")
    
    # Verificar cartas finales
    # p2 (drunk inicial) debe tener ahora el rol 'seer' (que estaba en centro pos 2)
    assert game.players['p2'].get_role_name() == 'seer'
    # La carta del centro pos 2 debe ser ahora 'robber' (la que p2 tenía antes de actuar)
    assert game.center_cards[2] == 'robber'
    
    print("✅ TEST PASADO CON ÉXITO")

if __name__ == '__main__':
    test_drunk_flow()
