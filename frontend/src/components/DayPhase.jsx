// src/components/DayPhase.jsx
import React, { useState, useEffect } from 'react';
import { Clock } from 'lucide-react';
import { useGameStore } from '../store/gameStore';

export const DayPhase = ({ isHost }) => {
  const { endDiscussion, gameState } = useGameStore();

  const endTimestamp = gameState?.discussion_end_timestamp;
  const duration = gameState?.discussion_duration || 300;

  const [timeLeft, setTimeLeft] = useState(() => {
    if (endTimestamp) {
      return Math.max(0, Math.round(endTimestamp - Date.now() / 1000));
    }
    return duration;
  });

  useEffect(() => {
    if (!endTimestamp) return;

    const updateTimer = () => {
      const remaining = Math.max(0, Math.round(endTimestamp - Date.now() / 1000));
      setTimeLeft(remaining);
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [endTimestamp]);

  const minutes = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;
  const formattedTime = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  const isUrgent = timeLeft <= 30 && timeLeft > 0;

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 p-4">
      <div className="max-w-3xl mx-auto">
        <div className="bg-slate-800 rounded-lg p-8 border border-slate-700 text-center shadow-xl">
          <div className="text-5xl mb-4">☀️</div>
          <h2 className="text-3xl font-bold text-white mb-2">Fase de Día</h2>
          <p className="text-slate-300 mb-6 max-w-xl mx-auto">
            Discutid lo que habéis visto, contrastad información y deducid quiénes son los hombres lobo.
          </p>

          {/* Temporizador de cuenta atrás */}
          <div className="my-8 flex flex-col items-center justify-center">
            <div
              className={`flex items-center gap-3 px-6 py-4 rounded-2xl border transition-all ${
                isUrgent
                  ? 'bg-red-950/60 border-red-500/80 text-red-400 animate-pulse shadow-lg shadow-red-900/30'
                  : 'bg-slate-900/80 border-amber-500/40 text-amber-300 shadow-md'
              }`}
            >
              <Clock size={32} className={isUrgent ? 'text-red-400 animate-spin' : 'text-amber-400'} />
              <div className="text-left">
                <div className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
                  Tiempo de Debate
                </div>
                <div className="text-4xl font-extrabold font-mono tracking-tight">
                  {formattedTime}
                </div>
              </div>
            </div>
            <p className="text-xs text-slate-400 mt-3">
              {timeLeft > 0
                ? 'Al llegar a 0, la fase de votación se abrirá automáticamente.'
                : '¡El tiempo de debate ha concluido! Pasando a votación...'}
            </p>
          </div>

          {isHost ? (
            <div className="mt-8 pt-6 border-t border-slate-700">
              <button
                onClick={endDiscussion}
                className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-xl transition-all shadow-lg hover:shadow-blue-500/25 active:scale-95"
              >
                Terminar discusión e iniciar votación
              </button>
              <p className="text-xs text-slate-500 mt-2">
                Como host, puedes abrir la votación antes si todos estáis listos.
              </p>
            </div>
          ) : (
            <div className="mt-6 text-slate-400 text-sm">
              Esperando a que concluya el tiempo o el host inicie la votación...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
