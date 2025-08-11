// src/store/gameStore.js
import { create } from 'zustand';

export const useGameStore = create((set, get) => ({
  // Estado de conexión
  isConnected: false,
  
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
  
  // 🔧 ACCIONES CORREGIDAS: Funciones estables que no cambian en cada render
  setConnectionStatus: (connected) => {
    set({ isConnected: connected });
  },
  
  setGameState: (state) => {
    set({ gameState: state });
  },
  
  setPrivateState: (state) => {
    set({ privateState: state });
  },
  
  setCurrentTurn: (turn) => {
    set({ currentTurn: turn });
  },
  
  setNightAction: (action) => {
    set({ nightAction: action });
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
  
  clearLogs: () => {
    set({ logs: [] });
  },
  
  setPlayerName: (name) => {
    set({ playerName: name });
  },
  
  setRoomCode: (code) => {
    set({ roomCode: code.toUpperCase() });
  },
  
  // Getters computados - estos SÍ pueden cambiar pero no afectan useSocket
  getCurrentPhase: () => {
    const { gameState, privateState } = get();
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
    const state = gameState || privateState;
    return state?.players || [];
  },
  
  getPlayerCount: () => {
    const { gameState, privateState } = get();
    const state = gameState || privateState;
    return state?.player_count || 0;
  },
  
  getRoomCode: () => {
    const { gameState, privateState } = get();
    const state = gameState || privateState;
    return state?.room_code || null;
  },
  
  getCurrentTurnRole: () => {
    const { currentTurn } = get();
    return currentTurn?.role || null;
  },
  
  canStartGame: () => {
    const { gameState, privateState } = get();
    const state = gameState || privateState;
    if (!state) return false;
    
    return (
      state.phase === 'lobby' &&
      state.player_count >= 3 &&
      state.player_count <= 8
    );
  },
  
  // Reset completo del estado
  reset: () => {
    set({
      gameState: null,
      privateState: null,
      currentTurn: null,
      nightAction: null,
      actionResult: null,
      error: null,
      logs: [],
      playerName: '',
      roomCode: ''
    });
  }
}));