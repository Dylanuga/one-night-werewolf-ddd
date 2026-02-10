// src/components/RevealPhase.jsx
import React from 'react';
import { useGameStore } from '../store/gameStore';
import { ROLES } from '../utils/constants';

export const RevealPhase = () => {
  const { revealData } = useGameStore();

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
        </div>
      </div>
    </div>
  );
};
