#!/usr/bin/env python3
"""
Pruebas de integración para endpoints REST de testing y flujo completo vía Socket.IO test_client.
"""


def test_endpoint_basic(client, socketio_app):
    """Prueba básica del endpoint de testing /test/create-test-room usando test_client."""
    test_config = {
        "role_distribution": {
            "players": ["werewolf", "mason", "mason", "villager"],
            "center": ["villager", "seer", "robber"]
        },
        "auto_start": True,
        "turn_duration": 1,
        "player_names": ["Alice", "Bob", "Charlie", "Diana"]
    }

    # 1. Limpiar sala anterior si existe
    reset_resp = client.post('/test/reset')
    assert reset_resp.status_code == 200

    # 2. Crear sala de prueba
    create_resp = client.post('/test/create-test-room', json=test_config)
    assert create_resp.status_code == 200
    result = create_resp.get_json()
    assert result['room_code'] == 'TEST'
    assert len(result['players']) == 4
    assert result['game_started'] is True

    # 3. Verificar estado
    status_resp = client.get('/test/status')
    assert status_resp.status_code == 200
    status = status_resp.get_json()
    assert status['exists'] is True
    assert status['phase'] == 'night_phase'
    assert status['test_mode'] is True
    assert status['players_count'] == 4
    assert status['current_turn_role'] == 'werewolf'

    # 4. Avanzar turnos manualmente hasta completar la noche
    seen_turns = [status['current_turn_role']]
    for _ in range(5):
        adv_resp = client.post('/test/advance-turn')
        assert adv_resp.status_code == 200
        adv_data = adv_resp.get_json()
        if adv_data.get('current_turn_role'):
            seen_turns.append(adv_data['current_turn_role'])
        status_now = client.get('/test/status').get_json()
        if status_now['game_state'].get('current_turn_role') == 'open_eyes':
            break

    assert 'mason' in seen_turns
    assert 'seer' in seen_turns
    assert 'robber' in seen_turns

    # Verificar que la transición open_eyes llega a day_phase
    for _ in range(70):
        socketio_app.sleep(0.1)
        if client.get('/test/status').get_json()['phase'] == 'day_phase':
            break
    assert client.get('/test/status').get_json()['phase'] == 'day_phase'


def test_presets(client):
    """Prueba las configuraciones predefinidas."""
    response = client.get('/test/presets')
    assert response.status_code == 200
    presets = response.get_json()['presets']
    assert 'seer_game' in presets
    assert 'hunter_vs_wolf' in presets

    assert client.post('/test/reset').status_code == 200

    test_config = {
        "role_distribution": presets['seer_game']['role_distribution'],
        "auto_start": True
    }
    create_resp = client.post('/test/create-test-room', json=test_config)
    assert create_resp.status_code == 200
    result = create_resp.get_json()
    assert len(result['players']) == 4
    assert result['role_distribution'] == presets['seer_game']['role_distribution']


def test_error_cases(client):
    """Prueba casos de error del endpoint /test/create-test-room."""
    error_cases = [
        {
            'config': {"auto_start": True},
            'expected_error': 'Se requiere role_distribution'
        },
        {
            'config': {
                "role_distribution": {
                    "players": ["invalid_role", "villager", "villager"],
                    "center": ["villager", "villager", "villager"]
                }
            },
            'expected_error': 'Roles inválidos'
        },
        {
            'config': {
                "role_distribution": {
                    "players": ["werewolf", "villager"],
                    "center": ["villager", "villager", "villager"]
                }
            },
            'expected_error': 'Se requieren entre 3 y 10 jugadores'
        },
        {
            'config': {
                "role_distribution": {
                    "players": ["werewolf", "villager", "villager", "villager"],
                    "center": ["villager", "villager"]
                }
            },
            'expected_error': 'center debe tener exactamente 3 roles'
        }
    ]

    for case in error_cases:
        assert client.post('/test/reset').status_code == 200
        response = client.post('/test/create-test-room', json=case['config'])
        assert response.status_code == 400
        error_msg = response.get_json().get('error', '')
        assert case['expected_error'] in error_msg


def test_socketio_full_game_events(app_instance, socketio_app):
    """Prueba el contrato de eventos Socket.IO usando socketio.test_client."""
    from main.app import game_service, room_repository

    host = socketio_app.test_client(app_instance)
    p2 = socketio_app.test_client(app_instance)
    p3 = socketio_app.test_client(app_instance)

    try:
        assert host.is_connected()
        assert p2.is_connected()
        assert p3.is_connected()

        # Limpiar evento inicial 'connected'
        host.get_received()
        p2.get_received()
        p3.get_received()

        # 1. Host crea sala
        host.emit('create_room', {'name': 'Alice'})
        host_events = {ev['name']: ev['args'][0] for ev in host.get_received()}
        assert 'room_created' in host_events
        room_code = host_events['room_created']['room_code']

        # 2. Jugadores se unen
        p2.emit('join_room', {'room_code': room_code, 'name': 'Bob'})
        p3.emit('join_room', {'room_code': room_code, 'name': 'Charlie'})
        assert any(ev['name'] == 'room_joined' for ev in p2.get_received())
        assert any(ev['name'] == 'room_joined' for ev in p3.get_received())

        # 3. Host configura roles y modo determinista para test
        roles = ['werewolf', 'seer', 'villager', 'mason', 'mason', 'robber']
        host.emit('set_roles', {'roles': roles, 'discussion_duration': 120})
        assert any(ev['name'] == 'roles_set' for ev in host.get_received())

        game = room_repository.get_game(room_code)
        game.enable_test_mode({
            'players': ['werewolf', 'seer', 'villager'],
            'center': ['mason', 'mason', 'robber']
        })
        game_service.set_turn_duration(room_code, 5)

        # 4. Iniciar partida
        host.emit('start_game')
        host_start_events = host.get_received()
        assert any(ev['name'] == 'game_started' for ev in host_start_events)
        assert any(ev['name'] == 'turn_start' and ev['args'][0]['role'] == 'werewolf' for ev in host_start_events)

        # 5. Lobo solitario ve carta del centro 0
        host.emit('night_action', {'action': {'center_position': 0}})
        action_events = host.get_received()
        assert any(ev['name'] == 'action_result' and ev['args'][0]['success'] for ev in action_events)

        # 6. Avanzar manualmente hasta open_eyes y pasar a día para probar votación
        host.emit('advance_turn')  # -> seer
        host.emit('advance_turn')  # -> open_eyes
        game_service._cancel_turn_timer(room_code)
        game_service._advance_to_day_phase(room_code)

        # 7. Iniciar votación, votar y revelar resultados
        host.emit('end_discussion')
        assert any(ev['name'] == 'voting_started' for ev in host.get_received())

        player_ids = list(room_repository.get_game(room_code).players.keys())
        host.emit('submit_vote', {'target_player_id': player_ids[1]})
        p2.emit('submit_vote', {'target_player_id': player_ids[0]})
        p3.emit('submit_vote', {'target_player_id': player_ids[0]})

        host.emit('end_voting')
        end_events = host.get_received()
        assert any(ev['name'] == 'reveal' for ev in end_events)
        assert any(ev['name'] == 'game_end' for ev in end_events)
    finally:
        for sc in (host, p2, p3):
            if sc.is_connected():
                sc.disconnect()
