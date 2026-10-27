// src/components/VotingPhase.jsx
import React, { useState, useEffect } from 'react';
import { Clock, CheckCircle2, AlertTriangle, Users } from 'lucide-react';
import { useGameStore } from '../store/gameStore';

export const VotingPhase = () => {
  const {
    gameState,
    myVote,
    submitVote,
    endVoting,
    playerName,
    revealData
  } = useGameStore();

  const players = gameState?.players || [];
  const votes = gameState?.votes || {};
  const playersById = Object.fromEntries(players.map(p => [p.player_id, p]));
  
  const totalVotesCast = Object.values(votes).filter(v => v !== null && v !== undefined).length;
  const connectedPlayers = players.filter(p => p.is_connected !== false);
  const allConnectedVoted = connectedPlayers.length > 0 && connectedPlayers.every(p => votes[p.player_id]);
  const allVoted = players.length > 0 && players.every(p => votes[p.player_id]);
  
  const host = players.find(p => p.is_host);
  const isHost = host?.name && playerName === host.name;
  const alreadyRevealed = Boolean(revealData) || gameState?.phase === 'game_end';

  // Temporizador de votación
  const votingEndTimestamp = gameState?.voting_end_timestamp;
  const [timeLeft, setTimeLeft] = useState(() => {
    if (votingEndTimestamp) {
      return Math.max(0, Math.round(votingEndTimestamp - Date.now() / 1000));
    }
    return 60;
  });

  useEffect(() => {
    if (!votingEndTimestamp) return;

    const updateTimer = () => {
      const remaining = Math.max(0, Math.round(votingEndTimestamp - Date.now() / 1000));
      setTimeLeft(remaining);
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [votingEndTimestamp]);

  const minutes = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;
  const formattedTime = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  const isUrgent = timeLeft <= 15 && timeLeft > 0;

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 p-4">
      <div className="max-w-3xl mx-auto">
        <div className="bg-slate-800 rounded-2xl p-6 md:p-8 border border-slate-700 shadow-2xl">
          <div className="text-center mb-6">
            <div className="text-5xl mb-3">🗳️</div>
            <h2 className="text-2xl md:text-3xl font-bold text-white mb-2">Fase de Votación</h2>
            <p className="text-slate-300 text-sm md:text-base">
              Selecciona al jugador que sospechas que es Hombre Lobo para lincharlo.
            </p>

            {/* Contador de tiempo de votación */}
            <div className="mt-4 flex items-center justify-center gap-2">
              <div
                className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl border font-mono text-sm font-bold ${
                  isUrgent
                    ? 'bg-red-950/70 border-red-500/80 text-red-400 animate-pulse'
                    : 'bg-slate-900/80 border-amber-500/40 text-amber-300'
                }`}
              >
                <Clock size={16} className={isUrgent ? 'animate-spin' : ''} />
                <span>Tiempo restante: {formattedTime}</span>
              </div>
            </div>

            <p className="text-xs text-slate-400 mt-2">
              Al llegar a 0, la votación finalizará automáticamente con los votos que haya.
            </p>

            {myVote && (
              <div className="mt-3 inline-flex items-center gap-2 bg-amber-500/10 border border-amber-500/30 px-4 py-1.5 rounded-full text-amber-300 text-sm">
                <CheckCircle2 size={16} />
                <span>Tu voto: <strong>{playersById[myVote]?.name || myVote}</strong></span>
              </div>
            )}
          </div>

          {/* Lista de jugadores para votar */}
          <div className="grid gap-2.5 my-6">
            {players.map(p => {
              const isDisconnected = p.is_connected === false;
              const hasVotedForThis = myVote === p.player_id;
              const votersForPlayer = Object.entries(votes)
                .filter(([, targetId]) => targetId === p.player_id)
                .map(([voterId]) => {
                  const voterName = playersById[voterId]?.name || voterId;
                  return voterName === playerName ? `${voterName} (tú)` : voterName;
                });

              return (
                <div
                  key={p.player_id}
                  className={`bg-slate-900 border rounded-xl p-3.5 transition-all ${
                    hasVotedForThis
                      ? 'border-red-500/60 bg-red-950/20 shadow-md'
                      : 'border-slate-700/80 hover:border-slate-600'
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div
                        className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${
                          isDisconnected ? 'bg-amber-500/70' : 'bg-emerald-400'
                        }`}
                        title={isDisconnected ? 'Jugador desconectado temporalmente' : 'Conectado'}
                      />
                      <div className="truncate">
                        <span className="text-white font-semibold">{p.name}</span>
                        {p.name === playerName && (
                          <span className="text-xs text-slate-400 ml-1.5">(Tú)</span>
                        )}
                        {isDisconnected && (
                          <span className="text-xs text-amber-400/90 ml-2 italic">
                            (Desconectado)
                          </span>
                        )}
                      </div>
                    </div>

                    <button
                      onClick={() => submitVote(p.player_id)}
                      className={`px-4 py-1.5 rounded-lg border text-sm font-semibold transition-all active:scale-95 ${
                        hasVotedForThis
                          ? 'bg-red-600 border-red-400 text-white shadow-md shadow-red-900/30'
                          : 'bg-slate-800 border-slate-600 text-slate-200 hover:bg-slate-700 hover:border-slate-500'
                      }`}
                    >
                      {hasVotedForThis ? 'Votado ✓' : 'Votar'}
                    </button>
                  </div>

                  <div className="text-slate-400 text-xs mt-2 pl-5 flex items-center justify-between">
                    <span>
                      Votado por:{' '}
                      <strong className="text-slate-200">
                        {votersForPlayer.length > 0 ? votersForPlayer.join(', ') : 'nadie'}
                      </strong>
                    </span>
                    {votes[p.player_id] && (
                      <span className="text-emerald-400 text-[11px] font-medium flex items-center gap-1">
                        <CheckCircle2 size={12} /> Ha votado
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Resumen de votos emitidos */}
          <div className="text-slate-400 text-xs text-center mt-4">
            Votos emitidos: <span className="text-white font-bold">{totalVotesCast}</span> de{' '}
            <span className="text-white font-bold">{players.length}</span>
            {allConnectedVoted && !allVoted && (
              <span className="text-amber-400 ml-2">
                (Todos los jugadores conectados han votado)
              </span>
            )}
          </div>

          {/* Controles para el Host */}
          {isHost && (
            <div className="mt-6 pt-5 border-t border-slate-700 text-center">
              <button
                onClick={endVoting}
                disabled={totalVotesCast === 0 || alreadyRevealed}
                className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold py-3 px-6 rounded-xl transition-all shadow-lg hover:shadow-emerald-900/40 active:scale-95"
              >
                {allVoted
                  ? '¡Todos han votado! Revelar resultados'
                  : `Revelar resultados (${totalVotesCast}/${players.length} votos)`}
              </button>

              {!allVoted && totalVotesCast > 0 && (
                <div className="text-slate-400 text-xs mt-2 flex items-center justify-center gap-1.5 text-amber-300/80">
                  <AlertTriangle size={13} />
                  <span>
                    Puedes revelar ahora con los votos actuales o esperar a que termine el temporizador.
                  </span>
                </div>
              )}

              {totalVotesCast === 0 && (
                <div className="text-slate-500 text-xs mt-2">
                  Esperando al menos un voto para poder revelar...
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
