#!/usr/bin/env python3
"""
Pruebas de avance automático de turnos nocturnos usando Flask test_client y socketio.sleep.
"""


def test_auto_turn_advancement(client, socketio_app):
    """Prueba que los turnos nocturnos avanzan automáticamente hasta llegar a la fase de día."""
    role_distribution = {
        'players': ['werewolf', 'mason', 'mason', 'villager', 'villager', 'villager'],
        'center': ['villager', 'villager', 'villager']
    }

    assert client.post('/test/reset').status_code == 200

    create_resp = client.post('/test/create-test-room', json={
        'role_distribution': role_distribution,
        'auto_start': True,
        'turn_duration': 1
    })
    assert create_resp.status_code == 200
    created = create_resp.get_json()
    assert created['game_started'] is True

    initial_status = client.get('/test/status').get_json()
    assert initial_status['phase'] == 'night_phase'
    assert initial_status['current_turn_role'] == 'werewolf'

    seen_roles = {initial_status['current_turn_role']}
    reached_day = False

    # 2 turnos nocturnos de 1s + transición open_eyes de 6s = ~8s
    for _ in range(110):
        socketio_app.sleep(0.1)
        status = client.get('/test/status').get_json()
        if status.get('current_turn_role'):
            seen_roles.add(status['current_turn_role'])
        if status.get('phase') == 'day_phase':
            reached_day = True
            break

    assert 'werewolf' in seen_roles
    assert 'mason' in seen_roles
    assert reached_day is True, f"No se alcanzó day_phase a tiempo; último estado: {status}"
    assert client.post('/test/reset').status_code == 200

