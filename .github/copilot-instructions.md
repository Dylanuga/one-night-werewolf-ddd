
# One Night Werewolf DDD — AI Coding Agent Guide

## Visión General y Arquitectura
Juego multijugador en tiempo real basado en "One Night Ultimate Werewolf". Arquitectura DDD estricta: backend en Python (Flask-SocketIO), frontend en React con Zustand. Separación clara de lógica de dominio, infraestructura y servicios.

### Backend (Python, DDD)
- `backend/domain/`: Lógica de juego pura (sin dependencias externas). Ejemplo: `game_logic.py` (fases, turnos), `roles.py` (patrón Factory para roles), `player.py` (entidad jugador).
- `backend/services/`: Orquestación y coordinación de dominio, nunca lógica de negocio. Ejemplo: `game_service.py` (emisión de eventos, timers).
- `backend/infrastructure/`: Persistencia y adaptadores externos. Ejemplo: `room_repository.py` (estado en memoria).
- `backend/main/`: Entrada de la app, configuración Flask-SocketIO. Ejemplo: `app.py` (handlers de eventos, validaciones de roles).

### Frontend (React + Zustand)
- `frontend/src/store/gameStore.js`: Estado global (Zustand), getters computados, limpieza automática de estados temporales.
- `frontend/src/hooks/useSocket.js`: Abstracción de WebSocket, maneja reconexión y sincronización.
- `frontend/src/components/`: UI por fases, componentes para cada rol y fase.

## Patrones y Flujos Críticos

### 1. DDD Estricto
- Toda la lógica de reglas va en `domain/`. Nunca mezclar lógica de negocio en infraestructura, servicios o UI.
- `game_service.py` solo coordina, no implementa reglas.
- Validaciones de roles y fases en `app.py`.

### 2. Comunicación WebSocket
Flujo: Frontend (useSocket) ⇄ SocketIO ⇄ `app.py` ⇄ `game_service.py` ⇄ `game_logic.py`.
- Cambios de estado: `socketio.emit(event, data, room=room_code)`.
- Datos privados: `emit('private_update', player_state)`.
- Eventos clave definidos en `utils/constants.js` y sincronizados en frontend/backend.

### 3. Identidad y Reconexión de Jugadores
- ID estable: `player_{room_code}_{player_name}` (sin espacios).
- El estado y rol persisten tras reconexión; el mapeo socket ID es independiente.

### 4. Testing y Debug
- Endpoints de test en backend: `/test/create-test-room`, `/test/status`, `/test/advance-turn`.
- Permiten roles fijos y avance manual de turnos para pruebas deterministas.
- Usa archivos como `test_domain.py`, `test_masones.py` para pruebas unitarias.

### 5. Workflows de Desarrollo
- Backend: `cd backend && python run.py`
- Frontend: `cd frontend && npm start`
- Añadir rol: define clase en `roles.py`, agrega a `RoleFactory`, implementa UI en `components/night-phases/`, valida en `app.py`.

### 6. Convenciones y Errores Comunes
- Roles = jugadores + 3 (centro). Validar antes de iniciar partida.
- Tras reconexión, siempre emitir `private_update`.
- No mezclar lógica de UI/persistencia en `domain/`.
- Usa presets de test para pruebas controladas.

## Ejemplos de Modificación
- Lógica de dominio: `backend/domain/`, prueba con endpoints `/test/`.
- UI: `frontend/src/components/`, estado en `gameStore.js`.
- Comunicación: nuevos eventos en `utils/constants.js` y `app.py`.

---
¿Falta algún flujo, convención o integración relevante? Indica qué parte es poco clara o incompleta para iterar y mejorar la guía.