#!/usr/bin/env python3
"""
Script de prueba para el nuevo endpoint de testing /test/create-test-room
"""

import time
import requests
import json

def test_endpoint_basic():
    """Prueba básica del endpoint de testing"""
    
    print(f"🧪 === PRUEBA BÁSICA DEL ENDPOINT ===")
    
    # Configuración simple
    test_config = {
        "role_distribution": {
            "players": ["werewolf", "mason", "mason", "villager"],
            "center": ["villager", "seer", "robber"]
        },
        "auto_start": True,
        "player_names": ["Alice", "Bob", "Charlie", "Diana"]
    }
    
    try:
        # 1. Limpiar sala anterior si existe
        print(f"🧹 Limpiando sala TEST anterior...")
        response = requests.post('http://localhost:5000/test/reset')
        print(f"   Reset: {response.status_code}")
        
        # 2. Crear sala de prueba
        print(f"🏗️ Creando sala TEST...")
        response = requests.post('http://localhost:5000/test/create-test-room', json=test_config)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Sala creada exitosamente:")
            print(f"   - Código: {result['room_code']}")
            print(f"   - Jugadores: {len(result['players'])}")
            print(f"   - Juego iniciado: {result['game_started']}")
            print(f"   - Jugadores:")
            for player in result['players']:
                print(f"     * {player['name']} (ID: {player['id']})")
        else:
            print(f"❌ Error creando sala: {response.status_code}")
            print(f"   Response: {response.text}")
            return
        
        # 3. Verificar estado
        print(f"\n📊 Verificando estado...")
        response = requests.get('http://localhost:5000/test/status')
        
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Estado obtenido:")
            print(f"   - Existe: {status['exists']}")
            print(f"   - Fase: {status['phase']}")
            print(f"   - Turno actual: {status['current_turn_role']}")
            print(f"   - Modo prueba: {status['test_mode']}")
            print(f"   - Jugadores conectados: {status['players_count']}")
            
            # Mostrar roles asignados
            print(f"   - Roles asignados:")
            for player in status['players']:
                print(f"     * {player['name']}: {player['role']} {'(HOST)' if player['is_host'] else ''}")
                
        else:
            print(f"❌ Error obteniendo estado: {response.status_code}")
        
        # 4. Observar progresión automática si está en modo noche
        if status.get('phase') == 'night_phase':
            print(f"\n🌙 Observando progresión automática de turnos...")
            
            for i in range(15):
                time.sleep(1)
                response = requests.get('http://localhost:5000/test/status')
                
                if response.status_code == 200:
                    current_status = response.json()
                    phase = current_status.get('phase', 'unknown')
                    turn_role = current_status.get('current_turn_role', 'none')
                    
                    print(f"   [{i+1:2d}s] Fase: {phase:15s} | Turno: {turn_role}")
                    
                    if phase == 'day_phase':
                        print(f"✅ Progresión automática completada - llegó a fase de día")
                        break
                else:
                    print(f"   [{i+1:2d}s] Error obteniendo estado")
            
        print(f"\n✅ Prueba básica completada")
        
    except Exception as e:
        print(f"❌ Error en prueba: {e}")

def test_presets():
    """Prueba las configuraciones predefinidas"""
    
    print(f"\n🧪 === PRUEBA DE PRESETS ===")
    
    try:
        # Obtener presets disponibles
        response = requests.get('http://localhost:5000/test/presets')
        
        if response.status_code == 200:
            data = response.json()
            presets = data['presets']
            
            print(f"📋 Presets disponibles:")
            for preset_id, preset_data in presets.items():
                print(f"   - {preset_id}: {preset_data['name']}")
                print(f"     {preset_data['description']}")
            
            # Probar un preset específico
            print(f"\n🧪 Probando preset 'seer_game'...")
            
            # Limpiar
            requests.post('http://localhost:5000/test/reset')
            
            # Crear con preset
            test_config = {
                "role_distribution": presets['seer_game']['role_distribution'],
                "auto_start": True
            }
            
            response = requests.post('http://localhost:5000/test/create-test-room', json=test_config)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Preset aplicado exitosamente:")
                print(f"   - Jugadores: {len(result['players'])}")
                print(f"   - Distribución: {result['role_distribution']}")
            else:
                print(f"❌ Error aplicando preset: {response.status_code}")
                
        else:
            print(f"❌ Error obteniendo presets: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error en prueba de presets: {e}")

def test_error_cases():
    """Prueba casos de error del endpoint"""
    
    print(f"\n🧪 === PRUEBA DE CASOS DE ERROR ===")
    
    error_cases = [
        {
            'name': 'Sin role_distribution',
            'config': {"auto_start": True},
            'expected_error': 'Se requiere role_distribution'
        },
        {
            'name': 'Roles inválidos',
            'config': {
                "role_distribution": {
                    "players": ["invalid_role", "villager"],
                    "center": ["villager", "villager", "villager"]
                }
            },
            'expected_error': 'Roles inválidos'
        },
        {
            'name': 'Muy pocos jugadores',
            'config': {
                "role_distribution": {
                    "players": ["werewolf", "villager"],  # Solo 2 jugadores
                    "center": ["villager", "villager", "villager"]
                }
            },
            'expected_error': 'Se requieren entre 3 y 10 jugadores'
        },
        {
            'name': 'Centro incorrecto',
            'config': {
                "role_distribution": {
                    "players": ["werewolf", "villager", "villager", "villager"],
                    "center": ["villager", "villager"]  # Solo 2 en centro
                }
            },
            'expected_error': 'center debe tener exactamente 3 roles'
        }
    ]
    
    for case in error_cases:
        print(f"\n🧪 Probando: {case['name']}")
        
        try:
            # Limpiar
            requests.post('http://localhost:5000/test/reset')
            
            # Probar caso de error
            response = requests.post('http://localhost:5000/test/create-test-room', json=case['config'])
            
            if response.status_code == 400:
                error_msg = response.json().get('error', '')
                if case['expected_error'] in error_msg:
                    print(f"   ✅ Error detectado correctamente: {error_msg}")
                else:
                    print(f"   ⚠️ Error detectado pero mensaje inesperado: {error_msg}")
            else:
                print(f"   ❌ Debería haber dado error 400, pero dio: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error en prueba: {e}")

def main():
    """Ejecuta todas las pruebas"""
    print(f"🧪 INICIANDO SUITE DE PRUEBAS DEL ENDPOINT DE TESTING")
    print(f"=" * 60)
    
    try:
        # Verificar que el servidor esté corriendo
        response = requests.get('http://localhost:5000/debug/rooms', timeout=5)
        print(f"🔌 Servidor conectado: {response.status_code}")
        
    except requests.exceptions.ConnectionError:
        print(f"❌ ERROR: No se puede conectar al servidor en localhost:5000")
        print(f"   Asegúrate de que el servidor esté corriendo con: python run.py")
        return
    except Exception as e:
        print(f"❌ ERROR de conexión: {e}")
        return
    
    # Ejecutar pruebas
    test_endpoint_basic()
    test_presets()
    test_error_cases()
    
    # Limpiar al final
    print(f"\n🧹 Limpieza final...")
    requests.post('http://localhost:5000/test/reset')
    
    print(f"\n🎉 SUITE DE PRUEBAS COMPLETADA")

if __name__ == '__main__':
    main()
