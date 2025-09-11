// src/components/Lobby.jsx
import React, { useState, useEffect } from 'react';
import { Users, Crown, Play, LogOut, UserPlus, Copy, Eye, Clock, CheckCircle, Settings } from 'lucide-react';
import { useGameStore } from '../store/gameStore';
import { useSocket } from '../hooks/useSocket';
import { MAX_PLAYERS, ROLES } from '../utils/constants';

export const Lobby = ({ onNext, showRoleSelection = false }) => {
  const {
    gameState,
    playerName,
    roomCode: inputRoomCode,
    setPlayerName,
    setRoomCode,
    error,
    selectedRoles,
    areRolesComplete
  } = useGameStore();

  const { createRoom, joinRoom, leaveRoom, isConnected } = useSocket();

  const players = gameState?.players || [];
  const currentRoomCode = gameState?.room_code;
  const playerCount = players.length;
  const requiredRoles = playerCount + 3;
  
  // Lógica correcta para determinar si el usuario actual es host
  const currentPlayerName = playerName;
  const hostPlayer = players.find(p => p.is_host);
  const isCurrentUserHost = hostPlayer && hostPlayer.name === currentPlayerName;
  const canStartGame = isCurrentUserHost && playerCount >= 3 && playerCount <= MAX_PLAYERS;

  // 🆕 NUEVO: Los roles ahora vienen del estado global, no hay necesidad de escucha local
  useEffect(() => {
    if (showRoleSelection && !isCurrentUserHost) {
      console.log('👥 No-host: roles seleccionados desde el store:', selectedRoles);
    }
  }, [showRoleSelection, isCurrentUserHost, selectedRoles]);

  const handleCreateRoom = () => {
    if (!playerName.trim()) {
      return;
    }
    createRoom(playerName.trim());
  };

  const handleJoinRoom = () => {
    if (!playerName.trim() || !inputRoomCode.trim()) {
      return;
    }
    joinRoom(inputRoomCode.trim(), playerName.trim());
  };

  const handleLeaveRoom = () => {
    leaveRoom();
  };

  const copyRoomCode = () => {
    if (currentRoomCode) {
      navigator.clipboard.writeText(currentRoomCode);
    }
  };

  // 🆕 NUEVO: Componente para mostrar roles seleccionados (para no-hosts)
  const RoleSelectionDisplay = () => {
    const totalSelected = Object.values(selectedRoles).reduce((sum, count) => sum + count, 0);
    const isComplete = areRolesComplete();

    return (
      <div className="bg-slate-800 rounded-lg p-6 mb-6 border border-blue-500">
        <h3 className="text-xl font-bold text-blue-400 mb-4 flex items-center gap-2">
          <Settings size={24} className="animate-spin" />
          El Host está Configurando los Roles
        </h3>
        
        <div className="space-y-4">
          {/* Progreso */}
          <div className="bg-slate-700 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-white font-medium">Progreso de Configuración</span>
              <span className={`font-bold ${isComplete ? 'text-green-400' : 'text-blue-400'}`}>
                {totalSelected} / {requiredRoles}
              </span>
            </div>
            
            <div className="w-full bg-slate-600 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all duration-300 ${
                  isComplete ? 'bg-green-400' : 'bg-blue-400'
                }`}
                style={{ width: `${Math.min(100, (totalSelected / requiredRoles) * 100)}%` }}
              ></div>
            </div>
            
            {isComplete && (
              <div className="flex items-center gap-2 mt-2 text-green-400 text-sm">
                <CheckCircle size={16} />
                <span>¡Configuración completa! El juego comenzará pronto...</span>
              </div>
            )}
          </div>

          {/* Host info */}
          <div className="bg-slate-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Crown size={16} className="text-yellow-400" />
                <span className="text-white">Configurando:</span>
              </div>
              <span className="text-yellow-400 font-bold">
                {hostPlayer?.name || 'Host'}
              </span>
            </div>
          </div>

          {/* Roles seleccionados */}
          {totalSelected > 0 && (
            <div className="space-y-3">
              <h4 className="text-white font-medium">Roles Seleccionados:</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {Object.entries(selectedRoles).map(([roleType, count]) => {
                  if (count === 0) return null;
                  const roleInfo = ROLES[roleType];
                  if (!roleInfo) return null;
                  
                  return (
                    <div key={roleType} className="bg-slate-700 rounded-lg p-3 border border-green-500/30">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-xl">{roleInfo.emoji}</span>
                          <div>
                            <p className="text-white font-medium text-sm">{roleInfo.name}</p>
                            <p className="text-green-400 text-xs">En juego</p>
                          </div>
                        </div>
                        <span className="text-lg font-bold text-green-400">×{count}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Estado de espera */}
          {totalSelected === 0 && (
            <div className="text-center py-6">
              <div className="text-4xl mb-2">⏳</div>
              <p className="text-slate-400">Esperando a que el host seleccione roles...</p>
            </div>
          )}

          {/* Información adicional */}
          <div className="bg-slate-700 rounded-lg p-3">
            <div className="flex items-center gap-2 text-slate-300 text-sm">
              <span>💡</span>
              <span>Se necesitan {requiredRoles} roles: {playerCount} para jugadores + 3 para el centro</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Si no está conectado al socket
  if (!isConnected) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-400 mx-auto mb-4"></div>
          <p>Conectando al servidor...</p>
        </div>
      </div>
    );
  }

  // Si no está en una sala (pantalla inicial)
  if (!currentRoomCode) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 flex items-center justify-center p-4">
        <div className="bg-slate-800 rounded-lg p-8 max-w-md w-full border border-slate-700">
          <div className="text-center mb-8">
            <div className="text-4xl mb-4">🐺</div>
            <h1 className="text-3xl font-bold text-white mb-2">One Night Werewolf</h1>
            <p className="text-slate-400">Únete o crea una sala para jugar</p>
          </div>

          {error && (
            <div className="bg-red-900/50 border border-red-500 rounded-lg p-3 mb-6">
              <p className="text-red-200 text-sm">{error}</p>
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Tu nombre
              </label>
              <input
                type="text"
                value={playerName}
                onChange={(e) => setPlayerName(e.target.value)}
                placeholder="Ingresa tu nombre"
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-yellow-500"
                maxLength={20}
              />
            </div>

            <div className="grid grid-cols-1 gap-3">
              <button
                onClick={handleCreateRoom}
                disabled={!playerName.trim()}
                className="w-full bg-green-600 hover:bg-green-700 disabled:bg-slate-600 disabled:opacity-50 text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                <UserPlus size={20} />
                Crear Sala
              </button>

              <div className="text-center text-slate-400 text-sm">o</div>

              <div className="space-y-2">
                <input
                  type="text"
                  value={inputRoomCode}
                  onChange={(e) => setRoomCode(e.target.value)}
                  placeholder="Código de sala (ej: ABCD)"
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 uppercase"
                  maxLength={4}
                />
                <button
                  onClick={handleJoinRoom}
                  disabled={!playerName.trim() || !inputRoomCode.trim()}
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:opacity-50 text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  <Users size={20} />
                  Unirse a Sala
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Pantalla del lobby (dentro de una sala)
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="text-4xl mb-4">🐺</div>
          <h1 className="text-3xl font-bold text-white mb-2">One Night Werewolf</h1>
          {showRoleSelection && !isCurrentUserHost && (
            <p className="text-blue-400 flex items-center justify-center gap-2">
              <Clock size={16} />
              El host está configurando la partida...
            </p>
          )}
        </div>

        {/* Info de la sala */}
        <div className="bg-slate-800 rounded-lg p-6 mb-6 border border-slate-700">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-white">
            <div>
              <p className="text-slate-400">Sala:</p>
              <p className="text-xl font-bold">{currentRoomCode}</p>
            </div>
            <div>
              <p className="text-slate-400">Código de sala:</p>
              <div className="flex items-center gap-2">
                <p className="text-xl font-bold">{currentRoomCode}</p>
                <button
                  onClick={copyRoomCode}
                  className="p-1 hover:bg-slate-700 rounded transition-colors"
                  title="Copiar código"
                >
                  <Copy size={16} />
                </button>
              </div>
            </div>
          </div>
          <div className="mt-4">
            <p className="text-slate-400">Jugadores: <span className="text-white font-bold">{playerCount}</span></p>
          </div>
        </div>

        {/* 🆕 NUEVO: Mostrar selección de roles si showRoleSelection=true y no eres host */}
        {showRoleSelection && !isCurrentUserHost && (
          <RoleSelectionDisplay />
        )}

        {/* Lista de jugadores */}
        <div className="bg-slate-800 rounded-lg p-6 mb-6 border border-slate-700">
          <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <Users size={24} />
            Jugadores en la sala:
          </h3>
          <div className="space-y-2">
            {players.map((player, index) => (
              <div
                key={player.player_id || index}
                className="flex items-center justify-between bg-slate-700 rounded-lg p-3"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${player.is_connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                  <span className="text-white font-medium">{player.name}</span>
                  {player.is_host && (
                    <div className="flex items-center gap-1 bg-yellow-600 px-2 py-1 rounded text-xs">
                      <Crown size={12} />
                      Host
                    </div>
                  )}
                  {player.name === currentPlayerName && (
                    <div className="flex items-center gap-1 bg-blue-600 px-2 py-1 rounded text-xs">
                      <span>Tú</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Controles del host - SOLO SI EL USUARIO ACTUAL ES HOST Y NO está en modo showRoleSelection */}
        {isCurrentUserHost && !showRoleSelection && (
          <div className="bg-slate-800 rounded-lg p-6 mb-6 border border-cyan-500">
            <h3 className="text-xl font-bold text-cyan-400 mb-4 flex items-center gap-2">
              <Crown size={24} />
              Controles del Host
            </h3>
            
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-green-400">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span>Suficientes jugadores. ¡Puedes iniciar el juego!</span>
              </div>
              
              <button
                onClick={onNext}
                disabled={!canStartGame}
                className="w-full bg-green-600 hover:bg-green-700 disabled:bg-slate-600 disabled:opacity-50 text-white font-bold py-3 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                <Play size={20} />
                Seleccionar Roles e Iniciar Juego
              </button>
              
              <p className="text-sm text-slate-400 text-center">
                {playerCount} jugadores - ¡Listo para comenzar!
              </p>
            </div>
          </div>
        )}

        {/* Panel informativo para NO-HOSTS (solo si NO está en modo showRoleSelection) */}
        {!isCurrentUserHost && hostPlayer && !showRoleSelection && (
          <div className="bg-slate-800 rounded-lg p-6 mb-6 border border-slate-600">
            <h3 className="text-xl font-bold text-slate-300 mb-4 flex items-center gap-2">
              <Eye size={24} />
              Estado de la Sala
            </h3>
            
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-blue-400">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                <span>Esperando a que el host configure la partida...</span>
              </div>
              
              <div className="bg-slate-700 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Crown size={16} className="text-yellow-400" />
                    <span className="text-white">Host actual:</span>
                  </div>
                  <span className="text-yellow-400 font-bold">
                    {hostPlayer?.name || 'N/A'}
                  </span>
                </div>
              </div>
              
              <div className="flex items-center gap-2 text-slate-400 text-sm">
                <span>💡</span>
                <span>El host seleccionará los roles y comenzará la partida</span>
              </div>
              
              <p className="text-sm text-slate-500 text-center">
                {playerCount} jugadores conectados - ¡Listos para jugar!
              </p>
            </div>
          </div>
        )}

        {/* Panel cuando no hay host definido */}
        {!hostPlayer && (
          <div className="bg-yellow-900/30 border border-yellow-500 rounded-lg p-6 mb-6">
            <h3 className="text-xl font-bold text-yellow-400 mb-2">⚠️ Sin Host</h3>
            <p className="text-yellow-200">
              Parece que no hay un host definido en esta sala. Esto puede ser un error técnico.
            </p>
          </div>
        )}

        {/* Botón salir */}
        <div className="text-center">
          <button
            onClick={handleLeaveRoom}
            className="bg-red-600 hover:bg-red-700 text-white font-medium py-3 px-6 rounded-lg transition-colors flex items-center gap-2 mx-auto"
          >
            <LogOut size={20} />
            Salir de la Sala
          </button>
        </div>

        {/* Debug info */}
        {process.env.NODE_ENV === 'development' && (
          <div className="mt-6 bg-black/50 rounded p-3 text-xs text-green-400 font-mono">
            <div>Tu nombre: {currentPlayerName}</div>
            <div>Host en sala: {hostPlayer?.name || 'ninguno'}</div>
            <div>¿Eres host?: {isCurrentUserHost ? 'SÍ' : 'NO'}</div>
            <div>Show role selection: {showRoleSelection ? 'SÍ' : 'NO'}</div>
            <div>Puede iniciar: {canStartGame ? 'SÍ' : 'NO'}</div>
          </div>
        )}
      </div>
    </div>
  );
};