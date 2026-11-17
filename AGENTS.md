# AGENTS.md — One Night Ultimate Werewolf (werewolf_DDD)

## Descripción del proyecto
Aplicación web multijugador en tiempo real basada en *One Night Ultimate Werewolf* (Aldeano, Lobo, Vidente, Ladrón, Alborotadora, Borracho, Insomne, Masones, Cazador, Curtidor).

## Arquitectura y estructura
- **Frontend (`frontend/`):** React + Zustand (`src/store/gameStore.js`) + Socket.IO Client.
  - Toda la gestión de WebSockets vive exclusivamente en `frontend/src/hooks/useGameSocket.js`. No añadir `socket.on` ni `socket.emit` sueltos dentro de `App.jsx`.
  - Componentes de turnos nocturnos en `frontend/src/components/night-phases/`.
- **Backend (`backend/`):** Python + Flask + Flask-SocketIO bajo arquitectura DDD.
  - `main/`: Capa de presentación (`app.py`, `http_routes.py`, `socket_handlers.py`, `session_manager.py`).
  - `services/`: Orquestación, temporizadores y emisión de eventos (`game_service.py` actúa como fachada pública).
  - `domain/`: Lógica pura del juego sin dependencias de red (`game_logic.py`, `night_resolution.py`, `voting_resolution.py`, `roles/`).
  - `infrastructure/`: Persistencia de salas (`room_repository.py` en memoria y Redis).
  - `tests/`: Suite unificada ejecutable con `pytest`.

## Comandos de ejecución y pruebas

### Ejecutar tests (Backend)
```bash
cd backend
python -m pytest -v
```

### Levantar el proyecto en desarrollo local
- **Backend:**
  ```bash
  cd backend
  pip install -r requirements.txt
  python run.py
  ```
- **Frontend:**
  ```bash
  cd frontend
  npm install
  npm run dev
  ```

### Levantar el proyecto con Docker Compose
```bash
docker compose up --build
```

## Reglas críticas de desarrollo
1. **Contrato de eventos Socket.IO:** Nunca cambiar los nombres ni la estructura de payloads de `SOCKET_EVENTS` (`game_update`, `private_update`, `turn_start`, `night_action`, `action_result`, `reveal`) sin actualizar simultáneamente `backend/services/state_emitter.py` y `frontend/src/hooks/useGameSocket.js`.
2. **Orden nocturno y estados:** Respetar estrictamente el orden de resolución de roles (ej. Ladrón actúa antes que Alborotadora, y ambos antes que Insomne) y mantener sincronizados los timestamps del servidor para evitar condiciones de carrera.
3. **Tests obligatorios:** Tras cualquier cambio en `domain/`, `services/` o `main/`, ejecutar `pytest` dentro de `backend/` y verificar que toda la suite pasa en verde.
4. **Seguridad y despliegue:** Nunca subir claves reales ni dejar activos los flags de debug/testing en `docker-compose.yml` para producción.

## Skills y procedimientos del proyecto
- **`add-new-role`** ([.agents/skills/add-new-role/SKILL.md](.agents/skills/add-new-role/SKILL.md)): Guía paso a paso para implementar un nuevo rol respetando la arquitectura DDD y el contrato de Socket.IO.
  - **Dominio (`backend/domain/`):** Registrar el identificador y metadatos en `roles/base.py` (`RoleType`), crear la clase en `roles/<nombre_rol>.py` (o `passive_roles.py`), exportarla en `roles/__init__.py` y `factory.py` (`RoleFactory`), e integrar sus reglas en `night_resolution.py` y/o `voting_resolution.py`.
  - **Aplicación (`backend/services/`):** Revisar `night_orchestrator.py`, `voting_orchestrator.py` y `state_emitter.py` para datos privados y temporizadores de turnos falsos cuando el rol esté en el centro.
  - **Frontend (`frontend/src/`):** Añadir descripción/icono en `constants.js`, habilitarlo en `RoleSelector.jsx`, crear el componente nocturno en `components/night-phases/<NombreRol>Phase.jsx` (conectado en `NightPhase.jsx`) y verificar `RevealPhase.jsx`.
  - **Verificación:** Ejecutar `pytest` en `backend/` y validar el rol con la skill `simulate-role-playtest`.
- **`simulate-role-playtest`** ([.agents/skills/simulate-role-playtest/SKILL.md](.agents/skills/simulate-role-playtest/SKILL.md)): Batería automatizada de playtest multijugador (usando `SocketIO test_client` y/o múltiples pestañas con `?autoJoin=1` / `TestingPanel`) que verifica 5 escenarios obligatorios antes de entregar el reporte (✅/❌):
  1. Rol en el centro (temporizador falso e interacción de Vidente/Borracho).
  2. Uso activo en manos de un jugador (`turn_start`, `night_action` y `privateState`).
  3. Timeout nocturno y reconexión (`reconnect_session` / F5) sin bloquear la partida.
  4. Intercambio nocturno con Ladrón, Alborotadora e Insomne y consistencia en `RevealPhase`.
  5. Votación, muerte, efectos especiales, empates (Lobo/Curtidor) y cálculo de victoria en `voting_resolution.py`.

