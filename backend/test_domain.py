# backend/test_domain.py
import sys
import os

# Añadir el directorio backend al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from domain.game_logic import GameLogic, GamePhase
from domain.roles import WerewolfRole

def test_basic_game_logic():
    """Test básico de la lógica del dominio"""
    print("🧪 Probando lógica del dominio...")
    
    # Crear juego
    game = GameLogic("TEST")
    assert game.room_code == "TEST"
    assert game.phase == GamePhase.LOBBY
    print("✅ GameLogic creado correctamente")
    
    # Añadir jugadores
    success = game.add_player("player1", "Dylan", "socket1", is_host=True)
    assert success == True
    assert len(game.players) == 1
    print("✅ Jugador añadido correctamente")
    
    # Añadir más jugadores
    game.add_player("player2", "Javi", "socket2")
    game.add_player("player3", "Moi", "socket3")
    assert len(game.players) == 3
    print("✅ Múltiples jugadores añadidos")
    
    # Configurar roles (3 jugadores + 3 centro = 6 roles)
    roles = ["werewolf", "werewolf", "villager", "villager", "seer", "robber"]
    success = game.set_selected_roles(roles)
    assert success == True
    assert game.phase == GamePhase.ROLE_SELECTION
    print("✅ Roles configurados correctamente")
    
    # Iniciar juego
    success = game.start_game()
    assert success == True
    assert game.phase == GamePhase.NIGHT_PHASE
    assert len(game.center_cards) == 3
    print("✅ Juego iniciado, roles distribuidos")
    
    # Verificar distribución de roles
    player_roles = [p.get_role_name() for p in game.players.values()]
    print(f"🎭 Roles de jugadores: {player_roles}")
    print(f"🃏 Cartas del centro: {game.center_cards}")
    
    # Verificar turnos nocturnos
    print(f"🌙 Turnos nocturnos: {game.night_turns}")
    print(f"🎯 Turno actual: {game.get_current_turn_player()}")
    print(f"🎭 Rol del turno: {game.get_current_turn_role()}")
    
    print("🎉 ¡Todas las pruebas pasaron!")

def test_werewolf_role():
    """Test específico del rol de lobo"""
    print("\n🐺 Probando rol de Werewolf...")
    
    werewolf = WerewolfRole()
    assert werewolf.role_type.value == "werewolf"
    assert werewolf.turn_order == 1
    print("✅ WerewolfRole creado correctamente")
    
    # Simular estado del juego con 2 lobos
    game_state = {
        'players': {
            'p1': {'name': 'Dylan', 'role': 'werewolf'},
            'p2': {'name': 'Javi', 'role': 'werewolf'},
            'p3': {'name': 'Moi', 'role': 'villager'}
        },
        'center_cards': ['villager', 'seer', 'robber']
    }
    
    # Test caso A: 2 lobos entre jugadores
    action_data = werewolf.get_night_action_data('p1', game_state)
    assert action_data['type'] == 'show_other_werewolf'
    assert 'Javi' in action_data['other_werewolf_name']
    print("✅ Caso A (2 lobos): Funciona correctamente")
    
    # Test caso B: 1 lobo entre jugadores
    game_state['players']['p2']['role'] = 'villager'
    game_state['center_cards'][0] = 'werewolf'
    
    action_data = werewolf.get_night_action_data('p1', game_state)
    assert action_data['type'] == 'can_view_center'
    assert action_data['center_positions'] == [0, 1, 2]
    print("✅ Caso B (1 lobo): Funciona correctamente")
    
    print("🎉 ¡Tests del Werewolf pasaron!")

if __name__ == '__main__':
    print("🚀 Iniciando tests del dominio...\n")
    test_basic_game_logic()
    test_werewolf_role()
    print("\n✅ ¡Todos los tests del backend pasaron!")
    print("🧠 El dominio está sólido y listo!")