// src/App.jsx
import React, { useEffect, useState } from 'react';
import { useGameStore } from './store/gameStore';
import { useSocket } from './hooks/useSocket';
import { Lobby } from './components/Lobby';
import { RoleSelector } from './components/RoleSelector';
import { NightPhase } from './components/NightPhase';
import { GameLog } from './components/GameLog';
import TestingPanel from './components/TestingPanel';
import { GAME_PHASES } from './utils/constants';
import { AlertCircle, TestTube } from 'lucide-react';

function App() {
  const {
    gameState,
    privateState,
    playerName,
    error,
    isConnected,
    getCurrentPhase,
    reset
  } = useGameStore();

  const socket = useSocket();
  const [showRoleSelector, setShowRoleSelector] = useState(false);
  const [showError, setShowError] = useState(false);
  const [showTestingPanel, setShowTestingPanel] = useState(false); // 🆕 NUEVO

  const currentPhase = getCurrentPhase();

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
    
    // 🆕 NUEVO: Si estamos en modo testing, mostrar el panel
    if (showTestingPanel) {
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
        return (
          <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 flex items-center justify-center p-4">
            <div className="bg-slate-800 rounded-lg p-8 max-w-md w-full border border-slate-700 text-center">
              <div className="text-4xl mb-4">☀️</div>
              <h2 className="text-2xl font-bold text-white mb-4">Amanecer</h2>
              <p className="text-slate-400">
                La fase nocturna ha terminado. ¡Próximamente: fase de discusión!
              </p>
              <div className="mt-6">
                <button
                  onClick={() => reset()}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                >
                  Volver al Inicio
                </button>
              </div>
            </div>
          </div>
        );
      
      case 'voting':
        return (
          <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 flex items-center justify-center p-4">
            <div className="bg-slate-800 rounded-lg p-8 max-w-md w-full border border-slate-700 text-center">
              <div className="text-4xl mb-4">🗳️</div>
              <h2 className="text-2xl font-bold text-white mb-4">Votación</h2>
              <p className="text-slate-400">
                ¡Próximamente: fase de votación!
              </p>
              <div className="mt-6">
                <button
                  onClick={() => reset()}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                >
                  Volver al Inicio
                </button>
              </div>
            </div>
          </div>
        );
      
      case 'game_end':
        return (
          <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 flex items-center justify-center p-4">
            <div className="bg-slate-800 rounded-lg p-8 max-w-md w-full border border-slate-700 text-center">
              <div className="text-4xl mb-4">🏆</div>
              <h2 className="text-2xl font-bold text-white mb-4">Fin del Juego</h2>
              <p className="text-slate-400 mb-6">
                ¡Próximamente: resultados y ganadores!
              </p>
              <button
                onClick={() => reset()}
                className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
              >
                Jugar de Nuevo
              </button>
            </div>
          </div>
        );
      
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