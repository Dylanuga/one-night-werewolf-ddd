// src/store/gameStore.js
import { create } from 'zustand';
import { ROLES } from '../utils/constants';

// Funciones de persistencia de sesión en navegador móvil/escritorio
export const getStoredSession = () => {
  try {
    const raw = sessionStorage.getItem('werewolf_session');
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    return null;
  }
};

export const saveSession = (roomCode, playerName, playerId = null, isHost = false) => {
  try {
    sessionStorage.setItem('werewolf_session', JSON.stringify({
      roomCode: roomCode ? roomCode.toUpperCase() : '',
      playerName: playerName || '',
      playerId,
      isHost,
      savedAt: Date.now()
    }));
  } catch (e) {
    console.warn('No se pudo guardar la sesión en sessionStorage', e);
  }
};

export const clearSession = () => {
  try {
    sessionStorage.removeItem('werewolf_session');
  } catch (e) {
    console.warn('No se pudo limpiar la sesión', e);
  }
};

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

const initialSession = getStoredSession();

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
  nightNotes: {
    werewolf: null,
    mason: null,
    seer: null
  },
  
  // Errores
  error: null,
  
  // Logs del juego
  logs: [],
  
  // Estado del formulario de entrada
  playerName: initialSession?.playerName || '',
  roomCode: initialSession?.roomCode || '',
  discussionDuration: 300, // 5 minutos por defecto (120, 300, 600)
  setDiscussionDuration: (sec) => set({ discussionDuration: sec }),
  
  // 🆕 NUEVO: Estado de roles seleccionados (para sincronización en tiempo real)
  selectedRoles: {},
  showRoleSelector: false,
  setShowRoleSelector: (show) => set({ showRoleSelector: show }),
  
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
    if (current && deepEqual(current, state)) {
      console.log('🔄 setPrivateState: Sin cambios detectados, ignorando');
      return;
    }

    // ✅ CRÍTICO: Actualización simple sin timestamps aleatorios
    set(prevState => {
      const updatedNotes = { ...(prevState.nightNotes || {}) };

      if (state.seer_last_result) {
        const sr = state.seer_last_result;
        const autoPrefix = sr.auto ? '🎲 (Aleatoria) ' : '';
        if (sr.seen_player) {
          const roleName = ROLES[sr.seen_player.role]?.name || sr.seen_player.role;
          updatedNotes.seer = `${autoPrefix}Viste el rol de ${sr.seen_player.name || sr.seen_player.player_id}: ${roleName}`;
        } else if (Array.isArray(sr.seen_center)) {
          const positions = ['Izquierda', 'Centro', 'Derecha'];
          const formatted = sr.seen_center
            .map(c => `${positions[c.position] || `Pos ${c.position + 1}`}: ${ROLES[c.role]?.name || c.role}`)
            .join(' | ');
          updatedNotes.seer = `${autoPrefix}Cartas del centro vistas: ${formatted}`;
        }
      }

      if (state.werewolf_last_center) {
        const wc = state.werewolf_last_center;
        const autoPrefix = wc.auto ? '🎲 (Aleatoria) ' : '';
        const pos = wc.center_position ?? wc.position ?? 0;
        const role = wc.center_role ?? wc.role;
        const posLabel = ['Izquierda', 'Centro', 'Derecha'][pos] || `Posición ${pos + 1}`;
        const roleName = ROLES[role]?.name || role;
        updatedNotes.werewolf = `${autoPrefix}Lobo solitario - Carta del centro (${posLabel}): ${roleName}`;
      }

      const newState = {
        ...prevState,
        privateState: state, // Usar el estado tal como viene del servidor
        nightNotes: updatedNotes
      };
      
      console.log('🔍 DEBUG setPrivateState - ESTADO ANTES:', prevState.privateState);
      console.log('🔍 DEBUG setPrivateState - ESTADO DESPUÉS:', newState.privateState);
      
      return newState;
    });

    console.log('🔍 DEBUG setPrivateState - FINAL:', get().privateState);
  },
  
  setCurrentTurnDisplay: (turn) => {
    const current = get().currentTurnDisplay;
    if (current && turn &&
        current.role === turn.role && 
        current.phase === turn.phase &&
        current.duration === turn.duration &&
        current.timestamp === turn.timestamp &&
        current.end_timestamp === turn.end_timestamp &&
        current.remaining === turn.remaining) {
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

    const currentResult = get().actionResult;
    if (currentResult && result) {
      const { _timestamp: _t1, ...cleanCurrent } = currentResult;
      const { _timestamp: _t2, ...cleanNext } = result;
      if (deepEqual(cleanCurrent, cleanNext)) {
        console.log('🔄 setActionResult: Sin cambios detectados, ignorando');
        return;
      }
    } else if (currentResult === result) {
      console.log('🔄 setActionResult: Misma referencia, ignorando');
      return;
    }
    
    // ✅ CRÍTICO: Actualización inmutable para forzar re-render y sincronizar notas nocturnas
    set(state => {
      const updatedNotes = { ...(state.nightNotes || {}) };
      if (result) {
        const autoPrefix = result.auto ? '🎲 (Aleatoria) ' : '';
        if (result.seen_player) {
          const roleName = ROLES[result.seen_player.role]?.name || result.seen_player.role;
          updatedNotes.seer = `${autoPrefix}Viste el rol de ${result.seen_player.name || result.seen_player.player_id}: ${roleName}`;
        } else if (Array.isArray(result.seen_center)) {
          const positions = ['Izquierda', 'Centro', 'Derecha'];
          const formatted = result.seen_center
            .map(c => `${positions[c.position] || `Pos ${c.position + 1}`}: ${ROLES[c.role]?.name || c.role}`)
            .join(' | ');
          updatedNotes.seer = `${autoPrefix}Cartas del centro vistas: ${formatted}`;
        } else if (result.center_role !== undefined && result.center_position !== undefined) {
          const posLabel = ['Izquierda', 'Centro', 'Derecha'][result.center_position] || `Posición ${result.center_position + 1}`;
          const roleName = ROLES[result.center_role]?.name || result.center_role;
          updatedNotes.werewolf = `${autoPrefix}Lobo solitario - Carta del centro (${posLabel}): ${roleName}`;
        }
      }

      const newState = {
        ...state,
        actionResult: result ? { ...result, _timestamp: Date.now() } : null,
        nightNotes: updatedNotes
      };
      
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
  },

  setRevealData: (data) => {
    const current = get().revealData;
    if (current === data) return;
    set({ revealData: data });
  },

  setMyVote: (vote) => set({ myVote: vote }),

  setNightNote: (role, note) => {
    if (!role) return;
    const current = get().nightNotes?.[role] || null;
    if (current === note) return;
    set(state => ({
      nightNotes: {
        ...state.nightNotes,
        [role]: note
      }
    }));
  },

  clearNightNotes: () => set({
    nightNotes: {
      werewolf: null,
      mason: null,
      seer: null
    }
  }),
  
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
  
  getCurrentPhase: () => {
    const { gameState, privateState } = get();
    const gamePhase = gameState?.phase;
    const privatePhase = privateState?.phase;
    
    // Las fases activas de juego tienen prioridad absoluta sobre lobby o role_selection
    const activePhases = ['night_phase', 'day_phase', 'voting', 'game_end'];
    if (activePhases.includes(privatePhase)) return privatePhase;
    if (activePhases.includes(gamePhase)) return gamePhase;
    
    return gamePhase || privatePhase || 'lobby';
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
    const { emitEvent, setPlayerName } = get();
    setPlayerName(name);
    return emitEvent('create_room', { name });
  },
  
  joinRoom: (roomCode, name) => {
    const { emitEvent, setRoomCode, setPlayerName } = get();
    setRoomCode(roomCode);
    setPlayerName(name);
    saveSession(roomCode, name);
    return emitEvent('join_room', { room_code: roomCode, name });
  },
  
  reconnectSession: (roomCode, playerName, playerId = null) => {
    const { emitEvent } = get();
    return emitEvent('reconnect_session', {
      room_code: roomCode,
      player_name: playerName,
      player_id: playerId
    });
  },

  setDiscussionTimer: (duration) => {
    const { emitEvent } = get();
    set({ discussionDuration: duration });
    return emitEvent('set_discussion_timer', { duration });
  },

  leaveRoom: () => {
    const { emitEvent, setSelectedRoles, roomCode, playerName } = get();
    clearSession();
    setSelectedRoles({});
    return emitEvent('leave_room', { room_code: roomCode, player_name: playerName });
  },
  
  setRoles: (roles, customDuration = null) => {
    const { emitEvent, setSelectedRoles, discussionDuration } = get();
    const roleCount = {};
    roles.forEach(role => {
      roleCount[role] = (roleCount[role] || 0) + 1;
    });
    setSelectedRoles(roleCount);
    const duration = customDuration || discussionDuration;
    return emitEvent('set_roles', { roles, discussion_duration: duration });
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

  resetGame: (toPhase) => {
    const { emitEvent, gameState, privateState } = get();
    const updates = { showRoleSelector: false };
    if (toPhase === 'lobby') {
      updates.selectedRoles = {};
      if (gameState) {
        updates.gameState = { ...gameState, phase: 'lobby', selected_roles: [], selected_roles_count: 0 };
      }
      if (privateState) {
        updates.privateState = { ...privateState, phase: 'lobby', selected_roles: [], selected_roles_count: 0 };
      }
    }
    set(updates);
    return emitEvent('reset_game', { to_phase: toPhase });
  },

  handleGameReset: (toPhase) => {
    const updates = {
      revealData: null,
      myVote: null,
      actionResult: null,
      nightNotes: {
        werewolf: null,
        mason: null,
        seer: null
      },
      error: null,
      showRoleSelector: false
    };
    if (toPhase === 'lobby') {
      updates.selectedRoles = {};
    }
    set(updates);
  },
  
  // Reset completo del estado
  reset: () => {
    clearSession();
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
      nightNotes: {
        werewolf: null,
        mason: null,
        seer: null
      },
      error: null,
      logs: [],
      playerName: '',
      roomCode: '',
      selectedRoles: {},
      showRoleSelector: false,
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
