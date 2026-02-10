// src/components/night-phases/RobberPhase.jsx
import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { useGameStore } from '../../store/gameStore';

export const RobberPhase = ({ isMyTurn, nightActionData, actionResult }) => {
  const { executeNightAction, privateState } = useGameStore();
  const [selectedPlayer, setSelectedPlayer] = useState('');
  const [hasActed, setHasActed] = useState(false);

  useEffect(() => {
    if (!isMyTurn) {
      setSelectedPlayer('');
      setHasActed(false);
    }
  }, [isMyTurn]);

  useEffect(() => {
    if (actionResult && actionResult.success) {
      setHasActed(true);
    }
  }, [actionResult]);

  const players = useMemo(() => nightActionData?.players || [], [nightActionData]);
  const robbedTarget = privateState?.robber_last_target;

  const handleRob = useCallback(() => {
    if (!selectedPlayer || hasActed) return;
    const success = executeNightAction({ target_player_id: selectedPlayer });
    if (success) {
      setHasActed(true);
    }
  }, [selectedPlayer, hasActed, executeNightAction]);

  if (!isMyTurn) {
    return (
      <div className="bg-slate-700/50 border border-slate-500 rounded-lg p-6 text-center">
        <h3 className="text-xl font-bold text-white mb-4">🥷 Turno: Ladrón</h3>
        <p className="text-slate-300 mb-2">Intercambia su carta con la de otro jugador y la ve.</p>
        {nightActionData?.message && (
          <div className="text-slate-400 text-xs mt-2">{nightActionData.message}</div>
        )}
      </div>
    );
  }

  if (!nightActionData) {
    return (
      <div className="bg-slate-700/50 border border-slate-500 rounded-lg p-6 text-center">
        <h3 className="text-xl font-bold text-white mb-4">🥷 Ladrón</h3>
        <p className="text-white">Esperando datos del servidor...</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-700/40 border border-slate-500 rounded-lg p-6">
      <h3 className="text-xl font-bold text-white mb-4 text-center">🥷 Tu acción</h3>
      <p className="text-slate-300 text-center mb-4">{nightActionData.message}</p>

      <div className="grid gap-2 mb-4">
        {players.length === 0 && (
          <p className="text-slate-300 text-sm text-center">No hay otros jugadores para elegir.</p>
        )}
        {players.map(p => (
          <button
            key={p.id}
            onClick={() => setSelectedPlayer(p.id)}
            disabled={hasActed}
            className={`w-full text-left px-4 py-2 rounded-lg border ${
              selectedPlayer === p.id
                ? 'bg-emerald-700/60 border-emerald-400 text-white'
                : 'bg-slate-800 border-slate-600 text-slate-200'
            }`}
          >
            {p.name}
          </button>
        ))}
      </div>

      <button
        onClick={handleRob}
        disabled={!selectedPlayer || hasActed}
        className="w-full bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 text-white font-bold py-2 rounded-lg"
      >
        Robar rol del jugador
      </button>

      {hasActed && actionResult?.success && (
        <div className="bg-green-900/30 border border-green-500 rounded-lg p-4 mt-4">
          <p className="text-green-400 text-center font-bold">✓ {actionResult.message}</p>
        </div>
      )}

      {robbedTarget && (
        <div className="bg-amber-900/20 border border-amber-500 rounded-lg p-4 mt-4">
          <p className="text-amber-300 text-center">
            Último robo: <span className="font-bold">{robbedTarget.name}</span>
          </p>
        </div>
      )}
    </div>
  );
};
