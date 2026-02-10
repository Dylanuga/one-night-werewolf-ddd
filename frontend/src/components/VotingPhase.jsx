// src/components/VotingPhase.jsx
import React from 'react';
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
  const allVoted = players.length > 0 && Object.keys(votes).length > 0 &&
    players.every(p => votes[p.player_id]);
  const host = players.find(p => p.is_host);
  const isHost = host?.name && playerName === host.name;
  const alreadyRevealed = Boolean(revealData) || gameState?.phase === 'game_end';

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 p-4">
      <div className="max-w-3xl mx-auto">
        <div className="bg-slate-800 rounded-lg p-8 border border-slate-700">
          <div className="text-center mb-6">
            <div className="text-4xl mb-4">🗳️</div>
            <h2 className="text-2xl font-bold text-white mb-2">Votación</h2>
            <p className="text-slate-300">
              Elige a un jugador para eliminar.
            </p>
            {myVote && (
              <p className="text-amber-300 mt-2">
                Tu voto actual: <span className="font-bold">{players.find(p => p.player_id === myVote)?.name || myVote}</span>
              </p>
            )}
          </div>

          <div className="grid gap-2">
            {players.map(p => (
              <div key={p.player_id} className="bg-slate-900 border border-slate-700 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <div className="text-white font-medium">{p.name}</div>
                  <button
                    onClick={() => submitVote(p.player_id)}
                    className={`px-3 py-1 rounded border text-sm ${
                      myVote === p.player_id
                        ? 'bg-red-700/60 border-red-400 text-white'
                        : 'bg-slate-800 border-slate-600 text-slate-200'
                    }`}
                  >
                    Votar
                  </button>
                </div>
                <div className="text-slate-400 text-sm mt-2">
                  Votado por:{' '}
                  <span className="text-slate-200">
                    {Object.entries(votes)
                      .filter(([, targetId]) => targetId === p.player_id)
                      .map(([voterId]) => {
                        const voterName = playersById[voterId]?.name || voterId;
                        return voterName === playerName ? `${voterName} (tú)` : voterName;
                      })
                      .join(', ') || 'nadie'}
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div className="text-slate-400 text-sm text-center mt-6">
            La revelación ocurrirá cuando todos hayan votado y el host la confirme.
          </div>

          {isHost && (
            <div className="mt-4 text-center">
              <button
                onClick={endVoting}
                disabled={!allVoted || alreadyRevealed}
                className="bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 text-white font-bold py-2 px-4 rounded-lg"
              >
                Revelar resultados
              </button>
              {!allVoted && (
                <div className="text-slate-400 text-xs mt-2">
                  Esperando a que todos voten...
                </div>
              )}
              {alreadyRevealed && (
                <div className="text-slate-400 text-xs mt-2">
                  Resultados ya revelados.
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
