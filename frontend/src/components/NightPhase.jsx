// src/components/NightPhase.jsx
import React, { useState, useEffect } from 'react';
import { Moon, Eye, Clock } from 'lucide-react';
import { useGameStore } from '../store/gameStore';
import { useSocket } from '../hooks/useSocket';
import { ROLES, TURN_DURATION } from '../utils/constants';

export const NightPhase = () => {
  const {
    gameState,
    privateState,
    currentTurn,
    nightAction,
    actionResult,
    isMyTurn
  } = useGameStore();

  const { executeNightAction } = useSocket();
  
  const [timeLeft, setTimeLeft] = useState(TURN_DURATION);
  const [hasActed, setHasActed] = useState(false);

  const myRole = privateState?.your_role;
  const currentTurnRole = currentTurn?.role;
  const isWerewolfTurn = currentTurnRole === 'werewolf';
  const isMyWerewolfTurn = isMyTurn() && myRole === 'werewolf';

  // Timer countdown
  useEffect(() => {
    if (currentTurn) {
      setTimeLeft(TURN_DURATION);
      setHasActed(false);
      
      const timer = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [currentTurn]);

  // Limpiar resultado de acción después de mostrarlo
  useEffect(() => {
    if (actionResult) {
      const timer = setTimeout(() => {
        // El store ya maneja el auto-clear del actionResult
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [actionResult]);

  const handleCenterCardClick = (position) => {
    if (!isMyWerewolfTurn || hasActed) return;
    
    executeNightAction({ center_position: position });
    setHasActed(true);
  };

  const renderWerewolfAction = () => {
    if (!nightAction) return null;

    // Caso A: Mostrar el otro lobo
    if (nightAction.type === 'show_other_werewolf') {
      return (
        <div className="bg-red-900/30 border border-red-500 rounded-lg p-6 text-center">
          <h3 className="text-xl font-bold text-red-400 mb-4">
            🐺 Otros Lobos
          </h3>
          <p className="text-white text-lg mb-2">
            {nightAction.message}
          </p>
          <div className="bg-red-800/50 rounded-lg p-4 mt-4">
            <p className="text-red-200 font-bold text-xl">
              {nightAction.other_werewolf_name}
            </p>
          </div>
        </div>
      );
    }

    // Caso B: Elegir carta del centro
    if (nightAction.type === 'can_view_center') {
      return (
        <div className="bg-red-900/30 border border-red-500 rounded-lg p-6">
          <h3 className="text-xl font-bold text-red-400 mb-4 text-center">
            🐺 Eres el único lobo
          </h3>
          <p className="text-white text-center mb-6">
            {nightAction.message}
          </p>
          
          <div className="grid grid-cols-3 gap-4">
            {[0, 1, 2].map(position => (
              <button
                key={position}
                onClick={() => handleCenterCardClick(position)}
                disabled={hasActed}
                className={`
                  bg-slate-700 hover:bg-slate-600 disabled:opacity-50 
                  border-2 border-yellow-500 rounded-lg p-4 transition-all duration-200
                  ${hasActed ? 'cursor-not-allowed' : 'hover:border-yellow-400'}
                `}
              >
                <div className="text-4xl mb-2">🃏</div>
                <p className="text-white font-bold">Carta {position + 1}</p>
              </button>
            ))}
          </div>
          
          {hasActed && (
            <p className="text-green-400 text-center mt-4">
              ✓ Has elegido una carta
            </p>
          )}
        </div>
      );
    }

    return null;
  };

  const renderActionResult = () => {
    if (!actionResult || !actionResult.success) return null;

    return (
      <div className="bg-green-900/30 border border-green-500 rounded-lg p-4 mt-4">
        <h4 className="text-green-400 font-bold mb-2">Resultado:</h4>
        <p className="text-white">{actionResult.message}</p>
      </div>
    );
  };

  const renderCurrentPhaseInfo = () => {
    if (!currentTurnRole) {
      return (
        <div className="bg-slate-800 rounded-lg p-6 text-center">
          <p className="text-slate-400">Preparando fase nocturna...</p>
        </div>
      );
    }

    const roleInfo = ROLES[currentTurnRole];
    const isMyRoleTurn = myRole === currentTurnRole;

    return (
      <div className={`rounded-lg p-6 border ${
        isMyRoleTurn 
          ? 'bg-yellow-900/30 border-yellow-500' 
          : 'bg-slate-800 border-slate-600'
      }`}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{roleInfo?.emoji || '❓'}</span>
            <div>
              <h3 className="text-xl font-bold text-white">
                Fase: {currentTurnRole}
              </h3>
              {isMyRoleTurn && (
                <p className="text-yellow-400 font-medium">¡Es tu turno!</p>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-2 text-white">
            <Clock size={20} />
            <span className="font-bold text-lg">{timeLeft}s</span>
          </div>
        </div>

        {roleInfo && (
          <p className="text-slate-300 mb-4">{roleInfo.description}</p>
        )}

        {isMyRoleTurn && isWerewolfTurn && renderWerewolfAction()}
        {actionResult && renderActionResult()}
        
        {!isMyRoleTurn && (
          <p className="text-slate-400 text-center">
            Esperando a que {currentTurnRole} complete su turno...
          </p>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="text-4xl mb-4">🌙</div>
          <h1 className="text-3xl font-bold text-white mb-2">
            Noche - Fase: {currentTurnRole || 'undefined'}
          </h1>
          <p className="text-slate-400">
            Los roles actúan en orden durante la noche
          </p>
        </div>

        {/* Tu rol */}
        <div className="bg-slate-800 rounded-lg p-6 mb-6 border border-slate-700">
          <h3 className="text-lg font-bold text-white mb-2">Tu Rol:</h3>
          <div className="flex items-center gap-3">
            <span className="text-3xl">{ROLES[myRole]?.emoji || '❓'}</span>
            <div>
              <p className="text-xl font-bold text-white">
                {myRole ? ROLES[myRole]?.name : 'Desconocido'}
              </p>
              <p className="text-slate-400">
                Eres: {myRole || 'rol no asignado'}
              </p>
            </div>
          </div>
        </div>

        {/* Fase actual */}
        {renderCurrentPhaseInfo()}

        {/* Información adicional */}
        <div className="mt-6 bg-slate-800 rounded-lg p-4 border border-slate-700">
          <h4 className="text-white font-bold mb-2 flex items-center gap-2">
            <Eye size={20} />
            Información:
          </h4>
          <div className="text-slate-300 text-sm space-y-1">
            {isMyTurn() ? (
              <p>🎯 Es tu turno. Tienes {timeLeft} segundos para actuar.</p>
            ) : (
              <p>⏱️ Esperando turno de: {currentTurnRole}</p>
            )}
            <p>🎭 Tu rol: {myRole}</p>
            <p>👥 Jugadores en partida: {gameState?.player_count || 0}</p>
          </div>
        </div>
      </div>
    </div>
  );
};