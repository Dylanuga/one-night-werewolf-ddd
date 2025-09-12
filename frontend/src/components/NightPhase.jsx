// src/components/NightPhase.jsx
import React, { useEffect } from 'react';
import { Eye } from 'lucide-react';
import { useGameStore } from '../store/gameStore';
import { ROLES } from '../utils/constants';
import { 
  PhaseTimer, 
  WerewolfPhase, 
  MasonPhase, 
  GenericPhase, 
  ActionResult 
} from './night-phases';

export const NightPhase = () => {
  const {
    gameState,
    privateState,
    nightAction,
    setNightAction,
    actionResult,
    currentTurn
  } = useGameStore();

  // 🔧 FIX MEJORADO: Usar tanto currentTurn como privateState para mayor robustez
  const myRole = privateState?.your_role;
  // Preferir currentTurn.role si está disponible, sino usar privateState
  const currentTurnRole = currentTurn?.role || privateState?.current_turn_role;
  const isMyTurn = privateState?.is_your_turn;
  const nightActionData = privateState?.night_action || nightAction;

  // Limpiar nightAction cuando deja de ser tu turno
  useEffect(() => {
    if (!isMyTurn && nightAction) {
      setNightAction(null);
    }
  }, [isMyTurn, nightAction, setNightAction]);

  // DEBUG: Detectar cambios en el turno actual
  useEffect(() => {
    console.log('🔄 NightPhase - Cambio detectado:', {
      currentTurn,
      fromStore: currentTurn?.role,
      fromPrivate: privateState?.current_turn_role,
      usingRole: currentTurnRole,
      isMyTurn
    });
  }, [currentTurn, privateState, currentTurnRole, isMyTurn]);

  const renderCurrentPhaseInfo = () => {
    if (!currentTurnRole) {
      return (
        <div className="bg-slate-800 rounded-lg p-6 text-center">
          <p className="text-slate-400">Preparando fase nocturna...</p>
        </div>
      );
    }

    const roleInfo = ROLES[currentTurnRole];

    return (
      <div className={`rounded-lg p-6 border ${
        isMyTurn 
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
              {isMyTurn && (
                <p className="text-yellow-400 font-medium">¡Es tu turno!</p>
              )}
            </div>
          </div>
          <PhaseTimer currentTurnRole={currentTurnRole} isMyTurn={isMyTurn} />
        </div>

        {roleInfo && (
          <p className="text-slate-300 mb-4">{roleInfo.description}</p>
        )}

        {/* Renderizar componente específico según el rol */}
        {currentTurnRole === 'werewolf' && (
          <WerewolfPhase 
            isMyTurn={isMyTurn} 
            nightActionData={nightActionData} 
            actionResult={actionResult} 
          />
        )}
        
        {currentTurnRole === 'mason' && (
          <MasonPhase 
            isMyTurn={isMyTurn} 
            nightActionData={nightActionData} 
          />
        )}
        
        {currentTurnRole && currentTurnRole !== 'werewolf' && currentTurnRole !== 'mason' && (
          <GenericPhase 
            currentTurnRole={currentTurnRole} 
            isMyTurn={isMyTurn} 
          />
        )}

        <ActionResult actionResult={actionResult} />
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
            Noche - Fase: {currentTurnRole || 'Preparando...'}
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
            {isMyTurn ? (
              <p>🎯 Es tu turno.</p>
            ) : (
              <p>⏱️ Esperando turno de: {currentTurnRole}</p>
            )}
            <p>🎭 Tu rol: {myRole}</p>
            <p>👥 Jugadores en partida: {gameState?.player_count || 0}</p>
            {/* Mostrar info del turno actual para todos */}
            {currentTurnRole && (
              <div className="mt-2 p-2 rounded bg-slate-900/60 border border-slate-700">
                <span className="font-bold text-cyan-300">Turno actual:</span> <span className="font-mono">{currentTurnRole}</span>
                {nightActionData?.message && (
                  <div className="text-slate-400 text-xs mt-1">{nightActionData.message}</div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};