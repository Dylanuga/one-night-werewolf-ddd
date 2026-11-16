// src/hooks/useGameSocket.js
import { useEffect, useRef } from 'react';
import { io } from 'socket.io-client';
import { useGameStore, getStoredSession, saveSession, clearSession } from '../store/gameStore';
import { SOCKET_URL, SOCKET_EVENTS } from '../utils/constants';

export const useGameSocket = () => {
  const {
    gameState,
    isConnected,
    setSocket,
    setConnectionStatus,
    setGameState,
    setPrivateState,
    setCurrentTurnDisplay,
    setActionResult,
    setRevealData,
    setMyVote,
    setError,
    handleGameReset,
    clearNightNotes,
    addLog,
    setSelectedRoles,
    setPlayerName,
    setRoomCode,
    emitEvent,
    emitEventWithRetry,
    createRoom,
    joinRoom,
    leaveRoom,
    setRoles,
    setDiscussionTimer,
    startGame,
    executeNightAction,
    endDiscussion,
    submitVote,
    endVoting,
    resetGame,
    getGameState,
    reconnectSession
  } = useGameStore();

  const socketRef = useRef(null);
  const isInitializedRef = useRef(false);
  const autoJoinRef = useRef(false);

  // Auto-join por URL (?autoJoin=1&room=TEST&name=Player1)
  useEffect(() => {
    if (!isConnected || autoJoinRef.current) return;

    const params = new URLSearchParams(window.location.search);
    const autoJoin = params.get('autoJoin') === '1';
    const room = params.get('room');
    const name = params.get('name');

    if (autoJoin && room && name && !gameState?.room_code) {
      autoJoinRef.current = true;
      setPlayerName(name);
      setRoomCode(room);
      joinRoom(room, name);
      addLog(`Auto-join: ${name} -> ${room}`);
    }
  }, [isConnected, gameState?.room_code, setPlayerName, setRoomCode, joinRoom, addLog]);

  // Inicialización centralizada del socket y suscripción a eventos
  useEffect(() => {
    console.log('🔧 useGameSocket - Inicializando socket centralizado');

    // Prevenir múltiples inicializaciones
    if (isInitializedRef.current) {
      console.log('✅ Socket ya inicializado, saltando');
      return;
    }

    // Si ya hay socket conectado, solo actualizar estado
    if (socketRef.current?.connected) {
      console.log('✅ Socket ya conectado, actualizando estado');
      setConnectionStatus(true);
      return;
    }

    console.log('🔌 Creando nueva conexión socket...');
    isInitializedRef.current = true;

    socketRef.current = io(SOCKET_URL, {
      transports: ['websocket', 'polling'],
      upgrade: true,
      autoConnect: true,
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      timeout: 20000,
      forceNew: false
    });

    const socket = socketRef.current;
    setSocket(socket); // Guardar la instancia en el store

    // Función para auto-recuperar sesión si el usuario cambió de app o perdió conexión
    const tryAutoReconnect = () => {
      const state = useGameStore.getState();
      const stored = getStoredSession();
      const room = state.roomCode || stored?.roomCode;
      const name = state.playerName || stored?.playerName;
      const pid = stored?.playerId;

      if (room && name) {
        console.log('🔄 Intentando auto-reconexión a sala:', { room, name, pid, socketId: socket.id });
        socket.emit('reconnect_session', {
          room_code: room,
          player_name: name,
          player_id: pid
        });
      }
    };

    // Eventos básicos de conexión
    socket.on('connect', () => {
      console.log('🔗 SOCKET CONECTADO:', socket.id);
      console.log('🔍 Socket conectado exitosamente');
      setConnectionStatus(true);
      tryAutoReconnect();
    });

    socket.on('disconnect', (reason) => {
      console.log('❌ SOCKET DESCONECTADO:', reason);
      console.warn('🔌 DESCONECTADO DEL SERVIDOR:', reason);
      setConnectionStatus(false);

      if (reason === 'io server disconnect') {
        console.log('⚠️ Servidor desconectó el cliente - posible reinicio');
        console.error('❌ El servidor forzó la desconexión');
      } else if (reason === 'io client disconnect') {
        console.log('⚠️ Cliente desconectó deliberadamente');
      } else if (reason === 'ping timeout') {
        console.log('⚠️ Timeout de ping - problemas de red');
      } else if (reason === 'transport close') {
        console.log('⚠️ Transporte cerrado - problemas de conexión');
      } else if (reason === 'transport error') {
        console.log('⚠️ Error de transporte');
      }
    });

    socket.on('reconnect', (attemptNumber) => {
      console.log('🔄 SOCKET RECONECTADO después de', attemptNumber, 'intentos');
      setConnectionStatus(true);
      addLog(`Reconectado tras ${attemptNumber} intentos`);
      tryAutoReconnect();
    });

    socket.on('reconnect_attempt', (attemptNumber) => {
      console.log('🔄 Intento de reconexión #', attemptNumber);
    });

    // 🔍 DEBUG: Heartbeat para verificar comunicación WebSocket
    const heartbeatInterval = setInterval(() => {
      if (socket.connected) {
        console.log('💓 Heartbeat - Socket conectado, enviando ping...');
        console.log('🔍 Socket status:', { connected: socket.connected, id: socket.id });
        socket.emit('ping', { timestamp: Date.now() });
      } else {
        console.log('💔 Heartbeat - Socket DESCONECTADO');
      }
    }, 10000); // Cada 10 segundos

    socket.on('pong', (data) => {
      console.log('💓 Pong recibido:', data);
    });

    socket.on('reconnect_error', (error) => {
      console.error('❌ Error de reconexión:', error);
    });

    socket.on('reconnect_failed', (data) => {
      if (!data) {
        console.error('💀 Falló la reconexión definitivamente');
        setError('No se pudo reconectar al servidor');
        return;
      }

      console.warn('⚠️ No se pudo reanudar sesión previa:', data?.message);
      clearSession();
      if (useGameStore.getState().gameState) {
        setError(data?.message || 'Tu sesión anterior ya no es válida');
        setGameState(null);
        setPrivateState(null);
      }
    });

    socket.on('connect_error', (error) => {
      console.error('🔴 ERROR DE CONEXIÓN:', error);
      setConnectionStatus(false);
    });

    // Eventos del servidor
    socket.on(SOCKET_EVENTS.CONNECTED, (data) => {
      console.log('✅ Conexión confirmada:', data.socket_id);
    });

    // Eventos de sesión y reconexión
    socket.on('reconnected_success', (data) => {
      console.log('🎉 Sesión recuperada exitosamente:', data);
      addLog(`Sesión recuperada en sala ${data.room_code}`);
      saveSession(data.room_code, data.player_name, data.player_id, data.is_host);
      setRoomCode(data.room_code);
      setPlayerName(data.player_name);
    });

    socket.on('timer_settings_updated', (data) => {
      console.log('⏱️ Configuración de temporizador recibida:', data);
      if (data?.discussion_duration) {
        useGameStore.getState().setDiscussionDuration(data.discussion_duration);
        addLog(`Tiempo de debate: ${Math.round(data.discussion_duration / 60)} min`);
      }
    });

    // Eventos de sala
    socket.on(SOCKET_EVENTS.ROOM_CREATED, (data) => {
      console.log('🏠 Sala creada:', data.room_code);
      saveSession(data.room_code, useGameStore.getState().playerName, null, true);
      setRoomCode(data.room_code);
      addLog(`Sala ${data.room_code} creada`);
      console.log('⏳ Esperando eventos game_update y private_update...');
    });

    socket.on(SOCKET_EVENTS.ROOM_JOINED, (data) => {
      console.log('🚪 Te uniste a la sala:', data.room_code);
      saveSession(data.room_code, useGameStore.getState().playerName);
      setRoomCode(data.room_code);
      addLog(`Te uniste a la sala ${data.room_code}`);
    });

    socket.on(SOCKET_EVENTS.ROOM_LEFT, () => {
      console.log('👋 Saliste de la sala');
      clearSession();
      addLog('Saliste de la sala');
      setGameState(null);
      setPrivateState(null);
      setSelectedRoles({});
      setRevealData(null);
      setMyVote(null);
    });

    // Eventos de juego
    socket.on(SOCKET_EVENTS.ROLES_SET, (data) => {
      console.log('🎭 ROLES ESTABLECIDOS:', data.roles);

      const roleCount = {};
      data.roles.forEach(role => {
        roleCount[role] = (roleCount[role] || 0) + 1;
      });

      setSelectedRoles(roleCount);
      addLog(`Host seleccionó ${data.roles.length} roles`);
    });

    socket.on(SOCKET_EVENTS.GAME_STARTED, (data) => {
      console.log('🎮 Juego iniciado:', data);
      useGameStore.getState().setShowRoleSelector(false);
      setActionResult(null);
      clearNightNotes();
      console.log('🔧 Estado actual antes de GAME_STARTED:', {
        socketConnected: socket.connected,
        gameState: useGameStore.getState().gameState,
        privateState: useGameStore.getState().privateState
      });
      addLog('¡El juego ha comenzado!');
    });

    socket.on(SOCKET_EVENTS.GAME_UPDATE, (data) => {
      console.log('🔄 Actualización del juego recibida:', data);
      console.log('⏰ Timestamp del evento game_update:', Date.now());
      console.log('🔧 Verificando si GAME_UPDATE causa problemas:', {
        dataPhase: data?.phase,
        socketConnected: socket.connected,
        timestamp: Date.now()
      });
      console.log('🔍 Estado previo antes de aplicar game_update:', {
        gameState: useGameStore.getState().gameState,
        privateState: useGameStore.getState().privateState
      });

      setGameState(data);
    });

    socket.on(SOCKET_EVENTS.PRIVATE_UPDATE, (data) => {
      setPrivateState(data);
    });

    socket.on(SOCKET_EVENTS.TURN_START, (data) => {
      console.log('⏰ Inicio de turno recibido:', data);
      useGameStore.getState().setShowRoleSelector(false);

      // ✅ ARQUITECTURA UNIFICADA: TURN_START ahora es solo para UI visual
      // Los datos funcionales (privateState) llegan via PRIVATE_UPDATE unificado
      // No hay race condition porque el backend envía ambos de manera atómica

      console.log('🔍 TURN_START listener - FUNCIONANDO para rol:', data.role);
      console.log('🔍 Socket conectado:', socket.connected);

      const currentTime = new Date().toISOString();
      console.log(`⏰ [${currentTime}] TURN_START recibido para rol: ${data.role}`);
      console.log(`🔧 Estado del socket: conectado=${socket.connected}, id=${socket.id}`);
      console.log('🔧 Estado actual antes del cambio:', {
        currentTurnRole: useGameStore.getState().privateState?.current_turn_role,
        gamePhase: useGameStore.getState().gameState?.phase
      });

      try {
        setCurrentTurnDisplay(data);
        addLog(`--- Fase: ${data.role} comenzó ---`);
        console.log('✅ TURN_START procesado exitosamente para:', data.role);
      } catch (error) {
        console.error('❌ ERROR procesando TURN_START:', error);
      }

      // Forzar actualización de privateState para mayor robustez
      const currentPrivateState = useGameStore.getState().privateState;
      if (currentPrivateState) {
        const initialRole = currentPrivateState.your_original_role || currentPrivateState.your_role;
        const isYourTurn = data.role !== 'open_eyes' && initialRole === data.role;

        const updatedPrivateState = {
          ...currentPrivateState,
          current_turn_role: data.role,
          is_your_turn: isYourTurn,
          ...(data.timestamp !== undefined ? { turn_timestamp: data.timestamp } : {}),
          ...(data.end_timestamp !== undefined ? { turn_end_timestamp: data.end_timestamp } : {}),
          ...(data.duration !== undefined ? { turn_duration: data.duration } : {}),
          ...(data.remaining !== undefined ? { turn_remaining: data.remaining } : {}),
          ...(data.server_time !== undefined ? { server_time: data.server_time } : {})
        };

        console.log('🔄 Actualizando privateState con nuevo turno:', {
          role: data.role,
          isYourTurn
        });

        setPrivateState(updatedPrivateState);
      }
    });

    socket.on(SOCKET_EVENTS.NIGHT_ACTION, (data) => {
      console.log('🌙 Acción nocturna disponible:', data);

      const currentPrivateState = useGameStore.getState().privateState;
      if (currentPrivateState) {
        setPrivateState({
          ...currentPrivateState,
          night_action: data,
          is_your_turn: true
        });
      }
    });

    socket.on(SOCKET_EVENTS.ACTION_RESULT, (data) => {
      console.log('✨ Resultado de acción:', data);
      setActionResult(data);
    });

    socket.on(SOCKET_EVENTS.VOTING_STARTED, (data) => {
      console.log('🗳️ Votación iniciada:', data);
      setMyVote(null);
      addLog('Votación iniciada');
    });

    socket.on(SOCKET_EVENTS.VOTE_RECEIVED, () => {
      console.log('🗳️ Voto recibido');
    });

    socket.on(SOCKET_EVENTS.REVEAL, (data) => {
      console.log('🏁 Revelación:', data);
      setRevealData(data);
    });

    socket.on(SOCKET_EVENTS.GAME_END, (data) => {
      console.log('🏁 Fin de partida:', data);
      setRevealData(data);
    });

    socket.on(SOCKET_EVENTS.GAME_RESET, (data) => {
      console.log('🔄 Partida reiniciada por el host:', data);
      handleGameReset(data?.to_phase);
      useGameStore.getState().setShowRoleSelector(false);
    });

    socket.on(SOCKET_EVENTS.GAME_STATE, (data) => {
      console.log('📊 Estado del juego:', data);
      setGameState(data);
    });

    socket.on(SOCKET_EVENTS.ERROR, (data) => {
      console.error('❌ Error del servidor:', data.message);
      setError(data.message);
    });

    // Escuchar cuando el usuario vuelve a la pestaña del navegador (ej: tras WhatsApp o llamada)
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        console.log('📱 App volvió a primer plano en navegador');
        if (socket.connected) {
          tryAutoReconnect();
        } else {
          socket.connect();
        }
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Cleanup al desmontar
    return () => {
      console.log('🧹 CLEANUP useGameSocket - Desmontando conexión');
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
        console.log('🧹 Heartbeat interval limpiado');
      }
      if (socket) {
        socket.removeAllListeners();
        socket.disconnect();
      }
      isInitializedRef.current = false;
    };
  }, []); // SIN dependencias - solo se ejecuta una vez al montar

  return {
    socket: socketRef.current,
    isConnected,
    emitEvent,
    emitEventWithRetry,
    createRoom,
    joinRoom,
    leaveRoom,
    setRoles,
    setDiscussionTimer,
    startGame,
    executeNightAction,
    endDiscussion,
    submitVote,
    endVoting,
    resetGame,
    getGameState,
    reconnectSession
  };
};

