// src/components/night-phases/WerewolfPhase.jsx - VERSIÓN OPTIMIZADA
import React, { useState, useEffect, useCallback } from 'react';
import { useGameStore } from '../../store/gameStore';

export const WerewolfPhase = ({ isMyTurn, nightActionData, actionResult }) => {
  const { executeNightAction } = useGameStore();
  const [hasActed, setHasActed] = useState(false);

  // ✅ OPTIMIZADO: Efecto simple para resetear estado
  useEffect(() => {
    if (!isMyTurn && hasActed) {
      setHasActed(false);
    }
  }, [isMyTurn, hasActed]);

  // ✅ OPTIMIZADO: Efecto simple para detectar acción completada
  useEffect(() => {
    if (actionResult && !hasActed) {
      setHasActed(true);
    }
  }, [actionResult, hasActed]);

  // ✅ OPTIMIZADO: Handler estable
  const handleCenterCardClick = useCallback((position) => {
    if (!isMyTurn || hasActed) {
      return;
    }
    
    const success = executeNightAction({ center_position: position });
    
    if (success) {
      setHasActed(true);
    }
  }, [isMyTurn, hasActed, executeNightAction]);

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
                🃏 Has visto ({['izquierda', 'centro', 'derecha'][actionResult.center_position] || 'izquierda'}):{' '}
                <span className="font-bold text-yellow-400">
                  {({
                    werewolf: 'lobo',
                    villager: 'aldeano',
                    seer: 'pitonisa',
                    robber: 'ladron',
                    troublemaker: 'alborotador',
                    tanner: 'curtidor',
                    drunk: 'borracho',
                    mason: 'mason',
                    hunter: 'cazador',
                    insomniac: 'insomne'
                  }[actionResult.center_role] || actionResult.center_role)}
                </span>
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
