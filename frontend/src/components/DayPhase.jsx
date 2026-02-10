// src/components/DayPhase.jsx
import React from 'react';
import { useGameStore } from '../store/gameStore';

export const DayPhase = ({ isHost }) => {
  const { endDiscussion } = useGameStore();

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 p-4">
      <div className="max-w-3xl mx-auto">
        <div className="bg-slate-800 rounded-lg p-8 border border-slate-700 text-center">
          <div className="text-4xl mb-4">☀️</div>
          <h2 className="text-2xl font-bold text-white mb-2">Fase de Día</h2>
          <p className="text-slate-300 mb-6">
            Discute por Discord y decide a quién votar. Cuando el host termine la discusión,
            se abrirá la votación.
          </p>

          {isHost ? (
            <button
              onClick={endDiscussion}
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
            >
              Terminar discusión e iniciar votación
            </button>
          ) : (
            <div className="text-slate-400">
              Esperando a que el host inicie la votación...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
