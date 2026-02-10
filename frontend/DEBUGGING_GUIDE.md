# 🔍 Guía de Debugging - Sistema de Night Actions

## Resumen de las Mejoras Implementadas

Este documento explica cómo usar el nuevo sistema de debugging implementado para resolver el problema de UI congelada tras recibir respuestas de 'night_action'.

## 🛠️ Sistema de Debugging Implementado

### 1. **Logs Detallados en el Store (gameStore.js)**

#### Métodos Mejorados:
- `setActionResult()`: Logs exhaustivos con verificación de cambios y timestamps únicos
- `setPrivateState()`: Anti-duplicados y actualizaciones inmutables con IDs únicos
- `getNightAction()`: Logs específicos para debugging de night_action
- `executeNightAction()`: Logs completos del flujo de ejecución

#### Ejemplo de logs que verás:
```javascript
🔍 DEBUG setActionResult - INICIO: {
  resultRecibido: {...},
  estadoActual: {...},
  optimisticState: {...},
  timestamp: 1699123456789
}
```

### 2. **Manejo Mejorado de Eventos Socket (App.jsx)**

#### Eventos Monitoreados:
- `PRIVATE_UPDATE`: Prevención de duplicados mejorada con ID único por contenido
- `ACTION_RESULT`: Verificación de estado antes y después del set
- `NIGHT_ACTION`: Logs básicos (se maneja vía private_update)
- `TURN_START`: Logs del estado currentTurnDisplay
- `GAME_UPDATE`: Logs del estado gameState

#### Prevención de Duplicados:
```javascript
const eventId = `${data.phase}_${data.room_code}_${data.your_role}_${data.current_turn_role}_${data.is_your_turn}_${JSON.stringify(data.night_action)}`;
```

### 3. **Memoización Inteligente (NightPhase.jsx)**

#### Características:
- Logs detallados en valores derivados memoizados
- Dependencias específicas incluyendo `privateState._lastUpdate`
- Múltiples useEffect con logs específicos para diferentes aspectos
- Debugging de rendering con logs en callback memoizado

### 4. **Debugging Específico por Rol (WerewolfPhase.jsx)**

#### Mejoras en hasActed:
- Reset inteligente cuando no es el turno
- Detección automática cuando se completa la acción
- Logs específicos para cambios de estado
- Debugging exhaustivo de clicks y validaciones

### 5. **Hooks de Debugging Personalizados**

#### `useDebugState.js`:
```javascript
// Uso básico
const debuggedState = useDebugState('ComponentName.stateName', state, [dependencies]);

// Uso avanzado con opciones
const debuggedState = useDebugState('ComponentName.stateName', state, [deps], {
  enabled: true,
  deep: true,
  logRenders: false,
  ignoreKeys: ['_timestamp']
});
```

#### Variantes Disponibles:
- `useDebugStateSimple`: Para debugging básico sin comparación profunda
- `useDebugStateObject`: Para objetos complejos con keys ignoradas
- `useDebugStateThrottled`: Para estados de alta frecuencia

#### `useDebugUtils.js`:
```javascript
// Monitoring de renders
const renderCount = useDebugRenders('ComponentName', props);

// Debugging de efectos
useDebugEffect('effect_name', callback, deps);

// Medición de performance
const { measurePerformance } = useDebugPerformance('functionName');

// Lifecycle debugging
useDebugLifecycle('ComponentName');

// Sistema de eventos
const { logEvent } = useDebugEvents('ComponentName');
```

## 🔍 Cómo Usar el Sistema

### Para Debugging General:
1. **Abre las DevTools del navegador**
2. **Ve a la pestaña Console**
3. **Filtra por los prefijos de debugging:**
   - `🔍 DEBUG` - Logs generales
   - `🎯` - Eventos específicos
   - `🔄` - Cambios de estado
   - `⚠️` - Warnings/problemas
   - `✅` - Operaciones exitosas
   - `❌` - Errores

### Para Debugging de Night Actions:
1. **Inicia una partida de prueba**
2. **Llega a la fase nocturna**
3. **Observa los logs en consola mientras:**
   - Cambias de turno
   - Ejecutas acciones nocturnas
   - Recibes resultados de acciones

### Ejemplo de Flujo de Logs Esperado:
```
🔍 DEBUG NightPhase memoizedValues - CALCULANDO: {...}
🔍 DEBUG PRIVATE_UPDATE - RECIBIDO: {...}
🎯 DEBUG NightPhase - ACTION RESULT DETECTADO: {...}
🔍 DEBUG WerewolfPhase - CLICK EN CARTA: {...}
✅ WerewolfPhase - Acción emitida exitosamente
🔍 DEBUG ACTION_RESULT - RECIBIDO: {...}
```

## 🚨 Identificación de Problemas

### UI Congelada tras night_action:
**Busca estos patrones en los logs:**

1. **Problema: Estado no se actualiza**
   ```
   🔄 setActionResult: Sin cambios detectados, ignorando
   ```
   - **Solución**: Verifica que el servidor envía datos únicos

2. **Problema: Componente no re-renderiza**
   ```
   🎨 RENDER #X - ComponentName (reason: No state changes detected)
   ```
   - **Solución**: Verifica dependencias en useEffect y useMemo

3. **Problema: Eventos duplicados**
   ```
   🔄 private_update duplicado ignorado por contenido
   ```
   - **Solución**: Verificar que el servidor no envía duplicados

4. **Problema: ActionResult undefined**
   ```
   🔍 DEBUG getNightAction: { nightAction: null, privateState: true }
   ```
   - **Solución**: Verificar que el servidor incluye night_action en private_update

## 📊 Métricas de Performance

### Monitoring Automático:
- **Conteo de renders** por componente
- **Tiempo de ejecución** de funciones críticas
- **Frecuencia de cambios** de estado
- **Lifecycle events** timing

### Snapshots de Estado:
```javascript
const { takeSnapshot, compareSnapshots } = useDebugSnapshot('GameState');

// Tomar snapshot antes de acción
const beforeId = takeSnapshot(gameState, 'before_night_action');

// Tomar snapshot después de resultado
const afterId = takeSnapshot(gameState, 'after_action_result');

// Comparar cambios
compareSnapshots(beforeId, afterId);
```

## 🎯 Debugging en Producción

### Variables de Entorno:
```javascript
// Los hooks solo están activos en desarrollo por defecto
const enabled = process.env.NODE_ENV === 'development'

// Para habilitar en producción específicamente:
const debuggedState = useDebugState('StateName', state, deps, { 
  enabled: true 
});
```

### Debugging Condicional:
```javascript
// Solo para usuarios específicos
const isDebugUser = localStorage.getItem('debugMode') === 'true';
const debuggedState = useDebugState('StateName', state, deps, { 
  enabled: isDebugUser 
});
```

## 🛡️ Características Anti-Congelamiento

### 1. **Actualizaciones Inmutables Forzadas**
```javascript
set(state => ({
  ...state,
  actionResult: result ? { ...result, _timestamp: Date.now() } : null
}));
```

### 2. **Dependencias Específicas**
```javascript
useEffect(() => {
  // Código específico
}, [
  actionResult?.message,    // Dependencia específica
  privateState?._updateId   // ID único para forzar cambios
]);
```

### 3. **Anti-Duplicados Inteligente**
```javascript
const eventId = `${phase}_${room}_${role}_${turn}_${action_data}`;
if (processedEvents.has(eventId)) return; // Ignorar duplicado
```

### 4. **Estados Optimistas con Cleanup**
```javascript
setOptimisticAction('night_action', action);
// Auto-cleanup cuando llega resultado real
```

Este sistema garantiza que la UI nunca se congele y proporciona visibility completa del flujo de datos para identificar y resolver problemas rápidamente.