// src/components/RevealPhase.jsx
import React from 'react';
import { RotateCcw, Home, Trophy, Skull, UserCheck, ShieldAlert } from 'lucide-react';
import { useGameStore } from '../store/gameStore';
import { ROLES } from '../utils/constants';

export const RevealPhase = () => {
  const { revealData, gameState, privateState, playerName, resetGame } = useGameStore();

  if (!revealData) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 flex items-center justify-center p-4">
        <div className="bg-slate-800 rounded-lg p-8 border border-slate-700 text-center">
          <div className="text-4xl mb-4 animate-bounce">🏁</div>
          <h2 className="text-2xl font-bold text-white mb-2">Revelación</h2>
          <p className="text-slate-400">Calculando resultados finales de la noche...</p>
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

  // Identificar al jugador actual
  const myRow = rows.find(r => r.name === playerName);
  const myFinalRole = myRow?.final;
  const myOriginalRole = myRow?.original;
  const amIEliminated = myRow?.eliminated;
  const winningPlayerIds = winners?.winning_player_ids || [];

  // Determinar si el jugador actual ha ganado
  let didIWin = false;
  if (myRow) {
    if (winningPlayerIds.length > 0) {
      didIWin = winningPlayerIds.includes(myRow.id);
    } else {
      if (winners?.team === 'tanner') {
        didIWin = (myFinalRole === 'tanner' && amIEliminated);
      } else if (winners?.team === 'werewolves') {
        didIWin = (myFinalRole === 'werewolf');
      } else if (winners?.team === 'villagers') {
        didIWin = (myFinalRole !== 'werewolf' && myFinalRole !== 'tanner');
      }
    }
  }

  // Generar mensajes altamente personalizados según rol y desenlace
  const getPersonalizedOutcome = () => {
    if (!myRow) {
      return {
        isVictory: false,
        icon: '🏁',
        title: 'Fin de la Partida',
        badge: 'Resultados Generales',
        subtitle: winners?.message || 'La partida ha concluido.'
      };
    }

    const roleChanged = myOriginalRole && myFinalRole && myOriginalRole !== myFinalRole;
    const roleChangedNote = roleChanged 
      ? ` (Empezaste la noche como ${ROLES[myOriginalRole]?.name || myOriginalRole}, pero tu rol final fue ${ROLES[myFinalRole]?.name || myFinalRole}).`
      : '';

    if (didIWin) {
      if (myFinalRole === 'tanner') {
        return {
          isVictory: true,
          icon: '🪣🎉',
          title: '¡HAS GANADO!',
          badge: 'Victoria en Solitario (Curtidor)',
          subtitle: `¡Conseguiste que el pueblo te linchara! Justo lo que querías para liberarte de tu miserable trabajo.${roleChangedNote}`
        };
      }
      if (myFinalRole === 'werewolf') {
        return {
          isVictory: true,
          icon: '🐺👑',
          title: '¡HAS GANADO!',
          badge: 'Victoria de la Manada',
          subtitle: `¡Engañasteis al pueblo con maestría! Ningún hombre lobo fue descubierto ni linchado.${roleChangedNote}`
        };
      }
      // Equipo de los aldeanos
      const lynchedWolves = rows.filter(r => r.final === 'werewolf' && r.eliminated);
      if (lynchedWolves.length > 0) {
        const names = lynchedWolves.map(w => w.name).join(', ');
        return {
          isVictory: true,
          icon: '👨‍🌾🎉',
          title: '¡HAS GANADO!',
          badge: 'Victoria de la Aldea',
          subtitle: `¡Pillasteis al lobo! El pueblo descubrió la verdad y linchó a ${names}.${roleChangedNote}`
        };
      } else {
        return {
          isVictory: true,
          icon: '🌾✨',
          title: '¡HAS GANADO!',
          badge: 'Victoria de la Aldea',
          subtitle: `¡Paz en el pueblo! No había ningún hombre lobo entre los presentes y la aldea está a salvo.${roleChangedNote}`
        };
      }
    } else {
      // Derrota
      if (myFinalRole === 'tanner') {
        return {
          isVictory: false,
          icon: '🪣💀',
          title: '¡HAS PERDIDO!',
          badge: 'Sobreviviste a la Votación',
          subtitle: `Nadie te votó para lincharte. Sigues con vida y mañana tendrás que volver a curtir pieles.${roleChangedNote}`
        };
      }
      if (myFinalRole === 'werewolf') {
        if (amIEliminated) {
          return {
            isVictory: false,
            icon: '🐺💀',
            title: '¡HAS PERDIDO!',
            badge: 'Fuiste Descubierto y Linchado',
            subtitle: `¡Los aldeanos te descubrieron! El pueblo te votó mayoritariamente y fuiste ejecutado como hombre lobo.${roleChangedNote}`
          };
        } else {
          return {
            isVictory: false,
            icon: '🐺💀',
            title: '¡HAS PERDIDO!',
            badge: 'Un Lobo de la Manada Cayó',
            subtitle: `¡Los aldeanos descubrieron a tu manada y lincharon a un hombre lobo! Los lobos pierden.${roleChangedNote}`
          };
        }
      }
      // Aldeano derrotado
      if (winners?.team === 'tanner') {
        return {
          isVictory: false,
          icon: '🪣🤦‍♂️',
          title: '¡HAS PERDIDO!',
          badge: 'Manipulado por el Curtidor',
          subtitle: `El Curtidor os manipuló para que lo lincharais a él en lugar de cazar a los lobos. ¡Se lleva la victoria él solo!${roleChangedNote}`
        };
      }
      if (winners?.team === 'werewolves') {
        return {
          isVictory: false,
          icon: '🐺🩸',
          title: '¡HAS PERDIDO!',
          badge: 'Engañado por los Lobos',
          subtitle: `¡Los hombres lobo os engañaron! Ningún lobo fue eliminado en las votaciones y la bestia triunfa.${roleChangedNote}`
        };
      }
      return {
        isVictory: false,
        icon: '💀',
        title: '¡HAS PERDIDO!',
        badge: 'Derrota',
        subtitle: `Tu equipo no ha conseguido la victoria en esta partida.${roleChangedNote}`
      };
    }
  };

  const outcome = getPersonalizedOutcome();

  // Determinar si el jugador actual es host
  const state = gameState || privateState;
  const host = state?.players?.find(p => p.is_host);
  const isHost = host?.name && playerName === host.name;

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 p-4 py-8">
      <div className="max-w-3xl mx-auto space-y-6">
        
        {/* BANNER PERSONALIZADO DE RESULTADO (VICTORIA / DERROTA) */}
        <div className={`rounded-2xl p-6 sm:p-8 border shadow-2xl text-center transition-all ${
          outcome.isVictory 
            ? 'bg-gradient-to-b from-emerald-950/90 via-emerald-900/50 to-slate-900 border-emerald-500/50 shadow-emerald-900/30' 
            : 'bg-gradient-to-b from-red-950/90 via-red-900/50 to-slate-900 border-red-500/50 shadow-red-900/30'
        }`}>
          <div className="text-5xl sm:text-6xl mb-3 drop-shadow-md">
            {outcome.icon}
          </div>

          <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider mb-2 border ${
            outcome.isVictory 
              ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' 
              : 'bg-red-500/20 text-red-300 border-red-500/40'
          }`}>
            {outcome.badge}
          </span>

          <h2 className={`text-3xl sm:text-4xl font-extrabold tracking-tight mb-3 ${
            outcome.isVictory ? 'text-emerald-300' : 'text-red-300'
          }`}>
            {outcome.title}
          </h2>

          <p className="text-slate-200 text-base sm:text-lg max-w-xl mx-auto leading-relaxed">
            {outcome.subtitle}
          </p>
        </div>

        {/* RESUMEN GLOBAL DE GANADORES */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 sm:p-5 flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-left">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block">
              Resultado Global
            </span>
            <span className="text-slate-200 font-medium text-sm">
              {winners?.message || 'Fin de la noche'}
            </span>
          </div>
          <div className="flex items-center gap-2 bg-slate-800/90 border border-slate-700 px-4 py-2 rounded-lg">
            <Trophy size={18} className="text-amber-400" />
            <span className="text-white font-bold text-sm">
              Ganadores: {
                winners?.team === 'villagers' ? 'Aldea 👨‍🌾' :
                winners?.team === 'werewolves' ? 'Hombres Lobo 🐺' :
                winners?.team === 'tanner' ? 'Curtidor 🪣' : '—'
              }
            </span>
          </div>
        </div>

        {/* LISTA DE JUGADORES Y ROLES FINALES */}
        <div className="bg-slate-900/90 rounded-2xl p-5 sm:p-6 border border-slate-800">
          <h3 className="text-white font-bold text-lg mb-4 flex items-center gap-2">
            <span>🎭</span>
            <span>Identidades Reveladas</span>
          </h3>

          <div className="space-y-2.5">
            {rows.map(row => {
              const isMe = row.name === playerName;
              const originalRoleObj = ROLES[row.original] || { name: row.original, emoji: '❓' };
              const finalRoleObj = ROLES[row.final] || { name: row.final, emoji: '❓' };
              const roleSwapped = row.original !== row.final;

              return (
                <div
                  key={row.id}
                  className={`flex flex-col sm:flex-row sm:items-center justify-between gap-2 rounded-xl border p-3.5 transition-colors ${
                    row.eliminated 
                      ? 'bg-red-950/40 border-red-500/60 shadow-sm' 
                      : isMe 
                        ? 'bg-slate-800/90 border-amber-500/50 shadow-sm ring-1 ring-amber-500/30' 
                        : 'bg-slate-800/40 border-slate-700/60'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <span className="text-lg">{finalRoleObj.emoji || '👤'}</span>
                    <div>
                      <span className="text-white font-semibold text-sm sm:text-base">
                        {row.name}
                      </span>
                      {isMe && (
                        <span className="ml-2 text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 px-1.5 py-0.5 rounded">
                          Tú
                        </span>
                      )}
                      {row.eliminated && (
                        <span className="ml-2 text-xs font-bold bg-red-500/20 text-red-300 border border-red-500/40 px-1.5 py-0.5 rounded">
                          Linchado 💀
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="text-xs sm:text-sm text-slate-300 flex items-center gap-1.5 self-end sm:self-auto">
                    <span className="text-slate-400">Empezó:</span>
                    <span className="font-semibold text-slate-300">{originalRoleObj.name}</span>
                    <span className="text-slate-500">➔</span>
                    <span className="text-slate-400">Final:</span>
                    <span className={`font-bold ${roleSwapped ? 'text-amber-400 underline underline-offset-2' : 'text-emerald-400'}`}>
                      {finalRoleObj.name}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* ACCIONES DE REINICIO DE PARTIDA */}
        {isHost ? (
          <div className="pt-2 flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={() => resetGame('role_selection')}
              className="flex items-center justify-center gap-2 px-6 py-3.5 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-slate-950 font-bold rounded-xl transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-amber-500/25 cursor-pointer"
            >
              <RotateCcw size={18} />
              <span>Jugar otra vez</span>
            </button>
            
            <button
              onClick={() => resetGame('lobby')}
              className="flex items-center justify-center gap-2 px-6 py-3.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-xl transition-all duration-200 border border-slate-700 hover:border-slate-600 cursor-pointer"
            >
              <Home size={18} />
              <span>Volver al Lobby</span>
            </button>
          </div>
        ) : (
          <div className="text-center pt-2">
            <div className="inline-flex items-center gap-2 text-amber-300 text-xs sm:text-sm bg-amber-500/10 px-4 py-2.5 rounded-full border border-amber-500/20">
              <div className="w-2 h-2 bg-amber-400 rounded-full animate-ping" />
              <span>Esperando a que el host inicie una nueva partida o regrese al lobby...</span>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};
