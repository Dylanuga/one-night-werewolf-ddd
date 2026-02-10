// src/store/gameStore.js
import { create } from 'zustand';

// ✅ NUEVA FUNCIÓN: Comparación profunda optimizada para estados específicos
const deepEqual = (obj1, obj2) => {
  if (obj1 === obj2) return true;
  if (!obj1 || !obj2) return obj1 === obj2;
  if (typeof obj1 !== 'object' || typeof obj2 !== 'object') return obj1 === obj2;
  
  const keys1 = Object.keys(obj1);
  const keys2 = Object.keys(obj2);
  
  if (keys1.length !== keys2.length) return false;
  
  for (let key of keys1) {
    if (!keys2.includes(key)) return false;
    if (!deepEqual(obj1[key], obj2[key])) return false;
  }
  
  return true;
};

export const useGameStore = create((set, get) => ({
  // ✅ Sistema de debounce para actualizaciones de estado
  debounceTimers: {},
  
  // ✅ Debounced state update
  debouncedSetState: (key, value, delay = 100) => {
    const { debounceTimers } = get();
    
    // Limpiar timer anterior si existe
    if (debounceTimers[key]) {
      clearTimeout(debounceTimers[key]);
    }
    
    // Crear nuevo timer
    debounceTimers[key] = setTimeout(() => {
      set({ [key]: value });
      delete debounceTimers[key];
    }, delay);
  },
  
  // Estado de conexión y socket
  isConnected: false,
  socket: null,
  
  // ✅ NUEVO: Estados optimistas
  optimisticState: {
    actionInProgress: false,
    optimisticActionResult: null,
    lastActionTimestamp: null
  },
  
  // ✅ NUEVO: Estado de error handling
  connectionState: {
    isStable: true,
    reconnectAttempts: 0,
    lastDisconnectReason: null,
    lastSuccessfulPing: null
  },
  
  // Estado del juego público
  gameState: null,
  
  // Estado privado del jugador
  privateState: null,
  
  // Información del turno actual (SOLO para UI - no para lógica)
  currentTurnDisplay: null,
  
  // Resultado de la última acción
  actionResult: null,
  revealData: null,
  myVote: null,
  
  // Errores
  error: null,
  
  // Logs del juego
  logs: [],
  
  // Estado del formulario de entrada
  playerName: '',
  roomCode: '',
  
  // 🆕 NUEVO: Estado de roles seleccionados (para sincronización en tiempo real)
  selectedRoles: {},
  
  // Acciones
  setSocket: (socket) => set({ socket }),
  
  setConnectionStatus: (connected) => {
    const current = get().isConnected;
    if (current === connected) {
      console.log('🔄 setConnectionStatus: Sin cambios, ignorando');
      return;
    }
    console.log('🔌 Actualizando estado de conexión:', connected);
    set({ isConnected: connected });
  },
  
  // ✅ NUEVAS FUNCIONES: Manejo de conexión
  updateConnectionState: (updates) => {
    const currentState = get().connectionState;
    
    // ✅ Evitar actualizaciones si no hay cambios
    const hasChanges = Object.keys(updates).some(key => 
      currentState[key] !== updates[key]
    );
    
    if (!hasChanges) {
      console.log('🔄 updateConnectionState: Sin cambios detectados, ignorando');
      return;
    }
    
    const newState = {
      ...currentState,
      ...updates,
      lastSuccessfulPing: updates.isStable ? Date.now() : currentState.lastSuccessfulPing
    };
    
    console.log('🔌 Actualizando estado de conexión:', newState);
    set({ connectionState: newState });
  },
  
  handleDisconnection: (reason) => {
    const { connectionState, clearOptimisticState } = get();
    
    // Limpiar estados optimistas en desconexión
    clearOptimisticState();
    
    set({
      connectionState: {
        ...connectionState,
        isStable: false,
        lastDisconnectReason: reason,
        reconnectAttempts: connectionState.reconnectAttempts + 1
      }
    });
    
    console.log(`💔 Desconexión manejada: ${reason} (intento #${connectionState.reconnectAttempts + 1})`);
  },
  
  handleReconnection: () => {
    set({
      connectionState: {
        isStable: true,
        reconnectAttempts: 0,
        lastDisconnectReason: null,
        lastSuccessfulPing: Date.now()
      }
    });
    
    console.log('✅ Reconexión exitosa - estado limpiado');
  },
  
  setGameState: (state) => {
    const current = get().gameState;
    
    // ✅ Evitar actualizaciones innecesarias
    if (current === state) {
      console.log('🔄 setGameState: Misma referencia, ignorando');
      return;
    }
    
    // ✅ Comparación profunda para objetos diferentes usando deepEqual
    if (current && state && deepEqual(current, state)) {
      console.log('🔄 setGameState: Sin cambios en contenido, ignorando');
      return;
    }
    
    console.log('🎮 Actualizando gameState:', state);
    set({ gameState: state });
  },
  
  setPrivateState: (state) => {
    console.log('🔍 DEBUG setPrivateState - INICIO:', {
      estadoRecibido: state,
      estadoActual: get().privateState,
      timestamp: Date.now()
    });

    if (!state) {
      console.log('⚠️ setPrivateState: Estado null/undefined recibido');
      return;
    }

    // ✅ ANTI-DUPLICADOS: Verificación profunda por contenido
    const current = get().privateState;
    if (current) {
      // Comparar todos los campos relevantes
      const criticalFields = [
        'phase', 'current_turn_role', 'is_your_turn', 'your_role',
        'room_code', 'player_count', 'selected_roles_count',
        'turn_timestamp'  // ✅ CRÍTICO: Detectar cambios de turno por timestamp
      ];
      
      // 🔍 DEBUG: Log detallado de comparación campo por campo
      console.log('🔍 DEBUG setPrivateState - COMPARACIÓN DETALLADA:');
      criticalFields.forEach(field => {
        const currentVal = current[field];
        const newVal = state[field];
        const changed = currentVal !== newVal;
        console.log(`  📝 ${field}: "${currentVal}" → "${newVal}" (cambió: ${changed})`);
      });
      
      const hasBasicChanges = criticalFields.some(field => current[field] !== state[field]);
      
      // ✅ ESPECÍFICO: Detectar cambios de turno por timestamp incluso si otros campos son iguales
      const isTurnChange = current.turn_timestamp !== state.turn_timestamp;
      if (isTurnChange) {
        console.log('🔄 CAMBIO DE TURNO DETECTADO por timestamp:', {
          anterior: current.turn_timestamp,
          nuevo: state.turn_timestamp,
          rol: state.current_turn_role
        });
      }
      
      // Comparar objetos complejos por referencia y contenido básico
      const hasActionChanges = current.night_action !== state.night_action || 
        (current.night_action && state.night_action && 
         (current.night_action.type !== state.night_action.type ||
          current.night_action.message !== state.night_action.message));
      
      const hasPlayerChanges = current.players?.length !== state.players?.length;
      
      console.log('🔍 DEBUG setPrivateState - RESUMEN CAMBIOS:', {
        hasBasicChanges,
        hasActionChanges,
        hasPlayerChanges,
        isTurnChange,
        totalChanges: hasBasicChanges || hasActionChanges || hasPlayerChanges || isTurnChange
      });
      
      if (!hasBasicChanges && !hasActionChanges && !hasPlayerChanges && !isTurnChange) {
        console.log('🔄 setPrivateState: Sin cambios detectados, ignorando');
        return;
      }
    }

    // ✅ CRÍTICO: Actualización simple sin timestamps aleatorios
    set(prevState => {
      const newState = {
        ...prevState,
        privateState: state // Usar el estado tal como viene del servidor
      };
      
      console.log('🔍 DEBUG setPrivateState - ESTADO ANTES:', prevState.privateState);
      console.log('🔍 DEBUG setPrivateState - ESTADO DESPUÉS:', newState.privateState);
      
      return newState;
    });

    console.log('🔍 DEBUG setPrivateState - FINAL:', get().privateState);
  },
  
  setCurrentTurnDisplay: (turn) => {
    // ✅ FIX CRÍTICO: Solo comparar role y phase, NO timestamp para permitir actualizaciones
    const current = get().currentTurnDisplay;
    if (current && turn &&
        current.role === turn.role && 
        current.phase === turn.phase &&
        current.duration === turn.duration) {
      console.log('🔄 setCurrentTurnDisplay: Sin cambios relevantes, ignorando');
      return;
    }
    
    console.log('🎮 Actualizando currentTurnDisplay (solo UI):', turn);
    set({ currentTurnDisplay: turn });
  },
  
  setActionResult: (result) => {
    console.log('🔍 DEBUG setActionResult - INICIO:', {
      resultRecibido: result,
      estadoActual: get().actionResult,
      optimisticState: get().optimisticState,
      timestamp: Date.now()
    });

    // ✅ FIX: Evitar set si no hay cambios reales usando comparación profunda
    const currentResult = get().actionResult;
    if (currentResult && result) {
      // Comparar campos críticos en lugar de JSON.stringify completo
      const criticalFields = ['type', 'message', 'success', 'data'];
      const hasChanges = criticalFields.some(field => 
        currentResult[field] !== result[field]
      );
      
      if (!hasChanges) {
        console.log('🔄 setActionResult: Sin cambios detectados, ignorando');
        return;
      }
    } else if (currentResult === result) {
      console.log('🔄 setActionResult: Misma referencia, ignorando');
      return;
    }
    
    // ✅ CRÍTICO: Actualización inmutable para forzar re-render
    set(state => {
      const newState = {
        ...state,
        actionResult: result ? { ...result, _timestamp: Date.now() } : null
      };
      
      console.log('🔍 DEBUG setActionResult - ESTADO ANTES:', {
        actionResult: state.actionResult,
        optimisticState: state.optimisticState
      });
      
      console.log('🔍 DEBUG setActionResult - ESTADO DESPUÉS:', {
        actionResult: newState.actionResult,
        optimisticState: newState.optimisticState
      });
      
      return newState;
    });
    
    // ✅ FIX: Limpiar estado optimista cuando llega resultado real
    const { optimisticState, clearOptimisticState } = get();
    if (optimisticState.actionInProgress) {
      console.log('✅ Limpiando estado optimista tras resultado real');
      clearOptimisticState();
    }
    
    console.log('🔍 DEBUG setActionResult - FINAL:', {
      nuevoActionResult: get().actionResult,
      estadoOptimista: get().optimisticState
    });
    
    // Auto-limpiar después de 3 segundos con verificación
    setTimeout(() => {
      const current = get().actionResult;
      if (current === result || (current && current._timestamp === result?._timestamp)) {
        console.log('🧹 Auto-limpiando actionResult tras 3 segundos');
        set(state => ({ ...state, actionResult: null }));
      }
    }, 3000);
  },

  setRevealData: (data) => {
    const current = get().revealData;
    if (current === data) return;
    set({ revealData: data });
  },

  setMyVote: (vote) => set({ myVote: vote }),
  
  setError: (error) => {
    const current = get().error;
    // ✅ Evitar actualizaciones innecesarias
    if (current === error || 
        (current && error && current.message === error.message && current.type === error.type)) {
      console.log('🔄 setError: Sin cambios, ignorando');
      return;
    }
    
    console.log('❌ Actualizando error:', error);
    set({ error });
    // Auto-limpiar después de 5 segundos
    setTimeout(() => {
      // Verificar que el error sigue siendo el mismo antes de limpiar
      if (get().error === error) {
        set({ error: null });
      }
    }, 5000);
  },
  
  addLog: (message) => {
    const current = get().logs;
    const lastLog = current[current.length - 1];
    
    // ✅ Evitar logs duplicados consecutivos
    if (lastLog && lastLog.message === message) {
      console.log('🔄 addLog: Mensaje duplicado, ignorando');
      return;
    }
    
    const timestamp = new Date().toLocaleTimeString();
    set(state => ({
      logs: [...state.logs, { timestamp, message }].slice(-20) // Máximo 20 logs
    }));
  },
  
  clearLogs: () => set({ logs: [] }),
  
  setPlayerName: (name) => {
    const current = get().playerName;
    if (current === name) {
      console.log('🔄 setPlayerName: Sin cambios, ignorando');
      return;
    }
    set({ playerName: name });
  },
  
  setRoomCode: (code) => {
    const upperCode = code.toUpperCase();
    const current = get().roomCode;
    if (current === upperCode) {
      console.log('🔄 setRoomCode: Sin cambios, ignorando');
      return;
    }
    set({ roomCode: upperCode });
  },
  
  // 🆕 NUEVO: Acciones para roles seleccionados
  setSelectedRoles: (roles) => {
    const current = get().selectedRoles;
    
    // ✅ Comparación profunda para evitar actualizaciones innecesarias
    if (current && deepEqual(current, roles)) {
      console.log('🔄 setSelectedRoles: Sin cambios detectados, ignorando');
      return;
    }
    
    console.log('🎭 STORE: Actualizando roles seleccionados:', roles);
    set({ selectedRoles: roles });
  },
  
  clearSelectedRoles: () => set({ selectedRoles: {} }),
  
  getSelectedRoles: () => {
    const { selectedRoles } = get();
    return selectedRoles;
  },
  
  getSelectedRolesCount: () => {
    const { selectedRoles } = get();
    return Object.values(selectedRoles).reduce((sum, count) => sum + count, 0);
  },
  
  // Getters computados
  getCurrentPhase: () => {
    const { gameState, privateState } = get();
    // CAMBIO: Usar privateState si gameState no está disponible
    // Esto arregla el problema de que privateState tiene los datos pero gameState es null
    const state = gameState || privateState;
    return state?.phase || 'lobby';
  },
  
  getPlayerRole: () => {
    const { privateState } = get();
    return privateState?.your_role || null;
  },
  
  getOriginalRole: () => {
    const { privateState } = get();
    return privateState?.your_original_role || null;
  },
  
  isHost: () => {
    const { gameState, privateState } = get();
    // CAMBIO: Usar privateState como fallback
    const state = gameState || privateState;
    if (!state?.players) return false;
    
    return state.players.some(player => player.is_host);
  },
  
  getPlayers: () => {
    const { gameState, privateState } = get();
    // CAMBIO: Usar privateState como fallback
    const state = gameState || privateState;
    return state?.players || [];
  },
  
  getPlayerCount: () => {
    const { gameState, privateState } = get();
    // CAMBIO: Usar privateState como fallback
    const state = gameState || privateState;
    return state?.player_count || 0;
  },
  
  getRoomCode: () => {
    const { gameState, privateState } = get();
    // CAMBIO: Usar privateState como fallback para obtener room_code
    // Esto arregla que el frontend no mostraba el código de sala
    const state = gameState || privateState;
    return state?.room_code || null;
  },
  
  getCurrentTurnRole: () => {
    const { privateState } = get();
    // ✅ FUENTE ÚNICA DE VERDAD: solo privateState
    return privateState?.current_turn_role || null;
  },
  
  // ✅ NUEVA FUNCIÓN: obtener información de display del turno
  getCurrentTurnDisplay: () => {
    const { currentTurnDisplay } = get();
    return currentTurnDisplay;
  },
  
  // ✅ NUEVA FUNCIÓN: verificar si es tu turno (solo desde privateState)
  isMyTurn: () => {
    const { privateState } = get();
    return privateState?.is_your_turn || false;
  },
  
  // ✅ MEJORADO: obtener night_action SIN logs (evita ciclos infinitos)
  getNightAction: () => {
    const { privateState } = get();
    return privateState?.night_action || null;
  },
  
  // ✅ NUEVAS FUNCIONES: Manejo de estados optimistas
  setOptimisticAction: (actionType, actionData) => {
    const timestamp = Date.now();
    set({
      optimisticState: {
        actionInProgress: true,
        optimisticActionResult: {
          type: actionType,
          data: actionData,
          timestamp,
          message: 'Procesando acción...'
        },
        lastActionTimestamp: timestamp
      }
    });
    
    console.log('⚡ Estado optimista activado:', actionType, actionData);
  },
  
  clearOptimisticState: () => {
    set({
      optimisticState: {
        actionInProgress: false,
        optimisticActionResult: null,
        lastActionTimestamp: null
      }
    });
    console.log('🧹 Estado optimista limpiado');
  },
  
  getEffectiveActionResult: () => {
    const { actionResult, optimisticState } = get();
    // Priorizar resultado real sobre optimista
    return actionResult || optimisticState.optimisticActionResult;
  },
  
  canStartGame: () => {
    const { gameState, privateState } = get();
    // CAMBIO: Usar privateState como fallback
    const state = gameState || privateState;
    if (!state) return false;
    
    return (
      state.phase === 'lobby' &&
      state.player_count >= 3 &&
      state.player_count <= 8
    );
  },
  
  // 🆕 NUEVO: Getter para verificar si los roles están completos
  areRolesComplete: () => {
    const { selectedRoles, gameState, privateState } = get();
    const state = gameState || privateState;
    if (!state) return false;
    
    const playerCount = state.player_count || 0;
    const requiredRoles = playerCount + 3;
    const totalSelected = Object.values(selectedRoles).reduce((sum, count) => sum + count, 0);
    
    return totalSelected === requiredRoles;
  },
  
  // ✅ NUEVA FUNCIÓN: Emisión con retry y timeout
  emitEventWithRetry: (event, data = {}, retries = 2, timeoutMs = 5000) => {
    const { socket, connectionState } = get();
    
    if (!socket?.connected) {
      console.warn('❌ Socket desconectado para:', event);
      return Promise.reject(new Error('Socket no conectado'));
    }
    
    // Si la conexión no es estable, reducir timeout
    const effectiveTimeout = connectionState.isStable ? timeoutMs : 2000;
    
    return new Promise((resolve, reject) => {
      let attempts = 0;
      
      const tryEmit = () => {
        attempts++;
        console.log(`📤 Emitiendo (intento ${attempts}/${retries + 1}):`, event, data);
        
        const timeoutId = setTimeout(() => {
          if (attempts <= retries) {
            console.log(`⏰ Timeout en intento ${attempts}, reintentando...`);
            tryEmit();
          } else {
            reject(new Error(`Timeout después de ${retries + 1} intentos`));
          }
        }, effectiveTimeout);
        
        socket.emit(event, data, (response) => {
          clearTimeout(timeoutId);
          if (response?.success !== false) {
            resolve(response);
          } else {
            reject(new Error(response?.message || 'Error del servidor'));
          }
        });
      };
      
      tryEmit();
    });
  },
  
  // ✅ FUNCIÓN LEGACY: mantener para compatibilidad
  emitEvent: (event, data = {}) => {
    const { socket } = get();
    console.log('🔌 emitEvent - Socket actual:', socket?.id, 'conectado:', socket?.connected);
    
    if (socket?.connected) {
      try {
        console.log('📤 Emitiendo:', event, data);
        socket.emit(event, data);
        return true;
      } catch (error) {
        console.error('❌ Error emitiendo evento:', event, error);
        return false;
      }
    } else {
      console.warn('❌ Socket no conectado para:', event);
      return false;
    }
  },
  
  createRoom: (name) => {
    const { emitEvent } = get();
    return emitEvent('create_room', { name });
  },
  
  joinRoom: (roomCode, name) => {
    const { emitEvent } = get();
    return emitEvent('join_room', { room_code: roomCode, name });
  },
  
  leaveRoom: () => {
    const { emitEvent, setSelectedRoles } = get();
    setSelectedRoles({});
    return emitEvent('leave_room');
  },
  
  setRoles: (roles) => {
    const { emitEvent, setSelectedRoles } = get();
    const roleCount = {};
    roles.forEach(role => {
      roleCount[role] = (roleCount[role] || 0) + 1;
    });
    setSelectedRoles(roleCount);
    return emitEvent('set_roles', { roles });
  },
  
  startGame: () => {
    const { emitEvent } = get();
    return emitEvent('start_game');
  },
  
  executeNightAction: (action) => {
    console.log('🔍 DEBUG executeNightAction - INICIO:', {
      action,
      estadoOptimista: get().optimisticState,
      isConnected: get().isConnected,
      timestamp: Date.now()
    });

    const { emitEventWithRetry, setOptimisticAction, clearOptimisticState } = get();
    
    // ✅ FIX: Verificar si ya hay una acción en progreso
    const { optimisticState } = get();
    if (optimisticState.actionInProgress) {
      console.log('⚠️ Acción ya en progreso, ignorando nueva acción:', {
        accionEnProgreso: optimisticState,
        nuevaAccion: action
      });
      return false;
    }
    
    console.log('🔍 DEBUG executeNightAction - ESTABLECIENDO ESTADO OPTIMISTA');
    
    // ✅ FIX: Estado optimista más específico con logs
    setOptimisticAction('night_action', action);
    
    console.log('🔍 DEBUG executeNightAction - EMITIENDO AL SERVIDOR');
    
    // ✅ FIX: Usar retry con timeout más corto para UI responsiva
    emitEventWithRetry('night_action', { action }, 1, 2000)
      .then((response) => {
        console.log('✅ DEBUG executeNightAction - RESPUESTA EXITOSA:', {
          response,
          timestamp: Date.now()
        });
        // El resultado vendrá por action_result event
      })
      .catch((error) => {
        console.error('❌ DEBUG executeNightAction - ERROR:', {
          error: error.message,
          action,
          timestamp: Date.now()
        });
        
        clearOptimisticState();
        
        // Mostrar error al usuario
        const { setError } = get();
        setError(`Error al ejecutar acción: ${error.message}`);
      });
    
    console.log('🔍 DEBUG executeNightAction - FINAL, retornando true');
    return true; // Retorno inmediato para UX
  },
  
  getGameState: () => {
    const { emitEvent } = get();
    return emitEvent('get_game_state');
  },

  endDiscussion: () => {
    const { emitEvent } = get();
    return emitEvent('end_discussion');
  },

  submitVote: (targetPlayerId) => {
    const { emitEvent, setMyVote } = get();
    const success = emitEvent('submit_vote', { target_player_id: targetPlayerId });
    if (success) {
      setMyVote(targetPlayerId);
    }
    return success;
  },

  endVoting: () => {
    const { emitEvent } = get();
    return emitEvent('end_voting');
  },
  
  // Reset completo del estado
  reset: () => {
    // ✅ FIX: Limpiar todos los timers de debounce
    const { debounceTimers } = get();
    Object.values(debounceTimers).forEach(timer => clearTimeout(timer));
    
    set({
      debounceTimers: {},
      gameState: null,
      privateState: null,
      currentTurnDisplay: null,
      actionResult: null,
      revealData: null,
      myVote: null,
      error: null,
      logs: [],
      playerName: '',
      roomCode: '',
      selectedRoles: {},
      optimisticState: { // Reset optimistic state
        actionInProgress: false,
        optimisticActionResult: null,
        lastActionTimestamp: null
      },
      connectionState: { // Reset connection state
        isStable: true,
        reconnectAttempts: 0,
        lastDisconnectReason: null,
        lastSuccessfulPing: null
      }
    });
  }
}));
