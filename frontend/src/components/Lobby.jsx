// src/components/Lobby.jsx
import React, { useState } from 'react';
import { Users, Crown, Play, LogOut, UserPlus, Copy } from 'lucide-react';
import { useGameStore } from '../store/gameStore';
import { useSocket } from '../hooks/useSocket';
import { MAX_PLAYERS } from '../utils/constants';

export const Lobby = () => {
  const {
    gameState,
    playerName,
    roomCode: inputRoomCode,
    setPlayerName,
    setRoomCode,
    error
  } = useGameStore();

  const { createRoom, joinRoom, leaveRoom, isConnected } = useSocket();
  const [isJoining, setIsJoining] = useState(false);

  const players = gameState?.players || [];
  const currentRoomCode = gameState?.room_code;
  const playerCount = players.length;
  const hostPlayer = players.find(p => p.is_host);
  const isHost = hostPlayer && players.some(p => p.is_host);
  const canStartGame = isHost && playerCount >= 3 && playerCount <= MAX_PLAYERS;

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

  const nextPhase = () => {
    // Esta función será llamada desde RoleSelector
    console.log('Avanzar a selección de roles');
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
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Controles del host */}
        {isHost && (
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
                onClick={nextPhase}
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
      </div>
    </div>
  );
};