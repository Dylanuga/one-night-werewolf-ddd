// src/components/night-phases/TroublemakerPhase.jsx
import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { useGameStore } from '../../store/gameStore';

export const TroublemakerPhase = ({ isMyTurn, nightActionData, actionResult }) => {
  const { executeNightAction, privateState } = useGameStore();
  const [selectedA, setSelectedA] = useState('');
  const [selectedB, setSelectedB] = useState('');
  const [hasActed, setHasActed] = useState(false);

  useEffect(() => {
    if (!isMyTurn) {
      setSelectedA('');
      setSelectedB('');
      setHasActed(false);
    }
  }, [isMyTurn]);

  useEffect(() => {
    if (actionResult && actionResult.success) {
      setHasActed(true);
    }
  }, [actionResult]);

  const players = useMemo(() => nightActionData?.players || [], [nightActionData]);
  const lastSwap = privateState?.troublemaker_last_swap;
  const swappedFromResult = actionResult?.swapped_players;
  const swapInfo = lastSwap || swappedFromResult;

  const toggleSelect = useCallback((playerId) => {
    if (hasActed) return;
    if (!selectedA || selectedA === playerId) {
      setSelectedA(playerId === selectedA ? '' : playerId);
      return;
    }
    if (!selectedB || selectedB === playerId) {
      setSelectedB(playerId === selectedB ? '' : playerId);
      return;
    }
  }, [hasActed, selectedA, selectedB]);

  const canConfirm = selectedA && selectedB && selectedA !== selectedB && !hasActed;

  const handleSwap = useCallback(() => {
    if (!canConfirm) return;
    const success = executeNightAction({
      target_player_id_a: selectedA,
      target_player_id_b: selectedB
    });
    if (success) {
      setHasActed(true);
    }
  }, [canConfirm, selectedA, selectedB, executeNightAction]);

  if (!isMyTurn) {
    return (
      <div className="bg-slate-700/50 border border-slate-500 rounded-lg p-6 text-center">
        <h3 className="text-xl font-bold text-white mb-4">🃏 Turno: Troublemaker (Alborotadora)</h3>
        <p className="text-slate-300 mb-2">Intercambia las cartas de otros dos jugadores sin verlas.</p>
        {nightActionData?.message && (
          <div className="text-slate-400 text-xs mt-2">{nightActionData.message}</div>
        )}
      </div>
    );
  }

  if (!nightActionData) {
    return (
      <div className="bg-slate-700/50 border border-slate-500 rounded-lg p-6 text-center">
        <h3 className="text-xl font-bold text-white mb-4">🃏 Alborotadora</h3>
        <p className="text-white">Esperando datos del servidor...</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-700/40 border border-slate-500 rounded-lg p-6">
      <h3 className="text-xl font-bold text-white mb-4 text-center">🃏 Tu acción</h3>
      <p className="text-slate-300 text-center mb-4">{nightActionData.message}</p>

      <div className="grid gap-2 mb-4">
        {players.length === 0 && (
          <p className="text-slate-300 text-sm text-center">No hay jugadores para elegir.</p>
        )}
        {players.map(p => {
          const isSelected = selectedA === p.id || selectedB === p.id;
          return (
            <button
              key={p.id}
              onClick={() => toggleSelect(p.id)}
              disabled={hasActed}
              className={`w-full text-left px-4 py-2 rounded-lg border ${
                isSelected
                  ? 'bg-pink-700/60 border-pink-400 text-white'
                  : 'bg-slate-800 border-slate-600 text-slate-200'
              }`}
            >
              {p.name}
            </button>
          );
        })}
      </div>

      <button
        onClick={handleSwap}
        disabled={!canConfirm}
        className="w-full bg-pink-700 hover:bg-pink-600 disabled:opacity-50 text-white font-bold py-2 rounded-lg"
      >
        Intercambiar roles
      </button>

      {hasActed && actionResult?.success && (
        <div className="bg-green-900/30 border border-green-500 rounded-lg p-4 mt-4">
          <p className="text-green-400 text-center font-bold">✓ {actionResult.message}</p>
        </div>
      )}

      {swapInfo && (
        <div className="bg-amber-900/20 border border-amber-500 rounded-lg p-4 mt-4">
          <p className="text-amber-300 text-center font-semibold">
            Cambiaste los roles de {swapInfo.a.name} y {swapInfo.b.name}
          </p>
          <p className="text-amber-200 text-center text-sm mt-1">
            Último intercambio: <span className="font-bold">{swapInfo.a.name}</span> ↔{' '}
            <span className="font-bold">{swapInfo.b.name}</span>
          </p>
        </div>
      )}
    </div>
  );
};
