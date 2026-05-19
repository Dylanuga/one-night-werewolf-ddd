// src/components/RevealPhase.jsx
import React from 'react';
import { RotateCcw, Home } from 'lucide-react';
import { useGameStore } from '../store/gameStore';
import { ROLES } from '../utils/constants';

export const RevealPhase = () => {
  const { revealData, gameState, privateState, playerName, resetGame } = useGameStore();

  if (!revealData) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 flex items-center justify-center p-4">
        <div className="bg-slate-800 rounded-lg p-8 border border-slate-700 text-center">
          <div className="text-4xl mb-4">🏁</div>
          <h2 className="text-2xl font-bold text-white mb-2">Revelación</h2>
          <p className="text-slate-400">Esperando resultados...</p>
        </div>
      </div>
    );
  }

  const { final_roles, original_roles, eliminated_ids, winners } = revealData;

  const rows = Object.keys(final_roles || {}).map(pid => {
    const finalRole = final_roles[pid];
    const originalRole = original_roles?.[pid];
    return {
      id: pid,
      name: finalRole?.name || originalRole?.name || pid,
      original: originalRole?.role,
      final: finalRole?.role,
      eliminated: eliminated_ids?.includes(pid)
    };
  });

  // Determinar si el jugador actual es host
  const state = gameState || privateState;
  const host = state?.players?.find(p => p.is_host);
  const isHost = host?.name && playerName === host.name;

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-slate-800 rounded-lg p-8 border border-slate-700">
          <div className="text-center mb-6">
            <div className="text-4xl mb-4">🏁</div>
            <h2 className="text-2xl font-bold text-white mb-2">Revelación</h2>
            <p className="text-slate-300">{winners?.message || 'Resultados finales'}</p>
          </div>

          <div className="mb-6">
            <div className="bg-slate-900/60 border border-slate-700 rounded-lg p-4">
              <h3 className="text-white font-bold mb-2">Ganadores</h3>
              <p className="text-slate-300">
                Equipo: <span className="font-bold">
                  {winners?.team === 'villagers' ? 'Aldeanos' :
                   winners?.team === 'werewolves' ? 'Lobos' :
                   winners?.team === 'tanner' ? 'Bufón' : '—'}
                </span>
              </p>
            </div>
          </div>

          <div className="grid gap-2">
            {rows.map(row => (
              <div
                key={row.id}
                className={`flex items-center justify-between rounded-lg border px-4 py-2 ${
                  row.eliminated ? 'bg-red-900/40 border-red-500' : 'bg-slate-900 border-slate-700'
                }`}
              >
                <div className="text-white font-medium">
                  {row.name} {row.eliminated && <span className="text-red-300">(eliminado)</span>}
                </div>
                <div className="text-slate-300 text-sm">
                  Inicial: <span className="font-bold">{ROLES[row.original]?.name || row.original}</span>
                  {' '}→{' '}
                  Final: <span className="font-bold">{ROLES[row.final]?.name || row.final}</span>
                </div>
              </div>
            ))}
          </div>

          {isHost ? (
            <div className="mt-8 pt-6 border-t border-slate-700 flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={() => resetGame('role_selection')}
                className="flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-slate-900 font-bold rounded-xl transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-amber-500/20"
              >
                <RotateCcw size={20} />
                Jugar otra vez
              </button>
              
              <button
                onClick={() => resetGame('lobby')}
                className="flex items-center justify-center gap-2 px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white font-semibold rounded-xl transition-all duration-200 border border-slate-600 hover:border-slate-500"
              >
                <Home size={20} />
                Volver al Lobby
              </button>
            </div>
          ) : (
            <div className="mt-8 pt-6 border-t border-slate-700 text-center">
              <div className="inline-flex items-center gap-2 text-amber-400 text-sm bg-amber-500/10 px-4 py-2 rounded-full border border-amber-500/20">
                <div className="w-2 h-2 bg-amber-400 rounded-full animate-ping" />
                <span>Esperando a que el host inicie una nueva partida o regrese al lobby...</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
