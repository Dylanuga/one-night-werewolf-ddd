// src/components/night-phases/WerewolfPhase.jsx
import React, { useState, useEffect } from 'react';
import { useGameStore } from '../../store/gameStore';
import { useRenderTracking, useEffectTracking, useStateTracking } from '../../hooks/useRenderTracking';
import { useStableCallback, useDebouncedEffect, useMemoryLeakPrevention } from '../../hooks/usePerformanceOptimization';

export const WerewolfPhase = ({ isMyTurn, nightActionData, actionResult }) => {
  const { executeNightAction } = useGameStore();
  const [hasActed, setHasActed] = useState(false);

  // ✅ NUEVO: Sistema de tracking avanzado
  const trackingProps = {
    isMyTurn,
    hasActionData: !!nightActionData,
    nightActionType: nightActionData?.type,
    hasActionResult: !!actionResult,
    hasActed
  };

  const { logManual } = useRenderTracking('WerewolfPhase', trackingProps, {
    logFrequency: 3 // Más frecuente para componente interactivo
  });

  // ✅ NUEVO: Prevención de memory leaks
  const { isMounted } = useMemoryLeakPrevention('WerewolfPhase');

  // ✅ NUEVO: Tracking de estado interno
  useStateTracking('hasActed', hasActed, 'WerewolfPhase');

  // ✅ OPTIMIZADO: Efectos con debouncing y tracking
  useDebouncedEffect(() => {
    if (!isMyTurn && hasActed && isMounted()) {
      logManual('reset_has_acted', { reason: 'not_my_turn' });
      setHasActed(false);
    }
  }, [isMyTurn, hasActed], 50);

  useDebouncedEffect(() => {
    if (actionResult && !hasActed && isMounted()) {
      logManual('action_completed', { 
        actionResult: actionResult.message,
        centerRole: actionResult.center_role 
      });
      setHasActed(true);
    }
  }, [actionResult, hasActed], 50);

  // ✅ OPTIMIZADO: Handler estable y limpio
  const handleCenterCardClick = useStableCallback((position) => {
    // ✅ REGLA: Toda lógica de logging en useEffect separados
    if (!isMyTurn || hasActed) {
      return;
    }
    
    const success = executeNightAction({ center_position: position });
    
    if (success) {
      setHasActed(true);
      logManual('night_action_executed', { position, success: true });
    } else {
      logManual('night_action_failed', { position, success: false });
    }
  }, [isMyTurn, hasActed, executeNightAction, logManual], 'handleCenterCardClick');

  // ✅ OPTIMIZADO: Efecto para logging con debouncing
  useDebouncedEffect(() => {
    if (hasActed && isMounted()) {
      logManual('user_action_state_changed', {
        hasActed,
        isMyTurn,
        actionType: nightActionData?.type
      });
    }
  }, [hasActed, isMyTurn, nightActionData?.type], 100);

  if (!isMyTurn) {
    // Mostrar info del turno actual aunque no seas lobo
    return (
      <div className="bg-red-900/30 border border-red-500 rounded-lg p-6 text-center">
        <h3 className="text-xl font-bold text-red-400 mb-4">🐺 Turno: Lobos</h3>
        <p className="text-red-200 mb-2">Los lobos se reconocen entre sí.</p>
        <p className="text-red-300 text-sm">Si está solo, puede ver una carta del centro.</p>
        {nightActionData?.message && (
          <div className="text-slate-400 text-xs mt-2">{nightActionData.message}</div>
        )}
      </div>
    );
  }

  if (!nightActionData) {
    return (
      <div className="bg-red-900/30 border border-red-500 rounded-lg p-6 text-center">
        <h3 className="text-xl font-bold text-red-400 mb-4">🐺 Lobo</h3>
        <p className="text-white">Esperando datos del servidor...</p>
      </div>
    );
  }

  // Caso A: Mostrar el otro lobo
  if (nightActionData.type === 'show_other_werewolf') {
    return (
      <div className="bg-red-900/30 border border-red-500 rounded-lg p-6 text-center">
        <h3 className="text-xl font-bold text-red-400 mb-4">
          🐺 Otros Lobos
        </h3>
        <p className="text-white text-lg mb-4">
          {nightActionData.message}
        </p>
        <div className="bg-red-800/50 rounded-lg p-4 mt-4">
          <p className="text-red-200 font-bold text-2xl">
            🐺 {nightActionData.other_werewolf_name}
          </p>
          <p className="text-red-300 text-sm mt-2">Es tu compañero lobo</p>
        </div>
        <p className="text-red-200 text-sm mt-4">
          ¡Ambos conocéis vuestra identidad!
        </p>
      </div>
    );
  }

  // Caso B: Elegir carta del centro
  if (nightActionData.type === 'can_view_center') {
    return (
      <div className="bg-red-900/30 border border-red-500 rounded-lg p-6">
        <h3 className="text-xl font-bold text-red-400 mb-4 text-center">
          🐺 Eres el único lobo
        </h3>
        <p className="text-white text-center mb-6">
          {nightActionData.message}
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
        
        {hasActed && actionResult && (
          <div className="bg-green-900/30 border border-green-500 rounded-lg p-4 mt-4">
            <p className="text-green-400 text-center font-bold">
              ✓ {actionResult.message || 'Has elegido una carta'}
            </p>
            {actionResult.center_role && (
              <p className="text-white text-center mt-2">
                🃏 Has visto: <span className="font-bold text-yellow-400">{actionResult.center_role}</span>
              </p>
            )}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="bg-red-900/30 border border-red-500 rounded-lg p-6 text-center">
      <h3 className="text-xl font-bold text-red-400 mb-4">🐺 Lobo</h3>
      <p className="text-white">Tipo de acción no reconocido: {nightActionData.type}</p>
    </div>
  );
};