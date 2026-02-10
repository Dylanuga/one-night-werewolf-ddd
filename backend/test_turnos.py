#!/usr/bin/env python3
"""
Script de prueba para verificar que el sistema de turnos automáticos funciona correctamente
"""

import time
import requests
import json

def create_test_room(role_distribution):
    """Crea una sala de prueba usando el nuevo endpoint REST"""
    try:
        # Limpiar sala anterior si existe
        requests.post('http://localhost:5000/test/reset')
        
        # Crear nueva sala TEST con auto-start
        test_config = {
            "role_distribution": role_distribution,
            "auto_start": True
        }
        
        response = requests.post('http://localhost:5000/test/create-test-room', json=test_config)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Sala TEST creada via REST endpoint")
            print(f"   - Jugadores: {len(result['players'])}")
            print(f"   - Juego iniciado: {result['game_started']}")
            return 'TEST'
        else:
            print(f"❌ Error creando sala: {response.status_code} - {response.text}")
            return None
        
    except Exception as e:
        print(f"❌ Error creando sala via REST: {e}")
        return None

def test_auto_turn_advancement():
    """Prueba que los turnos avanzan automáticamente después de 6 segundos"""
    
    # Configuración de prueba: 1 lobo, 2 masones, 3 aldeanos + 3 centro
    role_distribution = {
        'players': ['werewolf', 'mason', 'mason', 'villager', 'villager', 'villager'],
        'center': ['villager', 'villager', 'villager']
    }
    
    print(f"🧪 INICIANDO PRUEBA DE TURNOS AUTOMÁTICOS")
    print(f"   Distribución: {role_distribution}")
    
    try:
        # 0. Crear sala usando el nuevo endpoint REST
        room_code = create_test_room(role_distribution)
        if not room_code:
            print("❌ No se pudo crear la sala")
            return
        
        print(f"   Sala: {room_code}")
        
        # 1. Verificar estado inicial de la sala
        response = requests.get(f'http://localhost:5000/test/status')
        if response.status_code == 200:
            status = response.json()
            print(f"📊 Estado inicial de la sala:")
            print(f"   Fase: {status.get('phase', 'unknown')}")
            print(f"   Jugadores: {status.get('players_count', 0)}")
            print(f"   Turno actual: {status.get('current_turn_role', 'none')}")
            print(f"   Modo prueba: {status.get('test_mode', False)}")
            
            # Mostrar roles asignados
            print(f"   Roles asignados:")
            for player in status.get('players', []):
                print(f"     * {player['name']}: {player['role']}")
            
            # Si está en fase nocturna, observar la progresión
            if status.get('phase') == 'night_phase':
                print(f"\n🌙 JUEGO EN FASE NOCTURNA - OBSERVANDO TURNOS AUTOMÁTICOS")
                
                # Observar durante 20 segundos para ver si los turnos avanzan
                for i in range(20):
                    time.sleep(1)
                    
                    # Verificar estado actual
                    response = requests.get(f'http://localhost:5000/test/status')
                    if response.status_code == 200:
                        current_status = response.json()
                        current_role = current_status.get('current_turn_role', 'none')
                        phase = current_status.get('phase', 'unknown')
                        
                        print(f"   [{i+1:2d}s] Fase: {phase:15s} | Turno: {current_role}")
                        
                        # Si cambió a fase de día, la prueba fue exitosa
                        if phase == 'day_phase':
                            print(f"\n✅ ÉXITO: Los turnos avanzaron automáticamente a la fase de día")
                            print(f"   Tiempo total: {i+1} segundos")
                            return
                    else:
                        print(f"   [{i+1:2d}s] Error obteniendo estado")
                
                print(f"\n⚠️  ADVERTENCIA: No se observó avance automático a fase de día en 20s")
            
            else:
                print(f"ℹ️  Sala no está en fase nocturna, estado actual: {status.get('phase')}")
                
        else:
            print(f"❌ Error obteniendo estado de la sala: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
    
    finally:
        # Limpiar: resetear sala de prueba
        try:
            response = requests.post(f'http://localhost:5000/test/reset')
            if response.status_code == 200:
                print(f"\n🧹 Sala TEST reseteada")
            else:
                print(f"\n⚠️  Error reseteando sala: {response.status_code}")
        except Exception as e:
            print(f"\n⚠️  Error en limpieza: {e}")

if __name__ == '__main__':
    test_auto_turn_advancement()
