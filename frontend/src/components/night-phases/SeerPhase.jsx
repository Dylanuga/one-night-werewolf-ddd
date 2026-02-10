// src/components/night-phases/SeerPhase.jsx
import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { useGameStore } from '../../store/gameStore';

export const SeerPhase = ({ isMyTurn, nightActionData, actionResult }) => {
  const { executeNightAction, setNightNote } = useGameStore();
  const [mode, setMode] = useState('player');
  const [selectedPlayer, setSelectedPlayer] = useState('');
  const [selectedCenters, setSelectedCenters] = useState([]);
  const [hasActed, setHasActed] = useState(false);

  const roleNameMap = useMemo(() => ({
    werewolf: 'lobo',
    villager: 'aldeano',
    seer: 'pitonisa',
    robber: 'ladrón',
    troublemaker: 'alborotadora',
    tanner: 'curtidor',
    drunk: 'borracho',
    mason: 'masón',
    hunter: 'cazador',
    insomniac: 'insomne'
  }), []);
  const posNames = ['izquierda', 'centro', 'derecha'];

  useEffect(() => {
    if (!isMyTurn) {
      setMode('player');
      setSelectedPlayer('');
      setSelectedCenters([]);
      setHasActed(false);
    }
  }, [isMyTurn]);

  useEffect(() => {
    if (actionResult && actionResult.success) {
      setHasActed(true);
    }
  }, [actionResult]);

  const players = useMemo(() => nightActionData?.players || [], [nightActionData]);
  useEffect(() => {
    if (!actionResult?.success) return;
    if (actionResult.seen_player) {
      const roleName = roleNameMap[actionResult.seen_player.role] || actionResult.seen_player.role;
      setNightNote('seer', `${actionResult.seen_player.name} es ${roleName}`);
    }
    if (actionResult.seen_center) {
      const entries = actionResult.seen_center.map(card => {
        const posLabel = posNames[card.position] || posNames[0];
        const roleLabel = roleNameMap[card.role] || card.role;
        return `${posLabel}: ${roleLabel}`;
      });
      setNightNote('seer', `Centro: ${entries.join(', ')}`);
    }
  }, [actionResult, roleNameMap, posNames, setNightNote]);

  const toggleCenter = useCallback((pos) => {
    if (hasActed) return;
    setSelectedCenters(prev => {
      if (prev.includes(pos)) {
        return prev.filter(p => p !== pos);
      }
      if (prev.length >= 2) {
        return prev;
      }
      return [...prev, pos];
    });
  }, [hasActed]);

  const handleSeePlayer = useCallback(() => {
    if (!selectedPlayer || hasActed) return;
    const success = executeNightAction({ target_player_id: selectedPlayer });
    if (success) {
      setHasActed(true);
    }
  }, [selectedPlayer, hasActed, executeNightAction]);

  const handleSeeCenter = useCallback(() => {
    if (selectedCenters.length !== 2 || hasActed) return;
    const success = executeNightAction({ center_positions: selectedCenters });
    if (success) {
      setHasActed(true);
    }
  }, [selectedCenters, hasActed, executeNightAction]);

  if (!isMyTurn) {
    return (
      <div className="bg-purple-900/30 border border-purple-500 rounded-lg p-6 text-center">
        <h3 className="text-xl font-bold text-purple-300 mb-4">🔮 Turno: Pitonisa</h3>
        <p className="text-purple-200 mb-2">Puede ver el rol de otro jugador o dos cartas del centro.</p>
        {nightActionData?.message && (
          <div className="text-slate-400 text-xs mt-2">{nightActionData.message}</div>
        )}
      </div>
    );
  }

  if (!nightActionData) {
    return (
      <div className="bg-purple-900/30 border border-purple-500 rounded-lg p-6 text-center">
        <h3 className="text-xl font-bold text-purple-300 mb-4">🔮 Pitonisa</h3>
        <p className="text-white">Esperando datos del servidor...</p>
      </div>
    );
  }

  return (
    <div className="bg-purple-900/20 border border-purple-500 rounded-lg p-6">
      <h3 className="text-xl font-bold text-purple-300 mb-4 text-center">🔮 Tu acción</h3>
      <p className="text-purple-200 text-center mb-4">
        {nightActionData.message}
      </p>

      <div className="flex justify-center gap-4 mb-6">
        <button
          className={`px-4 py-2 rounded-lg border ${
            mode === 'player'
              ? 'bg-purple-700 border-purple-400 text-white'
              : 'bg-slate-800 border-slate-600 text-slate-200'
          }`}
          onClick={() => setMode('player')}
          disabled={hasActed}
        >
          Ver jugador
        </button>
        <button
          className={`px-4 py-2 rounded-lg border ${
            mode === 'center'
              ? 'bg-purple-700 border-purple-400 text-white'
              : 'bg-slate-800 border-slate-600 text-slate-200'
          }`}
          onClick={() => setMode('center')}
          disabled={hasActed}
        >
          Ver centro
        </button>
      </div>

      {mode === 'player' && (
        <div className="space-y-4">
          <div className="grid gap-2">
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
                    ? 'bg-purple-700/60 border-purple-400 text-white'
                    : 'bg-slate-800 border-slate-600 text-slate-200'
                }`}
              >
                {p.name}
              </button>
            ))}
          </div>
          <button
            onClick={handleSeePlayer}
            disabled={!selectedPlayer || hasActed}
            className="w-full bg-purple-700 hover:bg-purple-600 disabled:opacity-50 text-white font-bold py-2 rounded-lg"
          >
            Ver rol del jugador
          </button>
        </div>
      )}

      {mode === 'center' && (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            {[0, 1, 2].map(pos => {
              const active = selectedCenters.includes(pos);
              return (
                <button
                  key={pos}
                  onClick={() => toggleCenter(pos)}
                  disabled={hasActed}
                  className={`border rounded-lg p-4 ${
                    active ? 'bg-purple-700/60 border-purple-400' : 'bg-slate-800 border-slate-600'
                  }`}
                >
                  <div className="text-3xl mb-2">🃏</div>
                  <div className="text-white font-bold">Carta {pos + 1}</div>
                </button>
              );
            })}
          </div>
          <button
            onClick={handleSeeCenter}
            disabled={selectedCenters.length !== 2 || hasActed}
            className="w-full bg-purple-700 hover:bg-purple-600 disabled:opacity-50 text-white font-bold py-2 rounded-lg"
          >
            Ver 2 cartas del centro
          </button>
        </div>
      )}

      {hasActed && actionResult?.success && (
        <div className="bg-green-900/30 border border-green-500 rounded-lg p-4 mt-4">
          <p className="text-green-400 text-center font-bold">✓ {actionResult.message}</p>
          {actionResult.seen_player && (
            <p className="text-white text-center mt-2">
              👤 {actionResult.seen_player.name} es <span className="font-bold">{roleNameMap[actionResult.seen_player.role] || actionResult.seen_player.role}</span>
            </p>
          )}
          {actionResult.seen_center && (
            <div className="text-white text-center mt-2">
              {actionResult.seen_center.map(card => {
                const posLabel = posNames[card.position] || posNames[0];
                const roleLabel = roleNameMap[card.role] || card.role;
                return (
                  <div key={card.position}>
                    🃏 {posLabel}: <span className="font-bold">{roleLabel}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
