// src/components/NightPhase.jsx
import React, { useEffect, useMemo, useCallback } from 'react';
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
import { useDebugState, useDebugStateObject } from '../hooks/useDebugState';
import { useRenderTracking, useEffectTracking, useStateTracking } from '../hooks/useRenderTracking';
import { useStableMemo, useStableCallback, useDebouncedEffect, useMemoryLeakPrevention } from '../hooks/usePerformanceOptimization';
import { useDebugEvents } from '../hooks/useDebugUtils';

export const NightPhase = React.memo(() => {
  const {
    gameState,
    privateState,
    getCurrentTurnRole,
    getCurrentTurnDisplay, 
    isMyTurn,
    getNightAction,
    getEffectiveActionResult
  } = useGameStore();

  // ✅ NUEVO: Hook para eventos de debug
  const { logEvent } = useDebugEvents('NightPhase');

  // ✅ NUEVO: Sistema de tracking avanzado
  const trackingProps = {
    hasPrivateState: !!privateState,
    hasGameState: !!gameState,
    currentPhase: privateState?.phase,
    currentTurnRole: privateState?.current_turn_role,
    isMyTurn: privateState?.is_your_turn
  };

  const { logManual } = useRenderTracking('NightPhase', trackingProps, {
    logFrequency: 5 // Log cada 5 renders para componente crítico
  });

  // ✅ NUEVO: Prevención de memory leaks
  const { isMounted, safeSetTimeout } = useMemoryLeakPrevention('NightPhase');

  // ✅ OPTIMIZADO: Memoización estable para valores críticos
  const memoizedValues = useStableMemo(() => {
    const myRole = privateState?.your_role;
    const currentTurnRole = getCurrentTurnRole();
    const currentTurnDisplay = getCurrentTurnDisplay();
    const isCurrentUserTurn = isMyTurn();
    const nightActionData = getNightAction();
    const actionResult = getEffectiveActionResult();
    
    return {
      myRole,
      currentTurnRole,
      currentTurnDisplay,
      isCurrentUserTurn,
      nightActionData,
      actionResult
    };
  }, [
    privateState?.your_role,
    privateState?.current_turn_role,
    privateState?.is_your_turn,
    privateState?.night_action,
    getCurrentTurnRole,
    getCurrentTurnDisplay,
    isMyTurn,
    getNightAction,
    getEffectiveActionResult
  ]);

  const {
    myRole,
    currentTurnRole,
    currentTurnDisplay,
    isCurrentUserTurn,
    nightActionData,
    actionResult
  } = memoizedValues;

  // ✅ NUEVO: Tracking de estados críticos
  useStateTracking('currentTurnRole', currentTurnRole, 'NightPhase');
  useStateTracking('isCurrentUserTurn', isCurrentUserTurn, 'NightPhase');
  useStateTracking('actionResult', actionResult?.message, 'NightPhase');

  // ✅ OPTIMIZADO: Efecto principal con debouncing para evitar spam
  useDebouncedEffect(() => {
    if (isMounted()) {
      logManual('main_effect_triggered', {
        currentTurnRole,
        isCurrentUserTurn,
        nightActionType: nightActionData?.type,
        hasActionResult: !!actionResult
      });
    }
  }, [
    currentTurnRole, 
    isCurrentUserTurn, 
    nightActionData?.type,
    actionResult?.message
  ], 50); // 50ms debounce  // ✅ NUEVO: Efecto específico para monitorear nightActionData
  useEffect(() => {
    if (nightActionData) {
      logEvent('night_action_data_detected', {
        nightActionData,
        isMyTurn: isCurrentUserTurn,
        currentRole: currentTurnRole
      });

      console.log('🌙 DEBUG NightPhase - NIGHT ACTION DATA DETECTADO:', {
        nightActionData,
        isMyTurn: isCurrentUserTurn,
        currentRole: currentTurnRole,
        timestamp: Date.now()
      });
    }
  }, [nightActionData?.type, nightActionData?.message, isCurrentUserTurn, logEvent]);

  // ✅ FIX: DEBUG optimizado con logs específicos para cambios
  useEffect(() => {
    console.log('� DEBUG NightPhase - EFECTO DISPARADO:', {
      currentTurnRole,
      isCurrentUserTurn,
      hasNightAction: !!nightActionData,
      nightActionType: nightActionData?.type,
      hasActionResult: !!actionResult,
      actionResultMessage: actionResult?.message,
      privateStateId: privateState?._updateId,
      timestamp: Date.now()
    });
  }, [
    currentTurnRole, 
    isCurrentUserTurn, 
    nightActionData?.type, // ✅ Dependencia específica del tipo
    actionResult?.message, // ✅ Dependencia específica del mensaje
    privateState?._updateId // ✅ Dependencia del ID único
  ]);

  // ✅ OPTIMIZADO: Callback estable para renderizado
  const renderCurrentPhaseInfo = useStableCallback(() => {
    // ✅ REGLA: Sin logs, sin efectos secundarios, función completamente pura
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
  }, [currentTurnRole, isCurrentUserTurn, currentTurnDisplay, nightActionData, actionResult], 'renderCurrentPhaseInfo');

  // ✅ OPTIMIZADO: Efecto de logging con debouncing
  useDebouncedEffect(() => {
    if (isMounted()) {
      logManual('render_phase_info', {
        currentTurnRole,
        isCurrentUserTurn,
        hasNightActionData: !!nightActionData,
        hasActionResult: !!actionResult
      });
    }
  }, [currentTurnRole, isCurrentUserTurn, nightActionData, actionResult], 100);

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