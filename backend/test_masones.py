#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test específico para el rol de Masones
Prueba todas las funcionalidades implementadas para los masones.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from domain.game_logic import GameLogic
from domain.roles import MasonRole

def test_masones_se_reconocen():
    """Test: Dos masones entre jugadores se reconocen"""
    print("🔧 TEST 1: Dos masones se reconocen")
    
    game = GameLogic("TEST01")
    
    # Añadir jugadores
    game.add_player("player1", "Ana", "socket1", is_host=True)
    game.add_player("player2", "Bob", "socket2")
    game.add_player("player3", "Carlos", "socket3")
    game.add_player("player4", "Diana", "socket4")
    
    # Establecer roles - 2 masones, 2 aldeanos, 3 en centro
    roles = ['mason', 'mason', 'villager', 'villager', 'werewolf', 'villager', 'villager']
    game.set_selected_roles(roles)
    
    # Distribución de prueba: masones en player1 y player2
    game.enable_test_mode({
        'players': ['mason', 'mason', 'villager', 'villager'],
        'center': ['werewolf', 'villager', 'villager']
    })
    
    # Iniciar juego
    success = game.start_game()
    assert success, "El juego debería iniciar correctamente"
    
    # Verificar que los masones tienen turno nocturno
    assert 'player1' in game.night_turns, "Player1 (masón) debería tener turno nocturno"
    assert 'player2' in game.night_turns, "Player2 (masón) debería tener turno nocturno"
    
    # Verificar datos de acción nocturna para masón 1
    action_data_1 = game.get_night_action_data_for_player('player1')
    print(f"🔍 Action data player1: {action_data_1}")
    
    assert action_data_1 is not None, "Player1 debería tener datos de acción"
    assert action_data_1['type'] == 'show_other_mason', "Debería mostrar el otro masón"
    assert action_data_1['other_mason_name'] == 'Bob', "Debería mostrar a Bob como el otro masón"
    
    # Verificar datos de acción nocturna para masón 2
    action_data_2 = game.get_night_action_data_for_player('player2')
    print(f"🔍 Action data player2: {action_data_2}")
    
    assert action_data_2 is not None, "Player2 debería tener datos de acción"
    assert action_data_2['type'] == 'show_other_mason', "Debería mostrar el otro masón"
    assert action_data_2['other_mason_name'] == 'Ana', "Debería mostrar a Ana como el otro masón"
    
    print("✅ TEST 1 PASADO: Los masones se reconocen correctamente\n")

def test_mason_solo():
    """Test: Un masón solo (el otro está en el centro)"""
    print("🔧 TEST 2: Masón solo")
    
    game = GameLogic("TEST02")
    
    # Añadir jugadores
    game.add_player("player1", "Ana", "socket1", is_host=True)
    game.add_player("player2", "Bob", "socket2")
    game.add_player("player3", "Carlos", "socket3")
    game.add_player("player4", "Diana", "socket4")
    
    # Establecer roles - 1 masón entre jugadores, 1 en centro
    roles = ['mason', 'mason', 'villager', 'werewolf', 'villager', 'villager', 'villager']
    game.set_selected_roles(roles)
    
    # Distribución de prueba: solo un masón entre jugadores
    game.enable_test_mode({
        'players': ['mason', 'villager', 'villager', 'werewolf'],
        'center': ['mason', 'villager', 'villager']
    })
    
    # Iniciar juego
    success = game.start_game()
    assert success, "El juego debería iniciar correctamente"
    
    # Verificar datos de acción nocturna para el masón solitario
    action_data = game.get_night_action_data_for_player('player1')
    print(f"🔍 Action data mason solo: {action_data}")
    
    assert action_data is not None, "El masón solo debería tener datos de acción"
    assert action_data['type'] == 'alone', "Debería indicar que está solo"
    assert 'Estás solo' in action_data['message'], "El mensaje debería indicar que está solo"
    
    print("✅ TEST 2 PASADO: Masón solo funciona correctamente\n")

def test_masones_en_centro():
    """Test: Ambos masones están en el centro"""
    print("🔧 TEST 3: Masones en centro")
    
    game = GameLogic("TEST03")
    
    # Añadir jugadores
    game.add_player("player1", "Ana", "socket1", is_host=True)
    game.add_player("player2", "Bob", "socket2")
    game.add_player("player3", "Carlos", "socket3")
    game.add_player("player4", "Diana", "socket4")
    
    # Establecer roles - ambos masones en centro
    roles = ['mason', 'mason', 'villager', 'werewolf', 'villager', 'villager', 'villager']
    game.set_selected_roles(roles)
    
    # Distribución de prueba: ambos masones en centro
    game.enable_test_mode({
        'players': ['villager', 'villager', 'villager', 'werewolf'],
        'center': ['mason', 'mason', 'villager']
    })
    
    # Iniciar juego
    success = game.start_game()
    assert success, "El juego debería iniciar correctamente"
    
    # Verificar que hay un turno especial de "mason_wait"
    print(f"🔍 Night turns: {game.night_turns}")
    assert 'mason_wait' in game.night_turns, "Debería haber un turno especial mason_wait"
    
    # Verificar el turn role cuando es el turno de mason_wait
    original_index = game.current_turn_index
    for i, turn in enumerate(game.night_turns):
        if turn == 'mason_wait':
            game.current_turn_index = i
            break
    
    current_role = game.get_current_turn_role()
    print(f"🔍 Current role durante mason_wait: {current_role}")
    assert current_role == 'mason', "El rol actual debería ser 'mason' durante mason_wait"
    
    # Restaurar índice original
    game.current_turn_index = original_index
    
    print("✅ TEST 3 PASADO: Masones en centro funcionan correctamente\n")

def test_mason_role_class():
    """Test: Verificar la clase MasonRole directamente"""
    print("🔧 TEST 4: Clase MasonRole")
    
    mason_role = MasonRole()
    
    # Verificar turn order
    assert mason_role.turn_order == 2, "Los masones deberían tener turn_order 2"
    
    # Test con estado de juego simulado
    game_state = {
        'players': {
            'player1': {'name': 'Ana', 'role': 'mason'},
            'player2': {'name': 'Bob', 'role': 'mason'},
            'player3': {'name': 'Carlos', 'role': 'villager'}
        },
        'center_cards': ['werewolf', 'villager', 'villager']
    }
    
    # Test reconocimiento mutuo
    action_data = mason_role.get_night_action_data('player1', game_state)
    assert action_data['type'] == 'show_other_mason'
    assert action_data['other_mason_name'] == 'Bob'
    
    # Test ejecutar acción
    result = mason_role.execute_action('player1', {}, game_state)
    assert result['success'] == True
    
    print("✅ TEST 4 PASADO: Clase MasonRole funciona correctamente\n")

def run_all_tests():
    """Ejecuta todos los tests de masones"""
    print("🔨 INICIANDO TESTS DE MASONES")
    print("=" * 50)
    
    try:
        test_masones_se_reconocen()
        test_mason_solo()
        test_masones_en_centro()
        test_mason_role_class()
        
        print("🎉 TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ ERROR EN LOS TESTS: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    run_all_tests()
