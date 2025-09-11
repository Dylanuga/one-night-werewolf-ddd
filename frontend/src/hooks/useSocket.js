// src/hooks/useSocket.js
import { useEffect, useRef, useCallback } from 'react';
import { io } from 'socket.io-client';
import { useGameStore } from '../store/gameStore';
import { SOCKET_URL, SOCKET_EVENTS } from '../utils/constants';

export const useSocket = () => {
  const socketRef = useRef(null);
  const reconnectionDataRef = useRef({
    roomCode: null,
    playerName: null,
    wasInRoom: false
  });
  
  // Extraer funciones del store de forma estable
  const setConnectionStatus = useGameStore(state => state.setConnectionStatus);
  const setGameState = useGameStore(state => state.setGameState);
  const setPrivateState = useGameStore(state => state.setPrivateState);
  const setCurrentTurn = useGameStore(state => state.setCurrentTurn);
  const setNightAction = useGameStore(state => state.setNightAction);
  const setActionResult = useGameStore(state => state.setActionResult);
  const setError = useGameStore(state => state.setError);
  const addLog = useGameStore(state => state.addLog);
  
  // 🆕 NUEVO: Función para manejar roles seleccionados
  const setSelectedRoles = useGameStore(state => state.setSelectedRoles);
  
  // Obtener estado actual para reconexión
  const gameState = useGameStore(state => state.gameState);
  const playerName = useGameStore(state => state.playerName);

  useEffect(() => {
    console.log('🔧 useSocket INICIADO - CON SINCRONIZACIÓN DE ROLES');

    // Guardar datos para reconexión
    if (gameState?.room_code && playerName) {
      reconnectionDataRef.current = {
        roomCode: gameState.room_code,
        playerName: playerName,
        wasInRoom: true
      };
      console.log('💾 Datos guardados para reconexión:', reconnectionDataRef.current);
    }

    // Si ya hay socket conectado, no hacer nada
    if (socketRef.current?.connected) {
      console.log('✅ Socket ya conectado, saltando');
      return;
    }

    // Limpiar socket anterior si existe
    if (socketRef.current) {
      console.log('🧹 Limpiando socket anterior');
      socketRef.current.removeAllListeners();
      socketRef.current.disconnect();
    }

    console.log('🔄 Creando nuevo socket...');
    socketRef.current = io(SOCKET_URL, {
      transports: ['websocket'],
      upgrade: false,
      forceNew: true // Forzar nueva conexión
    });

    const socket = socketRef.current;

    // Evento de conexión exitosa
    socket.on('connect', () => {
      console.log('🔗 SOCKET CONECTADO:', socket.id);
      setConnectionStatus(true);
      
      // 🎯 RECONEXIÓN AUTOMÁTICA: Si estábamos en una sala, reconectarse
      if (reconnectionDataRef.current.wasInRoom) {
        console.log('🔄 INTENTANDO RECONEXIÓN AUTOMÁTICA...');
        const { roomCode, playerName: savedName } = reconnectionDataRef.current;
        
        setTimeout(() => {
          console.log('🔄 Enviando rejoin automático:', roomCode, savedName);
          socket.emit(SOCKET_EVENTS.JOIN_ROOM, { 
            room_code: roomCode, 
            name: savedName 
          });
        }, 100); // Pequeño delay para asegurar que el socket esté listo
      }
    });

    socket.on('disconnect', (reason) => {
      console.log('❌ SOCKET DESCONECTADO:', reason);
      setConnectionStatus(false);
    });

    socket.on('connect_error', (error) => {
      console.error('🔴 ERROR DE CONEXIÓN:', error);
    });

    socket.on(SOCKET_EVENTS.CONNECTED, (data) => {
      console.log('✅ Conexión confirmada:', data.socket_id);
    });

    // Eventos de sala
    socket.on(SOCKET_EVENTS.ROOM_CREATED, (data) => {
      console.log('🏠 Sala creada:', data.room_code);
      // Guardar datos para reconexión
      reconnectionDataRef.current = {
        roomCode: data.room_code,
        playerName: playerName,
        wasInRoom: true
      };
      addLog(`Sala ${data.room_code} creada`);
    });

    socket.on(SOCKET_EVENTS.ROOM_JOINED, (data) => {
      console.log('🚪 Te uniste a la sala:', data.room_code);
      // Guardar datos para reconexión
      reconnectionDataRef.current = {
        roomCode: data.room_code,
        playerName: playerName,
        wasInRoom: true
      };
      addLog(`Te uniste a la sala ${data.room_code}`);
    });

    socket.on(SOCKET_EVENTS.ROOM_LEFT, () => {
      console.log('👋 Saliste de la sala');
      // Limpiar datos de reconexión
      reconnectionDataRef.current = {
        roomCode: null,
        playerName: null,
        wasInRoom: false
      };
      addLog('Saliste de la sala');
      setGameState(null);
      setPrivateState(null);
      // 🆕 NUEVO: Limpiar roles seleccionados
      setSelectedRoles({});
    });

    // 🆕 MEJORADO: Eventos de juego con sincronización de roles
    socket.on(SOCKET_EVENTS.ROLES_SET, (data) => {
      console.log('🎭 ROLES ESTABLECIDOS POR EL HOST:', data.roles);
      
      // Convertir array de roles a objeto contador para la UI
      const roleCount = {};
      data.roles.forEach(role => {
        roleCount[role] = (roleCount[role] || 0) + 1;
      });
      
      console.log('📊 Contador de roles procesado:', roleCount);
      
      // 🎯 ACTUALIZAR ESTADO GLOBAL: Esto permitirá que todos los componentes vean los roles
      setSelectedRoles(roleCount);
      
      // Log para toda la sala
      addLog(`Host seleccionó ${data.roles.length} roles`);
      
      // 🆕 NUEVO: Emitir evento personalizado para componentes que lo necesiten
      window.dispatchEvent(new CustomEvent('rolesUpdated', { 
        detail: { roles: data.roles, roleCount } 
      }));
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
      setGameState(data);
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
      
      // 🎯 Si el error es "No estás en ninguna sala", intentar reconexión
      if (data.message.includes('No estás en ninguna sala') && reconnectionDataRef.current.wasInRoom) {
        console.log('🔄 ERROR DE SALA - Intentando reconexión...');
        setTimeout(() => {
          const { roomCode, playerName: savedName } = reconnectionDataRef.current;
          if (roomCode && savedName) {
            console.log('🔄 Reintentando join:', roomCode, savedName);
            socket.emit(SOCKET_EVENTS.JOIN_ROOM, { 
              room_code: roomCode, 
              name: savedName 
            });
          }
        }, 500);
      } else {
        setError(data.message);
      }
    });

    // Cleanup al desmontar
    return () => {
      console.log('🧹 CLEANUP useSocket');
      if (socket) {
        socket.removeAllListeners();
        socket.disconnect();
      }
    };
  }, []); // Array vacío - no dependencies

  // Funciones de emisión con useCallback
  const emitEvent = useCallback((event, data = {}) => {
    if (socketRef.current?.connected) {
      console.log('📤 Emitiendo:', event, data);
      socketRef.current.emit(event, data);
      return true;
    }
    console.warn('❌ Socket no conectado para:', event);
    return false;
  }, []);

  const createRoom = useCallback((name) => {
    console.log('🏠 Crear sala:', name);
    return emitEvent(SOCKET_EVENTS.CREATE_ROOM, { name });
  }, [emitEvent]);

  const joinRoom = useCallback((roomCode, name) => {
    console.log('🚪 Unirse a sala:', roomCode, name);
    return emitEvent(SOCKET_EVENTS.JOIN_ROOM, { room_code: roomCode, name });
  }, [emitEvent]);

  const leaveRoom = useCallback(() => {
    console.log('👋 Salir de sala');
    // 🆕 NUEVO: Limpiar roles al salir
    setSelectedRoles({});
    return emitEvent(SOCKET_EVENTS.LEAVE_ROOM);
  }, [emitEvent, setSelectedRoles]);

  const setRoles = useCallback((roles) => {
    console.log('🎭 HOST: Establecer roles:', roles);
    
    // 🆕 NUEVO: Actualizar estado local inmediatamente para el host
    const roleCount = {};
    roles.forEach(role => {
      roleCount[role] = (roleCount[role] || 0) + 1;
    });
    setSelectedRoles(roleCount);
    
    return emitEvent(SOCKET_EVENTS.SET_ROLES, { roles });
  }, [emitEvent, setSelectedRoles]);

  const startGame = useCallback(() => {
    console.log('🎮 Iniciar juego');
    return emitEvent(SOCKET_EVENTS.START_GAME);
  }, [emitEvent]);

  const executeNightAction = useCallback((action) => {
    console.log('🌙 Acción nocturna:', action);
    return emitEvent(SOCKET_EVENTS.NIGHT_ACTION, { action });
  }, [emitEvent]);

  const getGameState = useCallback(() => {
    console.log('📊 Obtener estado');
    return emitEvent(SOCKET_EVENTS.GET_GAME_STATE);
  }, [emitEvent]);

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