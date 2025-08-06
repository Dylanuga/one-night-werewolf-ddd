// src/hooks/useSocket.js
import { useEffect, useRef } from 'react';
import { io } from 'socket.io-client';
import { useGameStore } from '../store/gameStore';
import { SOCKET_URL, SOCKET_EVENTS } from '../utils/constants';

export const useSocket = () => {
  const socketRef = useRef(null);
  const {
    setConnectionStatus,
    setGameState,
    setPrivateState,
    setCurrentTurn,
    setNightAction,
    setActionResult,
    setError,
    addLog
  } = useGameStore();

  useEffect(() => {
    // Crear conexión Socket.IO
    socketRef.current = io(SOCKET_URL, {
      transports: ['websocket'],
      upgrade: false
    });

    const socket = socketRef.current;

    // Eventos de conexión
    socket.on('connect', () => {
      console.log('🔗 Conectado al servidor');
      setConnectionStatus(true);
    });

    socket.on('disconnect', () => {
      console.log('❌ Desconectado del servidor');
      setConnectionStatus(false);
    });

    socket.on(SOCKET_EVENTS.CONNECTED, (data) => {
      console.log('✅ Conexión confirmada:', data.socket_id);
    });

    // Eventos de sala
    socket.on(SOCKET_EVENTS.ROOM_CREATED, (data) => {
      console.log('🏠 Sala creada:', data.room_code);
      addLog(`Sala ${data.room_code} creada`);
    });

    socket.on(SOCKET_EVENTS.ROOM_JOINED, (data) => {
      console.log('🚪 Te uniste a la sala:', data.room_code);
      addLog(`Te uniste a la sala ${data.room_code}`);
    });

    socket.on(SOCKET_EVENTS.ROOM_LEFT, () => {
      console.log('👋 Saliste de la sala');
      addLog('Saliste de la sala');
      setGameState(null);
      setPrivateState(null);
    });

    // Eventos de juego
    socket.on(SOCKET_EVENTS.ROLES_SET, (data) => {
      console.log('🎭 Roles establecidos:', data.roles);
      addLog('Roles seleccionados por el host');
    });

    socket.on(SOCKET_EVENTS.GAME_STARTED, () => {
      console.log('🎮 Juego iniciado');
      addLog('¡El juego ha comenzado!');
    });

    socket.on(SOCKET_EVENTS.GAME_UPDATE, (data) => {
      console.log('🔄 Actualización del juego:', data);
      setGameState(data);
    });

    socket.on(SOCKET_EVENTS.PRIVATE_UPDATE, (data) => {
      console.log('🔐 Actualización privada:', data);
      setPrivateState(data);
    });

    socket.on(SOCKET_EVENTS.TURN_START, (data) => {
      console.log('⏰ Inicio de turno:', data);
      setCurrentTurn(data);
      addLog(`--- Fase: ${data.role} ---`);
    });

    socket.on(SOCKET_EVENTS.NIGHT_ACTION, (data) => {
      console.log('🌙 Acción nocturna disponible:', data);
      setNightAction(data);
    });

    socket.on(SOCKET_EVENTS.ACTION_RESULT, (data) => {
      console.log('✨ Resultado de acción:', data);
      setActionResult(data);
    });

    socket.on(SOCKET_EVENTS.GAME_STATE, (data) => {
      console.log('📊 Estado del juego:', data);
      setGameState(data);
    });

    socket.on(SOCKET_EVENTS.ERROR, (data) => {
      console.error('❌ Error del servidor:', data.message);
      setError(data.message);
    });

    // Cleanup al desmontar
    return () => {
      if (socket) {
        socket.disconnect();
      }
    };
  }, []);

  // Funciones para emitir eventos
  const emitEvent = (event, data = {}) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit(event, data);
      return true;
    }
    console.warn('❌ Socket no conectado, no se puede emitir:', event);
    return false;
  };

  const createRoom = (name) => {
    return emitEvent(SOCKET_EVENTS.CREATE_ROOM, { name });
  };

  const joinRoom = (roomCode, name) => {
    return emitEvent(SOCKET_EVENTS.JOIN_ROOM, { room_code: roomCode, name });
  };

  const leaveRoom = () => {
    return emitEvent(SOCKET_EVENTS.LEAVE_ROOM);
  };

  const setRoles = (roles) => {
    return emitEvent(SOCKET_EVENTS.SET_ROLES, { roles });
  };

  const startGame = () => {
    return emitEvent(SOCKET_EVENTS.START_GAME);
  };

  const executeNightAction = (action) => {
    return emitEvent(SOCKET_EVENTS.NIGHT_ACTION, { action });
  };

  const getGameState = () => {
    return emitEvent(SOCKET_EVENTS.GET_GAME_STATE);
  };

  return {
    isConnected: socketRef.current?.connected || false,
    createRoom,
    joinRoom,
    leaveRoom,
    setRoles,
    startGame,
    executeNightAction,
    getGameState
  };
};