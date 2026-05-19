// src/App.jsx
import React, { useEffect, useState, useRef } from 'react';
import { io } from 'socket.io-client';
import { useGameStore } from './store/gameStore';
import { Lobby } from './components/Lobby';
import { RoleSelector } from './components/RoleSelector';
import { NightPhase } from './components/NightPhase';
import { DayPhase } from './components/DayPhase';
import { VotingPhase } from './components/VotingPhase';
import { RevealPhase } from './components/RevealPhase';
import { GameLog } from './components/GameLog';
import TestingPanel from './components/TestingPanel';
import { GAME_PHASES, SOCKET_URL, SOCKET_EVENTS } from './utils/constants';
import { AlertCircle, TestTube } from 'lucide-react';

function App() {
  const {
    gameState,
    privateState,
    playerName,
    error,
    isConnected,
    getCurrentPhase,
    reset,
    // Nuevas funciones del store
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
    addLog,
    setSelectedRoles,
    setPlayerName,
    setRoomCode,
    joinRoom
  } = useGameStore();

  const socketRef = useRef(null);
  const isInitializedRef = useRef(false);
  
  const [showRoleSelector, setShowRoleSelector] = useState(false);
  const [showError, setShowError] = useState(false);
  const [showTestingPanel, setShowTestingPanel] = useState(false);
  const autoJoinRef = useRef(false);

  const currentPhase = getCurrentPhase();

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

  // 🔧 NUEVA LÓGICA: Inicialización centralizada del socket
  useEffect(() => {
    console.log('🔧 App - Inicializando socket centralizado');

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

    // Eventos básicos de conexión
    socket.on('connect', () => {
      console.log('🔗 SOCKET CONECTADO:', socket.id);
      console.log('🔍 Socket conectado exitosamente');
      setConnectionStatus(true);
    });

    socket.on('disconnect', (reason) => {
      console.log('❌ SOCKET DESCONECTADO:', reason);
      setConnectionStatus(false);
      
      // Log específico para diferentes tipos de desconexión
      if (reason === 'io server disconnect') {
        console.log('⚠️ Servidor desconectó el cliente - posible reinicio');
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

    socket.on('disconnect', (reason) => {
      console.warn('🔌 DESCONECTADO DEL SERVIDOR:', reason);
      setConnectionStatus(false);
      if (reason === 'io server disconnect') {
        // Desconexión iniciada por el servidor
        console.error('❌ El servidor forzó la desconexión');
      }
    });

    socket.on('reconnect_failed', () => {
      console.error('💀 Falló la reconexión definitivamente');
      setError('No se pudo reconectar al servidor');
    });

    socket.on('connect_error', (error) => {
      console.error('🔴 ERROR DE CONEXIÓN:', error);
      setConnectionStatus(false);
    });

    // Eventos del servidor
    socket.on(SOCKET_EVENTS.CONNECTED, (data) => {
      console.log('✅ Conexión confirmada:', data.socket_id);
    });

    // Eventos de sala
    socket.on(SOCKET_EVENTS.ROOM_CREATED, (data) => {
      console.log('🏠 Sala creada:', data.room_code);
      console.log('🔍 Datos completos del evento room_created:', data);
      console.log('🔍 Estado actual del store antes de room_created:', {
        gameState: useGameStore.getState().gameState,
        privateState: useGameStore.getState().privateState
      });
      addLog(`Sala ${data.room_code} creada`);
      
      // 🔧 NUEVO: Aguardar los eventos private_update y game_update que deberían llegar después
      console.log('⏳ Esperando eventos game_update y private_update...');
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
      console.log('🔧 Estado actual antes de GAME_STARTED:', {
        socketConnected: socket.connected,
        gameState: useGameStore.getState().gameState,
        privateState: useGameStore.getState().privateState
      });
      addLog('¡El juego ha comenzado!');
    });

    socket.on(SOCKET_EVENTS.GAME_UPDATE, (data) => {
      console.log('🔄 Actualización del juego recibida:', data);
      console.log('� Timestamp del evento game_update:', Date.now());
      console.log('�🔧 Verificando si GAME_UPDATE causa problemas:', {
        dataPhase: data?.phase,
        socketConnected: socket.connected,
        timestamp: Date.now()
      });
      console.log('🔍 Estado previo antes de aplicar game_update:', {
        gameState: useGameStore.getState().gameState,
        privateState: useGameStore.getState().privateState
      });
      
      setGameState(data);
      
      setTimeout(() => {
        console.log('[DEBUG] Estado final del store después de game_update:', {
          gameState: useGameStore.getState().gameState,
          privateState: useGameStore.getState().privateState
        });
      }, 0);
    });

    socket.on(SOCKET_EVENTS.PRIVATE_UPDATE, (data) => {
      console.log('🔐 Actualización privada recibida:', data);
      console.log('🔍 Timestamp del evento private_update:', Date.now());
      console.log('🔍 Estado previo antes de aplicar private_update:', {
        gameState: useGameStore.getState().gameState,
        privateState: useGameStore.getState().privateState
      });
      
      setPrivateState(data);
      // Si gameState es null (ej: tras crear sala o unirse), inicializarlo con privateState
      if (!useGameStore.getState().gameState) {
        console.log('🔧 gameState es null, inicializando con privateState');
        setGameState(data);
      }
      
      // Log extra para depuración
      setTimeout(() => {
        console.log('[DEBUG] Nuevo privateState aplicado:', data);
        console.log('[DEBUG] Estado final del store después de private_update:', {
          gameState: useGameStore.getState().gameState,
          privateState: useGameStore.getState().privateState
        });
      }, 0);
    });

    socket.on(SOCKET_EVENTS.TURN_START, (data) => {
      console.log('⏰ Inicio de turno recibido:', data);
      
      // ✅ ARQUITECTURA UNIFICADA: TURN_START ahora es solo para UI visual
      // Los datos funcionales (privateState) llegan via PRIVATE_UPDATE unificado
      // No hay race condition porque el backend envía ambos de manera atómica
      
      console.log('🔍 TURN_START listener - FUNCIONANDO para rol:', data.role);
      console.log('🔍 Socket conectado:', socket.connected);
      
      // Registrar recepción del evento con su timestamp
      const currentTime = new Date().toISOString();
      console.log(`⏰ [${currentTime}] TURN_START recibido para rol: ${data.role}`);
      
      console.log(`🔧 Estado del socket: conectado=${socket.connected}, id=${socket.id}`);
      console.log(`🔧 Estado actual antes del cambio:`, {
        currentTurnRole: useGameStore.getState().privateState?.current_turn_role,
        gamePhase: useGameStore.getState().gameState?.phase
      });
      
      try {
        // 🔧 FIX CRÍTICO: Usar setCurrentTurnDisplay que SÍ existe en gameStore
        setCurrentTurnDisplay(data);
        
        // Añadir al log para que el usuario vea el cambio
        addLog(`--- Fase: ${data.role} comenzó ---`);
        
        console.log('✅ TURN_START procesado exitosamente para:', data.role);
      } catch (error) {
        console.error('❌ ERROR procesando TURN_START:', error);
      }
      
      // Forzar actualización de privateState para mayor robustez
      const currentPrivateState = useGameStore.getState().privateState;
      if (currentPrivateState) {
        const isYourTurn = currentPrivateState.your_role === data.role;
        
        // Actualizar privateState con el nuevo turno y estado is_your_turn
        const updatedPrivateState = {
          ...currentPrivateState,
          current_turn_role: data.role,
          is_your_turn: isYourTurn
        };
        
        console.log('🔄 Actualizando privateState con nuevo turno:', {
          role: data.role,
          isYourTurn: isYourTurn
        });
        
        // Aplicar la actualización
        setPrivateState(updatedPrivateState);
      }
    });

    socket.on(SOCKET_EVENTS.NIGHT_ACTION, (data) => {
      console.log('🌙 Acción nocturna disponible:', data);
      
      // 🔧 FIX: Actualizar privateState en lugar de usar setNightAction que no existe
      const currentPrivateState = useGameStore.getState().privateState;
      if (currentPrivateState) {
        setPrivateState({
          ...currentPrivateState,
          night_action: data,
          is_your_turn: true  // Si recibe night_action, es definitivamente su turno
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

    socket.on(SOCKET_EVENTS.GAME_RESET, () => {
      console.log('🔄 Partida reiniciada por el host');
      handleGameReset();
    });

    socket.on(SOCKET_EVENTS.GAME_STATE, (data) => {
      console.log('📊 Estado del juego:', data);
      setGameState(data);
    });

    socket.on(SOCKET_EVENTS.ERROR, (data) => {
      console.error('❌ Error del servidor:', data.message);
      setError(data.message);
    });

    // Cleanup SOLO al desmontar el componente App
    return () => {
      console.log('🧹 CLEANUP App - Desmontando aplicación');
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
  }, []); // SIN dependencias - solo se ejecuta una vez al montar App

  // 🔧 NUEVA LÓGICA: Determinar si el usuario actual es host
  const players = gameState?.players || [];
  const currentPlayerName = playerName;
  const hostPlayer = players.find(p => p.is_host);
  const isCurrentUserHost = hostPlayer && hostPlayer.name === currentPlayerName;

  // Manejar errores con auto-hide
  useEffect(() => {
    if (error) {
      setShowError(true);
      const timer = setTimeout(() => {
        setShowError(false);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  // Debug: Log de cambios de estado
  useEffect(() => {
    console.log('Estado del juego actualizado:', {
      phase: currentPhase,
      gameState,
      privateState,
      isCurrentUserHost,
      hostPlayer: hostPlayer?.name
    });
  }, [currentPhase, gameState, privateState, isCurrentUserHost, hostPlayer]);

  const handleShowRoleSelector = () => {
    // 🔧 CRÍTICO: Solo el host puede ir a RoleSelector
    if (isCurrentUserHost) {
      setShowRoleSelector(true);
    } else {
      console.warn('❌ Solo el host puede acceder a la selección de roles');
    }
  };

  const handleBackToLobby = () => {
    setShowRoleSelector(false);
  };

  // 🔧 NUEVA FUNCIÓN: Determinar qué pantalla mostrar según usuario y fase
  const getScreenForCurrentUser = () => {
    // Si estamos mostrando el selector de roles manualmente (solo host)
    if (showRoleSelector && currentPhase === GAME_PHASES.LOBBY && isCurrentUserHost) {
      return 'role_selector';
    }

    // Basado en la fase del juego
    switch (currentPhase) {
      case GAME_PHASES.LOBBY:
        return 'lobby';
      
      case GAME_PHASES.ROLE_SELECTION:
        // 🎯 AQUÍ ESTÁ EL FIX PRINCIPAL:
        // Solo el host ve RoleSelector, no-hosts se quedan en Lobby
        return isCurrentUserHost ? 'role_selector' : 'lobby_with_roles';
      
      case GAME_PHASES.NIGHT_PHASE:
        return 'night_phase';
      
      case GAME_PHASES.DAY_PHASE:
        return 'day_phase';
      
      case GAME_PHASES.VOTING:
        return 'voting';
      
      case GAME_PHASES.GAME_END:
        return 'game_end';
      
      default:
        return 'loading';
    }
  };

  const renderCurrentScreen = () => {
    const screen = getScreenForCurrentUser();
    
    // 🆕 NUEVO: Si estamos en modo testing y está habilitado, mostrar el panel
    const isTestingEnabled = import.meta.env.DEV || import.meta.env.VITE_ENABLE_TESTING === 'true';
    if (showTestingPanel && isTestingEnabled) {
      return <TestingPanel onBack={() => setShowTestingPanel(false)} />;
    }
    
    switch (screen) {
      case 'lobby':
        return <Lobby onNext={handleShowRoleSelector} />;
      
      case 'lobby_with_roles':
        // 🆕 NUEVO: Lobby especial para no-hosts durante selección de roles
        return <Lobby onNext={handleShowRoleSelector} showRoleSelection={true} />;
      
      case 'role_selector':
        return <RoleSelector onBack={handleBackToLobby} />;
      
      case 'night_phase':
        return <NightPhase />;
      
      case 'day_phase':
        return <DayPhase isHost={isCurrentUserHost} />;
      
      case 'voting':
        return <VotingPhase />;
      
      case 'game_end':
        return <RevealPhase />;
      
      case 'loading':
      default:
        return (
          <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 flex items-center justify-center p-4">
            <div className="bg-slate-800 rounded-lg p-8 max-w-md w-full border border-slate-700 text-center">
              <div className="text-4xl mb-4">🎮</div>
              <h2 className="text-2xl font-bold text-white mb-4">One Night Werewolf</h2>
              <p className="text-slate-400 mb-6">
                Cargando...
              </p>
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-400 mx-auto"></div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800">
      {/* Header con estado de conexión */}
      <div className="fixed top-0 left-0 right-0 z-50 bg-slate-900/95 backdrop-blur border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 py-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-white font-bold text-lg">🐺 One Night Werewolf</h1>
              {gameState?.room_code && (
                <span className="bg-slate-700 text-white px-3 py-1 rounded text-sm">
                  Sala: {gameState.room_code}
                </span>
              )}
            </div>
            
            <div className="flex items-center gap-4">
              {/* Estado de conexión */}
              <div className={`flex items-center gap-2 text-sm ${
                isConnected ? 'text-green-400' : 'text-red-400'
              }`}>
                <span className="text-sm">
                  {isConnected ? '🟢' : '🔴'}
                </span>
                {isConnected ? 'Conectado' : 'Desconectado'}
              </div>

              {/* 🆕 NUEVO: Botón de Testing Panel */}
              {(import.meta.env.DEV || import.meta.env.VITE_ENABLE_TESTING === 'true') && (
                <button
                  onClick={() => setShowTestingPanel(!showTestingPanel)}
                  className={`flex items-center gap-2 px-3 py-1 rounded text-sm transition-colors ${
                    showTestingPanel 
                      ? 'bg-purple-600 text-white hover:bg-purple-700' 
                      : 'bg-slate-700 text-slate-300 hover:bg-slate-600 hover:text-white'
                  }`}
                  title="Panel de Testing"
                >
                  <TestTube size={16} />
                  {showTestingPanel ? 'Salir Testing' : 'Testing'}
                </button>
              )}
              
              {/* Fase actual */}
              {gameState && !showTestingPanel && (
                <span className="bg-blue-700 text-white px-3 py-1 rounded text-sm">
                  {currentPhase.replace('_', ' ')}
                </span>
              )}

              {/* 🆕 NUEVO: Indicador de rol de usuario */}
              {gameState && !showTestingPanel && (
                <span className={`px-3 py-1 rounded text-sm ${
                  isCurrentUserHost 
                    ? 'bg-yellow-600 text-white' 
                    : 'bg-slate-600 text-white'
                }`}>
                  {isCurrentUserHost ? '👑 Host' : '👤 Jugador'}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Contenido principal */}
      <div className="pt-16">
        <div className="flex flex-col lg:flex-row min-h-screen">
          {/* Contenido principal */}
          <div className="flex-1">
            {renderCurrentScreen()}
          </div>

          {/* Panel lateral con log (solo en fases de juego) */}
          {gameState && (currentPhase === GAME_PHASES.NIGHT_PHASE || currentPhase === GAME_PHASES.DAY_PHASE) && (
            <div className="lg:w-80 lg:border-l lg:border-slate-700 bg-slate-900">
              <div className="p-4 h-full">
                <GameLog />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Notificación de error */}
      {showError && error && (
        <div className="fixed bottom-4 right-4 z-50 max-w-sm">
          <div className="bg-red-900 border border-red-500 rounded-lg p-4 shadow-lg">
            <div className="flex items-start gap-3">
              <AlertCircle size={20} className="text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-red-200 font-medium">Error</p>
                <p className="text-red-300 text-sm">{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Overlay de desconexión */}
      {!isConnected && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 flex items-center justify-center">
          <div className="bg-slate-800 rounded-lg p-8 max-w-sm w-full mx-4 border border-slate-700 text-center">
            <span className="text-4xl mb-4 block">📡</span>
            <h3 className="text-xl font-bold text-white mb-2">Conexión perdida</h3>
            <p className="text-slate-400 mb-4">
              Intentando reconectar al servidor...
            </p>
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-400 mx-auto"></div>
          </div>
        </div>
      )}

      {/* Debug info (solo en desarrollo) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="fixed bottom-4 left-4 z-50 bg-black/80 text-green-400 p-3 rounded text-xs font-mono max-w-xs">
          <div>Phase: {currentPhase}</div>
          <div>Screen: {getScreenForCurrentUser()}</div>
          <div>Connected: {isConnected ? 'Yes' : 'No'}</div>
          <div>Room: {gameState?.room_code || 'None'}</div>
          <div>Players: {gameState?.player_count || 0}</div>
          <div>Current User: {currentPlayerName}</div>
          <div>Host: {hostPlayer?.name || 'None'}</div>
          <div>Is Host: {isCurrentUserHost ? 'YES' : 'NO'}</div>
          {privateState?.your_role && (
            <div>Role: {privateState.your_role}</div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
