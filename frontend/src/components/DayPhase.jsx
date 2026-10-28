// src/components/DayPhase.jsx
import React, { useState, useEffect, useRef } from 'react';
import { Clock, Eye } from 'lucide-react';
import { useGameStore } from '../store/gameStore';
import { ROLES } from '../utils/constants';

export const DayPhase = ({ isHost }) => {
  const { endDiscussion, gameState, privateState, nightNotes, actionResult } = useGameStore();

  const endTimestamp = gameState?.discussion_end_timestamp;
  const serverRemaining = gameState?.discussion_remaining;
  const serverTime = gameState?.server_time;
  const duration = gameState?.discussion_duration || 300;
  const endTimeRef = useRef(null);

  const [timeLeft, setTimeLeft] = useState(() => {
    if (typeof serverRemaining === 'number') {
      return Math.max(0, Math.round(serverRemaining));
    }
    if (endTimestamp && serverTime) {
      return Math.max(0, Math.round(endTimestamp - serverTime));
    }
    if (endTimestamp) {
      return Math.max(0, Math.round(endTimestamp - Date.now() / 1000));
    }
    return duration;
  });

  useEffect(() => {
    if (!endTimestamp && typeof serverRemaining !== 'number') return;

    let remSec = duration;
    if (typeof serverRemaining === 'number') {
      remSec = Math.max(0, serverRemaining);
    } else if (endTimestamp && serverTime) {
      remSec = Math.max(0, endTimestamp - serverTime);
    } else if (endTimestamp) {
      remSec = Math.max(0, endTimestamp - Date.now() / 1000);
    }

    const candidateEnd = Date.now() + remSec * 1000;
    if (!endTimeRef.current || Math.abs(candidateEnd - endTimeRef.current) > 1000) {
      endTimeRef.current = candidateEnd;
    }

    const updateTimer = () => {
      if (!endTimeRef.current) return;
      const remaining = Math.max(0, Math.round((endTimeRef.current - Date.now()) / 1000));
      setTimeLeft(remaining);
    };

    updateTimer();
    const interval = setInterval(updateTimer, 250);
    return () => clearInterval(interval);
  }, [endTimestamp, serverRemaining, serverTime, duration]);

  const myOriginalRole = privateState?.your_original_role || privateState?.your_role;
  const myCurrentRole = privateState?.your_role;

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

          {/* Resumen de lo ocurrido en la noche para el jugador */}
          <div className="my-6 bg-slate-900/70 border border-slate-700 rounded-xl p-4 text-left max-w-xl mx-auto">
            <div className="flex items-center gap-2 text-cyan-400 font-bold text-sm mb-2">
              <Eye size={16} />
              <span>Resumen de tu Noche</span>
            </div>
            <div className="text-sm text-slate-300 space-y-1.5">
              <p>
                🎭 Rol inicial: <strong className="text-white">{ROLES[myOriginalRole]?.name || myOriginalRole || 'Desconocido'}</strong>
                {myCurrentRole && myOriginalRole && myCurrentRole !== myOriginalRole && (
                  <span className="text-amber-300 ml-2">
                    → Rol visto tras tu acción: <strong>{ROLES[myCurrentRole]?.name || myCurrentRole}</strong>
                  </span>
                )}
              </p>
              {privateState?.night_summary ? (
                <p className="text-amber-300 font-medium">
                  {ROLES[myOriginalRole]?.emoji || '✨'} {privateState.night_summary}
                </p>
              ) : (
                <>
                  {nightNotes?.seer && myOriginalRole === 'seer' && (
                    <p className="text-purple-300 font-medium">🔮 {nightNotes.seer}</p>
                  )}
                  {nightNotes?.werewolf && myOriginalRole === 'werewolf' && (
                    <p className="text-red-300 font-medium">🐺 {nightNotes.werewolf}</p>
                  )}
                  {nightNotes?.mason && myOriginalRole === 'mason' && (
                    <p className="text-cyan-300 font-medium">🔨 {nightNotes.mason}</p>
                  )}
                  {privateState?.robber_last_target && myOriginalRole === 'robber' && (
                    <p className="text-amber-300 font-medium">
                      🦹 {privateState.robber_last_target.auto ? '🎲 (Aleatoria) ' : ''}Intercambiaste carta con {privateState.robber_last_target.name} y obtuviste {ROLES[privateState.robber_last_target.new_role || privateState.robber_last_target.role || myCurrentRole]?.name || privateState.robber_last_target.new_role || myCurrentRole}.
                    </p>
                  )}
                  {privateState?.troublemaker_last_swap && myOriginalRole === 'troublemaker' && (
                    <p className="text-amber-300 font-medium">
                      🎭 {privateState.troublemaker_last_swap.auto ? '🎲 (Aleatoria) ' : ''}Intercambiaste las cartas de {privateState.troublemaker_last_swap.a?.name || privateState.troublemaker_last_swap[0]?.name} y {privateState.troublemaker_last_swap.b?.name || privateState.troublemaker_last_swap[1]?.name}.
                    </p>
                  )}
                  {privateState?.drunk_last_center !== undefined && myOriginalRole === 'drunk' && (
                    <p className="text-amber-300 font-medium">
                      🍺 Intercambiaste tu carta con la carta {['izquierda', 'centro', 'derecha'][privateState.drunk_last_center] || 'izquierda'} del centro.
                    </p>
                  )}
                  {actionResult?.message && !nightNotes?.seer && !nightNotes?.werewolf && !privateState?.robber_last_target && !privateState?.troublemaker_last_swap && privateState?.drunk_last_center === undefined && (
                    <p className="text-green-300 font-medium">
                      ✓ {actionResult.auto ? '🎲 (Aleatoria) ' : ''}{actionResult.summary_text || actionResult.message}
                    </p>
                  )}
                </>
              )}
            </div>
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
