// src/components/RoleSelector.jsx
import React, { useState, useEffect } from 'react';
import { Crown, Play, ArrowLeft, Plus, Minus } from 'lucide-react';
import { useGameStore } from '../store/gameStore';
import { useSocket } from '../hooks/useSocket';
import { ROLES } from '../utils/constants';

export const RoleSelector = ({ onBack }) => {
  const { gameState, error } = useGameStore();
  const { setRoles, startGame } = useSocket();
  
  const [selectedRoles, setSelectedRoles] = useState({});
  const [isStarting, setIsStarting] = useState(false);

  const players = gameState?.players || [];
  const playerCount = players.length;
  const requiredRoles = playerCount + 3; // jugadores + 3 cartas del centro
  const hostPlayer = players.find(p => p.is_host);
  const isHost = hostPlayer && players.some(p => p.is_host);

  // Calcular total de roles seleccionados
  const totalSelected = Object.values(selectedRoles).reduce((sum, count) => sum + count, 0);

  // Garantizar que siempre hay 2 lobos (requisito de esta implementación)
  useEffect(() => {
    setSelectedRoles(prev => ({ ...prev, werewolf: 2 }));
  }, []);

  const updateRoleCount = (roleType, change) => {
    setSelectedRoles(prev => {
      const currentCount = prev[roleType] || 0;
      const newCount = Math.max(0, currentCount + change);
      
      // Los lobos deben ser exactamente 2 para esta implementación
      if (roleType === 'werewolf' && newCount !== 2) {
        return prev;
      }
      
      return {
        ...prev,
        [roleType]: newCount
      };
    });
  };

  const canStartGame = () => {
    return (
      isHost &&
      totalSelected === requiredRoles &&
      selectedRoles.werewolf === 2 && // Exactamente 2 lobos
      playerCount >= 3 &&
      playerCount <= 5
    );
  };

  const handleStartGame = async () => {
    if (!canStartGame()) return;
    
    setIsStarting(true);
    
    // Convertir a array de roles
    const rolesArray = [];
    Object.entries(selectedRoles).forEach(([roleType, count]) => {
      for (let i = 0; i < count; i++) {
        rolesArray.push(roleType);
      }
    });
    
    // Establecer roles primero
    setRoles(rolesArray);
    
    // Pequeño delay y luego iniciar juego
    setTimeout(() => {
      startGame();
      setIsStarting(false);
    }, 500);
  };

  if (!isHost) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 flex items-center justify-center p-4">
        <div className="bg-slate-800 rounded-lg p-8 max-w-md w-full border border-slate-700 text-center">
          <h2 className="text-2xl font-bold text-white mb-4">Selección de Roles</h2>
          <div className="bg-red-900/50 border border-red-500 rounded-lg p-4">
            <p className="text-red-200">No eres el host de esta sala</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="text-4xl mb-4">🐺</div>
          <h1 className="text-3xl font-bold text-white mb-2">Selección de Roles</h1>
        </div>

        {/* Info de la sala */}
        <div className="bg-slate-800 rounded-lg p-6 mb-6 border border-cyan-500">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-white">
            <div>
              <p className="text-slate-400">Sala:</p>
              <p className="text-xl font-bold">{gameState?.room_code}</p>
            </div>
            <div>
              <p className="text-slate-400">Jugadores conectados:</p>
              <p className="text-xl font-bold">{playerCount}</p>
            </div>
            <div>
              <p className="text-slate-400">Roles necesarios:</p>
              <p className="text-xl font-bold">{requiredRoles} (jugadores + 3)</p>
            </div>
            <div>
              <p className="text-slate-400">Roles seleccionados:</p>
              <p className="text-xl font-bold">{totalSelected}</p>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-900/50 border border-red-500 rounded-lg p-4 mb-6">
            <p className="text-red-200">{error}</p>
          </div>
        )}

        {/* Instrucciones */}
        <div className="bg-slate-800 rounded-lg p-6 mb-6 border border-slate-700">
          <h3 className="text-xl font-bold text-white mb-4">Selecciona los roles para la partida</h3>
          <p className="text-slate-400 mb-2">
            Debes seleccionar exactamente {requiredRoles} roles.
          </p>
          <p className="text-yellow-400 text-sm">
            ⚠️ Esta implementación requiere exactamente 2 lobos.
          </p>
        </div>

        {/* Grid de roles */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {Object.entries(ROLES).map(([roleType, roleInfo]) => {
            const count = selectedRoles[roleType] || 0;
            const isWerewolf = roleType === 'werewolf';
            
            return (
              <div
                key={roleType}
                className={`bg-slate-800 rounded-lg p-6 border transition-all duration-200 ${
                  count > 0 
                    ? 'border-yellow-500 bg-slate-700' 
                    : 'border-slate-600 hover:border-slate-500'
                }`}
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{roleInfo.emoji}</span>
                    <div>
                      <h4 className="font-bold text-white text-lg">{roleInfo.name}</h4>
                      {isWerewolf && (
                        <span className="text-xs bg-red-600 px-2 py-1 rounded text-white">
                          Requerido: 2
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => updateRoleCount(roleType, -1)}
                      disabled={count === 0 || (isWerewolf && count <= 2)}
                      className="w-8 h-8 bg-red-600 hover:bg-red-700 disabled:bg-slate-600 disabled:opacity-50 text-white rounded flex items-center justify-center transition-colors"
                    >
                      <Minus size={16} />
                    </button>
                    
                    <span className="w-8 text-center text-white font-bold text-xl">
                      {count}
                    </span>
                    
                    <button
                      onClick={() => updateRoleCount(roleType, 1)}
                      disabled={totalSelected >= requiredRoles || (isWerewolf && count >= 2)}
                      className="w-8 h-8 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 disabled:opacity-50 text-white rounded flex items-center justify-center transition-colors"
                    >
                      <Plus size={16} />
                    </button>
                  </div>
                </div>
                
                <p className="text-slate-300 text-sm">{roleInfo.description}</p>
              </div>
            );
          })}
        </div>

        {/* Resumen y controles */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div>
              <h3 className="text-lg font-bold text-white mb-2">Resumen de roles seleccionados</h3>
              <div className="flex flex-wrap gap-2">
                {Object.entries(selectedRoles).map(([roleType, count]) => {
                  if (count === 0) return null;
                  return (
                    <span
                      key={roleType}
                      className="bg-yellow-600 text-white px-3 py-1 rounded-full text-sm font-medium"
                    >
                      {ROLES[roleType].emoji} {ROLES[roleType].name.split(' ')[0]} × {count}
                    </span>
                  );
                })}
              </div>
              
              <p className="text-slate-400 text-sm mt-2">
                Total: {totalSelected} / {requiredRoles} roles
                {totalSelected === requiredRoles && (
                  <span className="text-green-400 ml-2">✓ Completo</span>
                )}
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={onBack}
                className="bg-slate-600 hover:bg-slate-700 text-white font-medium py-3 px-6 rounded-lg transition-colors flex items-center gap-2"
              >
                <ArrowLeft size={20} />
                Volver
              </button>
              
              <button
                onClick={handleStartGame}
                disabled={!canStartGame() || isStarting}
                className="bg-green-600 hover:bg-green-700 disabled:bg-slate-600 disabled:opacity-50 text-white font-bold py-3 px-6 rounded-lg transition-colors flex items-center gap-2"
              >
                {isStarting ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Iniciando...
                  </>
                ) : (
                  <>
                    <Play size={20} />
                    Iniciar Juego
                  </>
                )}
              </button>
            </div>
          </div>
          
          {!canStartGame() && totalSelected === requiredRoles && (
            <div className="mt-4 p-3 bg-yellow-900/50 border border-yellow-500 rounded-lg">
              <p className="text-yellow-200 text-sm">
                ⚠️ Verifica que tengas exactamente 2 lobos para esta implementación.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};