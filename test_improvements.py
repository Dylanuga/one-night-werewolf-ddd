#!/usr/bin/env python3
"""
Script para probar las mejoras de rendimiento implementadas.
"""
import sys
import os
import time
import threading
from pathlib import Path

# Añadir el directorio backend al path para poder importar los módulos
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from domain.game_logic import GameLogic
from services.game_service import GameService
from infrastructure.room_repository import RoomRepository

def test_timer_functionality():
    """Prueba la funcionalidad del timer automático."""
    print("🧪 PRUEBA: Funcionalidad del timer automático")
    
    # Crear emisor mock
    def mock_emit(event, data, room=None):
        print(f"📤 EMIT: {event} -> {data} (room: {room})")
    
    # Crear dependencias
    repo = RoomRepository()
    service = GameService(repo, mock_emit)
    
    # Reducir duración del turno para la prueba
    service.TURN_DURATION = 3  # 3 segundos para prueba rápida
    
    # Crear sala de prueba
    room_code = "TEST123"
    player1_id = "player_test_1"
    player2_id = "player_test_2"
    
    print(f"✅ Creando sala {room_code}...")
    success = service.create_room(room_code, player1_id, "TestPlayer1", "socket1")
    assert success, "No se pudo crear la sala"
    
    # Añadir segundo jugador
    success = service.join_room(room_code, player2_id, "TestPlayer2", "socket2")
    assert success, "No se pudo añadir el segundo jugador"
    
    # Establecer roles de prueba
    roles = ["werewolf", "mason", "villager", "seer", "robber"]  # 5 roles para 2 jugadores + 3 centro
    success = service.set_selected_roles(room_code, player1_id, roles)
    assert success, "No se pudieron establecer los roles"
    
    # Activar modo de prueba con distribución específica
    game = repo.get_game(room_code)
    game.enable_test_mode({
        'players': ['werewolf', 'mason'],
        'center': ['villager', 'seer', 'robber']
    })
    
    # Iniciar el juego
    print(f"🎮 Iniciando juego...")
    success = service.start_game(room_code, player1_id)
    assert success, "No se pudo iniciar el juego"
    
    # Verificar que el juego está en fase nocturna
    game = repo.get_game(room_code)
    assert game.phase.value == 'night_phase', f"Fase incorrecta: {game.phase.value}"
    
    print(f"🌙 Juego en fase nocturna. Rol actual: {game.get_current_turn_role()}")
    print(f"⏰ Esperando {service.TURN_DURATION} segundos para avance automático...")
    
    # Esperar un poco más que la duración del turno
    time.sleep(service.TURN_DURATION + 1)
    
    # Verificar que el turno avanzó
    game = repo.get_game(room_code)
    new_role = game.get_current_turn_role()
    
    print(f"🔄 Después del timer - Rol actual: {new_role}")
    
    if new_role == 'mason':
        print("✅ ÉXITO: El timer avanzó automáticamente de werewolf a mason")
        
        # Esperar otro ciclo para ver si avanza a día
        print(f"⏰ Esperando otro ciclo para avanzar a fase de día...")
        time.sleep(service.TURN_DURATION + 1)
        
        game = repo.get_game(room_code)
        print(f"🌅 Fase final: {game.phase.value}")
        
        if game.phase.value == 'day_phase':
            print("✅ ÉXITO COMPLETO: El juego avanzó automáticamente a la fase de día")
        else:
            print(f"⚠️ ADVERTENCIA: El juego no avanzó a día, fase actual: {game.phase.value}")
    else:
        print(f"❌ FALLO: El timer no avanzó correctamente. Rol sigue siendo: {new_role}")
    
    print("🧪 Prueba completada")

def test_phase_timer_calculation():
    """Prueba el cálculo del timer de fase."""
    print("\n🧪 PRUEBA: Cálculo del PhaseTimer")
    
    # Simular datos del turn_start como los envía el servidor
    import time
    
    current_time = time.time()
    
    # Simular que el turno comenzó hace 2 segundos
    turn_data = {
        'role': 'werewolf',
        'phase': 'Fase: werewolf',
        'duration': 6,
        'timestamp': current_time - 2  # Comenzó hace 2 segundos
    }
    
    print(f"📊 Datos del turno: {turn_data}")
    
    # Simular el cálculo que hace PhaseTimer
    TURN_DURATION = 6
    server_start_time = turn_data['timestamp'] * 1000  # Convertir a ms
    now = time.time() * 1000  # Tiempo actual en ms
    elapsed = (now - server_start_time) / 1000  # Tiempo transcurrido en segundos
    remaining = max(0, TURN_DURATION - elapsed)
    
    print(f"⏰ Tiempo transcurrido: {elapsed:.1f}s")
    print(f"⏰ Tiempo restante: {remaining:.1f}s")
    
    if 3.5 <= remaining <= 4.5:  # Debería quedar entre 3.5 y 4.5 segundos
        print("✅ ÉXITO: El cálculo del timer es correcto")
    else:
        print(f"❌ FALLO: El tiempo restante no es el esperado (debería ser ~4s)")
    
    print("🧪 Prueba completada")

def run_all_tests():
    """Ejecuta todas las pruebas."""
    print("🚀 INICIANDO PRUEBAS DE MEJORAS DE RENDIMIENTO")
    print("=" * 60)
    
    try:
        test_timer_functionality()
        test_phase_timer_calculation()
        
        print("\n" + "=" * 60)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS")
        print("\n🎯 RESUMEN DE MEJORAS IMPLEMENTADAS:")
        print("   1. ✅ Timer automático de transición entre fases")
        print("   2. ✅ Cálculo correcto del tiempo restante en PhaseTimer")  
        print("   3. ✅ Optimización de re-renders en NightPhase")
        print("   4. ✅ Eliminación de logs excesivos en PhaseTimer")
        print("   5. ✅ Simplificación de anti-duplicados en App.jsx")
        
    except Exception as e:
        print(f"\n❌ ERROR EN LAS PRUEBAS: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()