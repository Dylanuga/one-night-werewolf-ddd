// src/components/NightPhase.jsx - VERSIÓN OPTIMIZADA
import React, { useEffect, useMemo } from 'react';
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

export const NightPhase = React.memo(() => {
  const {
    gameState,
    privateState,
    getCurrentTurnRole,
    isMyTurn,
    getNightAction,
    getEffectiveActionResult
  } = useGameStore();

  // ✅ NUEVA ARQUITECTURA: Datos desde privateState con turn_timestamp
  const myRole = privateState?.your_role;
  const currentTurnRole = getCurrentTurnRole();
  const isCurrentUserTurn = isMyTurn();
  const nightActionData = getNightAction();
  const actionResult = getEffectiveActionResult();
  
  // ✅ CRÍTICO: Crear currentTurn desde privateState para PhaseTimer
  const currentTurnDisplay = useMemo(() => {
    if (!privateState?.current_turn_role || !privateState?.turn_timestamp) {
      return null;
    }
    
    return {
      role: privateState.current_turn_role,
      phase: `Fase: ${privateState.current_turn_role}`,
      timestamp: privateState.turn_timestamp,
      duration: 6  // TURN_DURATION
    };
  }, [privateState?.current_turn_role, privateState?.turn_timestamp]);

  // ✅ OPTIMIZACIÓN: Un solo efecto simplificado para debugging
  useEffect(() => {
    console.log('🌙 NightPhase - Estado actualizado (NUEVA ARQUITECTURA):', {
      currentTurnRole,
      isCurrentUserTurn,
      hasNightAction: !!nightActionData,
      hasActionResult: !!actionResult,
      turn_timestamp: privateState?.turn_timestamp,
      currentTurnDisplay,
      timestamp: Date.now()
    });
  }, [currentTurnRole, isCurrentUserTurn, privateState?.turn_timestamp]);

  // ✅ OPTIMIZACIÓN: Función de render estable sin useMemo/useCallback
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
        isCurrentUserTurn 
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
              {isCurrentUserTurn && (
                <p className="text-yellow-400 font-medium">¡Es tu turno!</p>
              )}
            </div>
          </div>
          <PhaseTimer currentTurn={currentTurnDisplay} isMyTurn={isCurrentUserTurn} />
        </div>
        
        {roleInfo && (
          <p className="text-slate-300 mb-4">{roleInfo.description}</p>
        )}

        {/* Renderizar componente específico según el rol */}
        {currentTurnRole === 'werewolf' && (
          <WerewolfPhase 
            isMyTurn={isCurrentUserTurn} 
            nightActionData={nightActionData} 
            actionResult={actionResult} 
          />
        )}
        
        {currentTurnRole === 'mason' && (
          <MasonPhase 
            isMyTurn={isCurrentUserTurn} 
            nightActionData={nightActionData} 
          />
        )}
        
        {currentTurnRole && currentTurnRole !== 'werewolf' && currentTurnRole !== 'mason' && (
          <GenericPhase 
            currentTurnRole={currentTurnRole} 
            isMyTurn={isCurrentUserTurn} 
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
            {isCurrentUserTurn ? (
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
});