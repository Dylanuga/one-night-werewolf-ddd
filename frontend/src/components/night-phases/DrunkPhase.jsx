// src/components/night-phases/DrunkPhase.jsx
import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { useGameStore } from '../../store/gameStore';

export const DrunkPhase = ({ isMyTurn, nightActionData, actionResult }) => {
  const { executeNightAction, privateState } = useGameStore();
  const [selectedCenter, setSelectedCenter] = useState(null);
  const [hasActed, setHasActed] = useState(false);

  useEffect(() => {
    if (!isMyTurn) {
      setSelectedCenter(null);
      setHasActed(false);
    }
  }, [isMyTurn]);

  useEffect(() => {
    if (actionResult && actionResult.success) {
      setHasActed(true);
    }
  }, [actionResult]);

  const centerPositions = useMemo(() => nightActionData?.center_positions || [0, 1, 2], [nightActionData]);
  const drunkCenter = privateState?.drunk_last_center;
  const posNames = ['izquierda', 'centro', 'derecha'];

  const handleSelect = useCallback((pos) => {
    if (hasActed) return;
    setSelectedCenter(pos);
  }, [hasActed]);

  const handleSwap = useCallback(() => {
    if (selectedCenter === null || hasActed) return;
    const success = executeNightAction({ center_position: selectedCenter });
    if (success) {
      setHasActed(true);
    }
  }, [selectedCenter, hasActed, executeNightAction]);

  if (!isMyTurn) {
    return (
      <div className="bg-amber-900/30 border border-amber-500 rounded-lg p-6 text-center">
        <h3 className="text-xl font-bold text-amber-300 mb-4">🍺 Turno: Borracho</h3>
        <p className="text-amber-200 mb-2">Intercambia su carta con una del centro sin verla.</p>
        {nightActionData?.message && (
          <div className="text-slate-400 text-xs mt-2">{nightActionData.message}</div>
        )}
      </div>
    );
  }

  if (!nightActionData) {
    return (
      <div className="bg-amber-900/30 border border-amber-500 rounded-lg p-6 text-center">
        <h3 className="text-xl font-bold text-amber-300 mb-4">🍺 Borracho</h3>
        <p className="text-white">Esperando datos del servidor...</p>
      </div>
    );
  }

  return (
    <div className="bg-amber-900/20 border border-amber-500 rounded-lg p-6">
      <h3 className="text-xl font-bold text-amber-300 mb-4 text-center">🍺 Tu acción</h3>
      <p className="text-amber-200 text-center mb-4">{nightActionData.message}</p>

      <div className="grid grid-cols-3 gap-3 mb-4">
        {centerPositions.map(pos => (
          <button
            key={pos}
            onClick={() => handleSelect(pos)}
            disabled={hasActed}
            className={`border rounded-lg p-4 ${
              selectedCenter === pos
                ? 'bg-amber-700/60 border-amber-400'
                : 'bg-slate-800 border-slate-600'
            }`}
          >
            <div className="text-3xl mb-2">🃏</div>
            <div className="text-white font-bold">Carta {pos + 1}</div>
          </button>
        ))}
      </div>

      <button
        onClick={handleSwap}
        disabled={selectedCenter === null || hasActed}
        className="w-full bg-amber-700 hover:bg-amber-600 disabled:opacity-50 text-white font-bold py-2 rounded-lg"
      >
        Intercambiar con el centro
      </button>

      {hasActed && actionResult?.success && (
        <div className="bg-green-900/30 border border-green-500 rounded-lg p-4 mt-4">
          <p className="text-green-400 text-center font-bold">✓ {actionResult.message}</p>
        </div>
      )}

      {drunkCenter !== undefined && drunkCenter !== null && (
        <div className="bg-yellow-900/20 border border-yellow-500 rounded-lg p-4 mt-4">
          <p className="text-yellow-400 text-center font-semibold">
            Recuerda: elegiste la carta {posNames[drunkCenter] || 'izquierda'}.
          </p>
        </div>
      )}
    </div>
  );
};
