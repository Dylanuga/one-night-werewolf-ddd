# One Night Werewolf DDD - AI Agent Instructions

## Project Overview
This is a real-time multiplayer web implementation of "One Night Ultimate Werewolf" using **Domain-Driven Design (DDD)** principles. Players receive secret roles, perform night actions, then vote to eliminate werewolves.

## Architecture & Key Patterns

### Backend - Strict DDD Layers
- **Domain** (`backend/domain/`): Pure business logic with NO external dependencies
  - `game_logic.py`: Core game orchestration, phase management, turn ordering
  - `player.py`: Player entity with role assignment and actions
  - `roles.py`: Role-specific behavior using Factory pattern
- **Services** (`backend/services/`): Application coordination layer
  - `game_service.py`: Orchestrates domain logic, handles WebSocket emissions
- **Infrastructure** (`backend/infrastructure/`): External concerns
  - `room_repository.py`: In-memory game state persistence
- **Main** (`backend/main/`): Entry point with Flask-SocketIO setup

### Frontend - React + Zustand State Management
- **Store** (`frontend/src/store/gameStore.js`): Zustand global state with computed getters
- **Hooks** (`frontend/src/hooks/useSocket.js`): WebSocket communication abstraction
- **Components**: Phase-specific UI components with real-time updates

## Critical Development Patterns

### 1. Domain-Driven Design Rules
- **Never** put business logic in infrastructure or UI layers
- All game rules belong in `domain/` - roles, turn order, win conditions
- Use `game_service.py` only for coordination, not business logic
- Repository interfaces are defined in domain, implemented in infrastructure

### 2. WebSocket Communication Flow
```
Frontend (useSocket) → SocketIO Events → app.py → game_service.py → domain/game_logic.py
                    ← emit_callback    ← room updates ← state changes ← business logic
```

**Key Events Pattern:**
- All game state changes emit to entire room: `socketio.emit(event, data, room=room_code)`
- Private data uses player-specific emissions: `emit('private_update', player_state)`
- Frontend automatically syncs via `SOCKET_EVENTS` constants

### 3. Player Identity & Reconnection System
**CRITICAL**: Uses stable player IDs for reconnection:
```python
player_id = f"player_{room_code}_{player_name}".replace(" ", "_")
```
- Players maintain identity across disconnections
- Roles and game state persist during reconnections
- Socket ID mapping separate from game identity

### 4. State Management Patterns
**Zustand Store** (`gameStore.js`):
- `gameState`: Public room state (all players)
- `privateState`: Player-specific data (role, actions)
- Computed getters with fallback logic: `gameState || privateState`
- Auto-cleanup for temporary states (errors, action results)

### 5. Testing Infrastructure
**Test Mode Commands:**
```bash
# Create test room with specific roles
POST /test/create-test-room
{
  "role_distribution": {
    "players": ["werewolf", "mason", "mason", "villager"],
    "center": ["villager", "seer", "robber"]
  },
  "auto_start": true
}

# Check test status
GET /test/status

# Advance turns manually
POST /test/advance-turn
```

## Development Workflows

### Running the Application
```bash
# Backend
cd backend && python run.py

# Frontend  
cd frontend && npm start
```

### Adding New Roles
1. Define role class in `backend/domain/roles.py` with `turn_order` and `execute_action()`
2. Add to `RoleFactory.create_role()` method
3. Implement frontend UI in `components/night-phases/`
4. Add to role validation in `app.py`

### Phase Management
Game phases follow strict order: `LOBBY → ROLE_SELECTION → NIGHT_PHASE → DAY_PHASE → VOTING → GAME_END`
- Turn advancement is automatic via `game_logic.advance_night_turn()`
- Night phases use role-specific `turn_order` for sequencing
- Timer system in `game_service.py` manages phase transitions

## Common Pitfalls & Solutions

### WebSocket State Sync
- **Problem**: Frontend shows stale state after reconnection
- **Solution**: Always emit `private_update` after reconnection in `join_room` handler

### Role Distribution
- **Problem**: Roles must equal `player_count + 3` (center cards)
- **Solution**: Validate in `set_selected_roles()` before game start

### Test Mode Debugging
- **Problem**: Need controlled role assignment for testing
- **Solution**: Use `test_role_distribution` in `game_logic.py` to override random shuffling

### DDD Boundary Violations
- **Problem**: Temptation to add database/UI logic to domain
- **Solution**: Keep `domain/` pure - use dependency injection through `game_service.py`

## File Modification Patterns

When editing:
- **Domain logic**: Modify `backend/domain/` files, test with `/test/` endpoints
- **UI features**: Update React components + corresponding `gameStore.js` state
- **Communication**: Add new events to `utils/constants.js` and `app.py`
- **Testing**: Use predefined test configurations from `/test/presets`

This architecture emphasizes clean separation of concerns, real-time communication, and maintainable domain logic. Always preserve the DDD boundaries and test critical flows using the built-in test infrastructure.