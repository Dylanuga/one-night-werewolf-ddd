// src/store/gameStore.js
import { create } from 'zustand';

export const useGameStore = create((set, get) => ({
  // Estado de conexión y socket
  isConnected: false,
  socket: null,
  
  // Estado del juego público
  gameState: null,
  
  // Estado privado del jugador
  privateState: null,
  
  // Información del turno actual
  currentTurn: null,
  
  // Acción nocturna disponible
  nightAction: null,
  
  // Resultado de la última acción
  actionResult: null,
  
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
  
  setConnectionStatus: (connected) => set({ isConnected: connected }),
  
  setGameState: (state) => set({ gameState: state }),
  
  setPrivateState: (state) => set({ privateState: state }),
  
  setCurrentTurn: (turn) => {
    console.log('🎮 Actualizando currentTurn:', turn);
    set({ currentTurn: turn });
    
    // Sincronizar con privateState para evitar inconsistencias
    const currentPrivateState = get().privateState;
    if (currentPrivateState) {
      set({ 
        privateState: {
          ...currentPrivateState,
          current_turn_role: turn?.role
        }
      });
    }
  },
  
  setNightAction: (action) => {
    console.log('🌙 Actualizando nightAction:', action);
    set({ nightAction: action });
    
    // Sincronizar con privateState para evitar inconsistencias
    const currentPrivateState = get().privateState;
    if (currentPrivateState) {
      set({ 
        privateState: {
          ...currentPrivateState,
          night_action: action
        }
      });
    }
  },
  
  setActionResult: (result) => {
    set({ actionResult: result });
    // Auto-limpiar después de 3 segundos
    setTimeout(() => {
      set({ actionResult: null });
    }, 3000);
  },
  
  setError: (error) => {
    set({ error });
    // Auto-limpiar después de 5 segundos
    setTimeout(() => {
      set({ error: null });
    }, 5000);
  },
  
  addLog: (message) => {
    const timestamp = new Date().toLocaleTimeString();
    set(state => ({
      logs: [...state.logs, { timestamp, message }].slice(-20) // Máximo 20 logs
    }));
  },
  
  clearLogs: () => set({ logs: [] }),
  
  setPlayerName: (name) => set({ playerName: name }),
  
  setRoomCode: (code) => set({ roomCode: code.toUpperCase() }),
  
  // 🆕 NUEVO: Acciones para roles seleccionados
  setSelectedRoles: (roles) => {
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
  
  isMyTurn: () => {
    const { privateState } = get();
    return privateState?.is_your_turn || false;
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
    const { currentTurn } = get();
    return currentTurn?.role || null;
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
  
  // 🆕 NUEVO: Funciones de emisión de eventos a través del socket centralizado
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
    const { emitEvent } = get();
    return emitEvent('night_action', { action });
  },
  
  getGameState: () => {
    const { emitEvent } = get();
    return emitEvent('get_game_state');
  },
  
  // Reset completo del estado
  reset: () => set({
    gameState: null,
    privateState: null,
    currentTurn: null,
    nightAction: null,
    actionResult: null,
    error: null,
    logs: [],
    playerName: '',
    roomCode: '',
    selectedRoles: {} // 🆕 NUEVO: También resetear roles
  })
}));