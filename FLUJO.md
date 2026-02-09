# 🔄 **FLUJO COMPLETO: Comunicación Backend ↔ Frontend**

## **CONFIGURACIÓN DE EJEMPLO**
- **Jugadores:** 4 (Dilan, 1, 2, 3)
- **Roles:** [mason, mason, villager, villager, villager, werewolf, werewolf]
- **Distribución Final:**
  - Dilan → villager
  - Jugador "1" → werewolf  
  - Jugador "2" → mason
  - Jugador "3" → mason
  - Centro → [villager, villager, werewolf]

---

## **FASE 1: INICIO DEL JUEGO** 🎮

### **Backend:**
```
1. 🔍 Calcula roles y los distribuye
2. 🔧 Calcula turnos nocturnos: ['werewolf', 'mason']
3. ✅ Emite a TODA LA SALA:
   📡 socketio.emit('game_started', {
     room_code: 'WPIQ',
     message: 'El juego ha comenzado',
     timestamp: 1757854935.558
   }, room='WPIQ')
```

### **Frontend (Todos los jugadores):**
```
✅ Reciben 'game_started'
✅ Actualizan estado a phase: 'night_phase'
✅ Logs: "🎮 Juego iniciado: {message: 'El juego ha comenzado'}"
```

---

## **FASE 2: PRIMER TURNO NOCTURNO - WEREWOLF** 🐺

### **Backend:**
```
1. 🔧 Inicia turno werewolf
2. ⏰ Inicia timer de 6 segundos
3. 📡 Emite a TODA LA SALA:
   socketio.emit('turn_start', {
     role: 'werewolf',
     phase: 'Fase: werewolf', 
     duration: 6,
     timestamp: 1757854935.552
   }, room='WPIQ')

4. 📡 Emite SOLO al werewolf:
   socketio.emit('night_action', {
     type: 'can_view_center',
     message: 'Eres el único lobo. Puedes ver una carta del centro.',
     center_positions: [0, 1, 2]
   }, to=socket_werewolf)

5. 📡 Emite a CADA JUGADOR individualmente:
   socketio.emit('private_update', {estado_completo}, to=socket_individual)
```

### **Frontend Werewolf (Jugador "1"):**
```
✅ Recibe 'turn_start':
   - currentTurnRole: 'werewolf'
   - timestamp: 1757854935.552
   - PhaseTimer inicia countdown de 6s

✅ Recibe 'night_action':
   - hasNightAction: true
   - isCurrentUserTurn: true
   - Muestra UI: "Eres el único lobo. Puedes ver una carta del centro."

⚡ Usuario hace clic en posición del centro
📤 Emite al backend:
   socket.emit('night_action', {
     action: { center_position: 0 }
   })
```

### **Frontend Otros Jugadores (Dilan, 2, 3):**
```
✅ Reciben 'turn_start':
   - currentTurnRole: 'werewolf'
   - isCurrentUserTurn: false
   - PhaseTimer muestra: "Turno de werewolf (6s)"

❌ NO reciben 'night_action' (correcto)
✅ Ven UI: "Es el turno del werewolf, esperando..."
```

### **Backend (Respuesta a acción):**
```
✅ Recibe 'night_action' del werewolf
📡 Emite SOLO al werewolf:
   socketio.emit('action_result', {
     success: true,
     message: 'Has visto la carta: villager',
     card_seen: 'villager'
   }, to=socket_werewolf)

⏰ Después de 6s (automático):
   - Cancela timer
   - Avanza al siguiente turno
```

---

## **FASE 3: SEGUNDO TURNO NOCTURNO - MASON** 🏗️

### **Backend:**
```
1. 🔧 Avanza a turno mason
2. ⏰ Inicia timer de 6 segundos
3. 📡 Emite a TODA LA SALA:
   socketio.emit('turn_start', {
     role: 'mason',
     phase: 'Fase: mason',
     duration: 6,
     timestamp: 1757854941.569
   }, room='WPIQ')

4. 📡 Emite a AMBOS masones:
   - Al jugador "2": 'night_action' con other_mason_name: '3'
   - Al jugador "3": 'night_action' con other_mason_name: '2'

5. 📡 Emite 'private_update' a todos
```

### **Frontend Masones (Jugadores "2" y "3"):**
```
✅ Reciben 'turn_start':
   - currentTurnRole: 'mason'
   - PhaseTimer inicia countdown de 6s

✅ Reciben 'night_action':
   - hasNightAction: true
   - isCurrentUserTurn: true
   - Muestra UI: "Tu compañero masón es: [nombre]"

📝 No necesitan hacer acción (solo información)
```

### **Frontend Otros Jugadores (Dilan, "1"):**
```
✅ Reciben 'turn_start':
   - currentTurnRole: 'mason'
   - isCurrentUserTurn: false
   - PhaseTimer muestra: "Turno de mason (6s)"

❌ NO reciben 'night_action'
✅ Ven UI: "Es el turno de los masones, esperando..."
```

### **Backend (Auto-advance):**
```
⏰ Después de 6s:
   - Cancela timer
   - No hay más turnos nocturnos
   - Avanza a fase de día
```

---

## **FASE 4: TRANSICIÓN A FASE DE DÍA** ☀️

### **Backend:**
```
1. 🌞 Cambia phase a 'day_phase'
2. 📡 Emite a TODA LA SALA:
   socketio.emit('game_update', {
     phase: 'day_phase',
     // ... resto del estado
   }, room='WPIQ')

3. 📡 Emite 'private_update' a cada jugador
```

### **Frontend (Todos los jugadores):**
```
✅ Reciben 'game_update':
   - phase: 'day_phase'
   - Cambian a componente DayPhase

✅ Actualizan UI:
   - Muestran lista de jugadores
   - Botones de votación
   - Logs de la noche
```

---

## **📊 RESUMEN DE EVENTOS POR JUGADOR:**

### **Jugador Dilan (villager):**
```
✅ game_started
✅ turn_start (werewolf) → NO es su turno
✅ private_update
✅ turn_start (mason) → NO es su turno  
✅ private_update
✅ game_update (day_phase)
```

### **Jugador "1" (werewolf):**
```
✅ game_started
✅ turn_start (werewolf) → ES su turno
✅ night_action → Puede ver centro
✅ private_update
📤 night_action → Elige centro
✅ action_result → Ve carta
✅ turn_start (mason) → NO es su turno
✅ private_update
✅ game_update (day_phase)
```

### **Jugadores "2" y "3" (masones):**
```
✅ game_started
✅ turn_start (werewolf) → NO es su turno
✅ private_update
✅ turn_start (mason) → ES su turno
✅ night_action → Ve compañero masón
✅ private_update
✅ game_update (day_phase)
```

---

## **⚡ TIMING CRÍTICO:**

```
T+0s:   🎮 game_started
T+0s:   📡 turn_start (werewolf)
T+0s:   📡 night_action (solo al werewolf)
T+3s:   📤 werewolf hace acción
T+3s:   ✅ action_result
T+6s:   ⏰ AUTO-ADVANCE
T+6s:   📡 turn_start (mason)
T+6s:   📡 night_action (solo a masones)
T+12s:  ⏰ AUTO-ADVANCE
T+12s:  🌞 game_update (day_phase)
```

---

## **🔧 EVENTOS SOCKET.IO:**

### **Eventos del Backend al Frontend:**
- `game_started` → Toda la sala
- `turn_start` → Toda la sala
- `night_action` → Jugador específico con rol activo
- `action_result` → Jugador que hizo la acción
- `private_update` → Cada jugador individualmente
- `game_update` → Toda la sala

### **Eventos del Frontend al Backend:**
- `night_action` → Respuesta del jugador con su acción
- `join_room` → Conexión inicial/reconexión
- `start_game` → Host inicia partida

---

## **📋 REGLAS DE NEGOCIO:**

1. **Turnos Secuenciales:** Solo un rol activo a la vez
2. **Timer Automático:** 6 segundos por turno, avance automático
3. **Eventos Dirigidos:** `night_action` solo al rol activo
4. **Estado Sincronizado:** `private_update` mantiene sincronización
5. **Reconexión:** Reenvío automático de estado actual

Este flujo representa el comportamiento **CORRECTO** esperado del sistema.