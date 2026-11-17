// src/components/NightPhase.jsx - VERSIÓN OPTIMIZADA
import React, { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import { Eye } from 'lucide-react';
import { useGameStore } from '../store/gameStore';
import { ROLES, TURN_DURATION } from '../utils/constants';
import { 
  PhaseTimer, 
  WerewolfPhase, 
  MasonPhase, 
  SeerPhase,
  RobberPhase,
  TroublemakerPhase,
  DrunkPhase,
  InsomniacPhase,
  GenericPhase, 
  ActionResult 
} from './night-phases';

const INTRO_DURATION_MS = 1200;
const CLOSING_STAGE_MAX_MS = 550;
const MIN_ACTION_TIME_SEC = 3.5;

const calculateIntroWindowMs = (currentTurn) => {
  if (!currentTurn?.role || currentTurn.role === 'open_eyes') {
    return 0;
  }

  const duration =
    typeof currentTurn.duration === 'number' && currentTurn.duration > 0
      ? currentTurn.duration
      : TURN_DURATION;

  let serverRemainingSec = duration;
  if (typeof currentTurn.end_timestamp === 'number' && typeof currentTurn.server_time === 'number') {
    serverRemainingSec = Math.max(0, currentTurn.end_timestamp - currentTurn.server_time);
  } else if (typeof currentTurn.remaining === 'number') {
    serverRemainingSec = Math.max(0, currentTurn.remaining);
  } else if (typeof currentTurn.timestamp === 'number' && typeof currentTurn.server_time === 'number') {
    const serverElapsed = Math.max(0, currentTurn.server_time - currentTurn.timestamp);
    serverRemainingSec = Math.max(0, duration - serverElapsed);
  } else if (typeof currentTurn.timestamp === 'number') {
    const clientElapsed = Math.max(0, (Date.now() - currentTurn.timestamp * 1000) / 1000);
    serverRemainingSec = Math.max(0, Math.min(duration, duration - clientElapsed));
  }

  let serverElapsedSec = 0;
  if (typeof currentTurn.server_time === 'number' && typeof currentTurn.timestamp === 'number') {
    serverElapsedSec = Math.max(0, currentTurn.server_time - currentTurn.timestamp);
  } else if (typeof currentTurn.end_timestamp === 'number' && typeof currentTurn.server_time === 'number') {
    serverElapsedSec = Math.max(0, duration - serverRemainingSec);
  } else if (typeof currentTurn.remaining === 'number') {
    serverElapsedSec = Math.max(0, duration - currentTurn.remaining);
  } else if (typeof currentTurn.timestamp === 'number') {
    serverElapsedSec = Math.max(0, (Date.now() - currentTurn.timestamp * 1000) / 1000);
  }

  const remainingIntroMs = Math.max(0, INTRO_DURATION_MS - serverElapsedSec * 1000);
  const maxAllowedIntroMs = Math.max(0, (serverRemainingSec - MIN_ACTION_TIME_SEC) * 1000);

  return Math.round(Math.max(0, Math.min(remainingIntroMs, maxAllowedIntroMs)));
};

export const NightPhase = React.memo(() => {
  const {
    gameState,
    privateState,
    currentTurnDisplay: storeTurnDisplay,
    getCurrentTurnRole,
    isMyTurn,
    getNightAction,
    getEffectiveActionResult,
    nightNotes
  } = useGameStore();

  // ✅ NUEVA ARQUITECTURA: Datos desde privateState con turn_timestamp
  const myRole = privateState?.your_role;
  const myOriginalRole = privateState?.your_original_role || myRole;
  const currentTurnRole = getCurrentTurnRole();
  const isCurrentUserTurn = isMyTurn();
  const nightActionData = getNightAction();
  const actionResult = getEffectiveActionResult();
  
  // ✅ CRÍTICO: Crear currentTurn unificado desde storeTurnDisplay y privateState para PhaseTimer
  const currentTurnDisplay = useMemo(() => {
    const role = privateState?.current_turn_role || storeTurnDisplay?.role;
    if (!role) return null;

    const timestamp = privateState?.turn_timestamp ?? storeTurnDisplay?.timestamp;
    const endTimestamp = privateState?.turn_end_timestamp ?? storeTurnDisplay?.end_timestamp;
    const duration = privateState?.turn_duration ?? storeTurnDisplay?.duration ?? TURN_DURATION;
    const remaining = privateState?.turn_remaining ?? storeTurnDisplay?.remaining;
    const serverTime = privateState?.server_time ?? storeTurnDisplay?.server_time;

    return {
      role,
      phase: storeTurnDisplay?.phase || `Fase: ${ROLES[role]?.name || role}`,
      timestamp,
      end_timestamp: endTimestamp,
      duration,
      remaining,
      server_time: serverTime
    };
  }, [
    storeTurnDisplay,
    privateState?.current_turn_role,
    privateState?.turn_timestamp,
    privateState?.turn_end_timestamp,
    privateState?.turn_duration,
    privateState?.turn_remaining,
    privateState?.server_time
  ]);

  const turnKey = currentTurnDisplay?.role
    ? `${currentTurnDisplay.role}_${currentTurnDisplay.timestamp ?? ''}`
    : null;

  const latestTurnDisplayRef = useRef(currentTurnDisplay);
  latestTurnDisplayRef.current = currentTurnDisplay;

  const activeTurnRef = useRef({ key: null, role: null, timestamp: null });
  const timersRef = useRef({ closing: null, ready: null });

  const clearIntroTimers = useCallback(() => {
    if (timersRef.current.closing) {
      clearTimeout(timersRef.current.closing);
      timersRef.current.closing = null;
    }
    if (timersRef.current.ready) {
      clearTimeout(timersRef.current.ready);
      timersRef.current.ready = null;
    }
  }, []);

  useEffect(() => {
    return () => clearIntroTimers();
  }, [clearIntroTimers]);

  const [introState, setIntroState] = useState(() => {
    const initialMs = calculateIntroWindowMs(currentTurnDisplay);
    const initialStage =
      initialMs > 650 ? 'closing' : initialMs > 0 ? 'waking' : 'ready';
    return {
      turnKey: null,
      role: null,
      stage: initialStage,
      totalMs: initialMs,
      previousRole: null
    };
  });

  useEffect(() => {
    const turn = latestTurnDisplayRef.current;

    if (!turnKey || !turn?.role) {
      clearIntroTimers();
      activeTurnRef.current = { key: null, role: null, timestamp: null };
      setIntroState({
        turnKey: null,
        role: null,
        stage: 'ready',
        totalMs: 0,
        previousRole: null
      });
      return;
    }

    const prev = activeTurnRef.current;
    if (prev.key === turnKey) {
      return;
    }

    // Si llega el timestamp oficial del servidor para el mismo rol iniciado milisegundos antes,
    // actualizamos la clave sin reiniciar la transición ni alterar previousRole.
    if (prev.role === turn.role && prev.timestamp == null && turn.timestamp != null) {
      activeTurnRef.current = {
        key: turnKey,
        role: turn.role,
        timestamp: turn.timestamp
      };
      setIntroState(current => ({
        ...current,
        turnKey
      }));
      return;
    }

    clearIntroTimers();

    const prevRole = prev.role && prev.role !== turn.role ? prev.role : null;
    activeTurnRef.current = {
      key: turnKey,
      role: turn.role,
      timestamp: turn.timestamp ?? null
    };

    const introMs = calculateIntroWindowMs(turn);
    if (introMs <= 0) {
      setIntroState({
        turnKey,
        role: turn.role,
        stage: 'ready',
        totalMs: 0,
        previousRole: prevRole
      });
      return;
    }

    const startStage = introMs > 650 ? 'closing' : 'waking';
    setIntroState({
      turnKey,
      role: turn.role,
      stage: startStage,
      totalMs: introMs,
      previousRole: prevRole
    });

    if (startStage === 'closing') {
      const closingMs = Math.min(CLOSING_STAGE_MAX_MS, Math.round(introMs * 0.46));
      timersRef.current.closing = setTimeout(() => {
        timersRef.current.closing = null;
        setIntroState(current =>
          current.role === turn.role && current.turnKey === activeTurnRef.current.key
            ? { ...current, stage: 'waking' }
            : current
        );
      }, closingMs);
    }

    timersRef.current.ready = setTimeout(() => {
      timersRef.current.ready = null;
      setIntroState(current =>
        current.role === turn.role && current.turnKey === activeTurnRef.current.key
          ? { ...current, stage: 'ready' }
          : current
      );
    }, introMs);
  }, [turnKey, clearIntroTimers]);

  const isOpenEyes = currentTurnRole === 'open_eyes';
  const isNewPendingTurn =
    Boolean(turnKey) &&
    !isOpenEyes &&
    introState.turnKey !== turnKey &&
    !(
      introState.turnKey === `${currentTurnRole}_` &&
      currentTurnDisplay?.timestamp != null
    );
  const pendingIntroMs = isNewPendingTurn
    ? calculateIntroWindowMs(currentTurnDisplay)
    : 0;
  const effectiveIntroStage = isNewPendingTurn
    ? pendingIntroMs > 650
      ? 'closing'
      : pendingIntroMs > 0
        ? 'waking'
        : 'ready'
    : introState.stage;
  const effectiveIntroTotalMs = isNewPendingTurn
    ? pendingIntroMs
    : introState.totalMs;
  const effectivePreviousRole = isNewPendingTurn
    ? introState.role && introState.role !== currentTurnRole
      ? introState.role
      : null
    : introState.previousRole;
  const isInteractionLocked = !isOpenEyes && effectiveIntroStage !== 'ready';

  const handleLockedInteractionCapture = useCallback((event) => {
    if (isInteractionLocked) {
      event.preventDefault();
      event.stopPropagation();
    }
  }, [isInteractionLocked]);

  // ✅ OPTIMIZACIÓN: Un solo efecto simplificado para debugging
  useEffect(() => {
    console.log('🌙 NightPhase - Estado actualizado (NUEVA ARQUITECTURA):', {
      currentTurnRole,
      isCurrentUserTurn,
      hasNightAction: !!nightActionData,
      hasActionResult: !!actionResult,
      turn_timestamp: privateState?.turn_timestamp,
      currentTurnDisplay,
      timestamp: Date.now()
    });
  }, [currentTurnRole, isCurrentUserTurn, privateState?.turn_timestamp, currentTurnDisplay, nightActionData, actionResult]);

  // ✅ OPTIMIZACIÓN: Función de render estable sin useMemo/useCallback
  const renderCurrentPhaseInfo = () => {
    if (!currentTurnRole) {
      return (
        <div className="bg-slate-800 rounded-lg p-6 text-center night-turn-transition">
          <p className="text-slate-400">Preparando fase nocturna...</p>
        </div>
      );
    }

    const roleInfo = ROLES[currentTurnRole];
    const prevRoleInfo = effectivePreviousRole ? ROLES[effectivePreviousRole] : null;

    return (
      <div
        key={currentTurnRole}
        className={`night-turn-transition rounded-lg p-6 border ${
          isCurrentUserTurn 
            ? 'bg-yellow-900/30 border-yellow-500 shadow-lg shadow-yellow-900/20' 
            : 'bg-slate-800 border-slate-600'
        }`}
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{isOpenEyes ? '👀' : (roleInfo?.emoji || '❓')}</span>
            <div>
              <h3 className="text-xl font-bold text-white">
                {isOpenEyes ? 'Abrid los ojos todos' : `Fase: ${roleInfo?.name || currentTurnRole}`}
              </h3>
              {isCurrentUserTurn && !isOpenEyes && (
                <p className="text-yellow-400 font-medium">¡Es tu turno!</p>
              )}
            </div>
          </div>
          <PhaseTimer currentTurn={currentTurnDisplay} isMyTurn={isCurrentUserTurn} />
        </div>
        
        {!isOpenEyes && roleInfo && (
          <p className="text-slate-300 mb-4">{roleInfo.description}</p>
        )}

        {/* Transición narrativa de respiro antes de habilitar botones interactivos */}
        {!isOpenEyes && (
          <div
            aria-live="polite"
            className={`transition-all duration-[420ms] ease-out overflow-hidden ${
              isInteractionLocked
                ? 'opacity-100 max-h-52 mb-4 translate-y-0'
                : 'opacity-0 max-h-0 mb-0 -translate-y-2 pointer-events-none'
            }`}
          >
            <div className="bg-slate-900/75 border border-indigo-500/40 rounded-lg p-5 text-center">
              <div key={effectiveIntroStage} className="night-turn-transition night-narrative-pulse">
                {effectiveIntroStage === 'closing' ? (
                  <>
                    <p className="text-lg font-semibold text-indigo-200">
                      😌 Cierra los ojos...
                    </p>
                    <p className="text-sm text-slate-400 mt-1">
                      {prevRoleInfo
                        ? `Termina el turno de ${prevRoleInfo.name}.`
                        : 'La aldea descansa en silencio.'}
                    </p>
                  </>
                ) : (
                  <>
                    <p className="text-lg font-semibold text-amber-200">
                      ✨ Despierta el siguiente rol...
                    </p>
                    <p className="text-sm text-slate-300 mt-1">
                      {isCurrentUserTurn
                        ? `${roleInfo?.emoji || '🌙'} ¡Es tu turno (${roleInfo?.name || currentTurnRole})! Preparando tus opciones...`
                        : `${roleInfo?.emoji || '🌙'} Turno de ${roleInfo?.name || currentTurnRole}`}
                    </p>
                  </>
                )}
              </div>

              {effectiveIntroTotalMs > 0 && (
                <div className="w-full max-w-xs mx-auto h-1.5 bg-slate-700/70 rounded-full overflow-hidden mt-3">
                  <div
                    className="h-full bg-gradient-to-r from-indigo-400 via-purple-400 to-yellow-400 rounded-full"
                    style={{
                      animation: `nightIntroProgress ${effectiveIntroTotalMs}ms linear forwards`
                    }}
                  />
                </div>
              )}
            </div>
          </div>
        )}

        {/* Contenedor interactivo del rol: permanece montado pero bloqueado durante el respiro */}
        <div
          inert={isInteractionLocked ? '' : undefined}
          aria-hidden={isInteractionLocked}
          onClickCapture={handleLockedInteractionCapture}
          className={
            isInteractionLocked
              ? 'pointer-events-none select-none opacity-0 translate-y-2 max-h-0 overflow-hidden'
              : `opacity-100 translate-y-0 max-h-[1200px] pointer-events-auto transition-all duration-500 ease-out${
                  !isOpenEyes ? ' night-controls-reveal' : ''
                }`
          }
        >
          {/* Renderizar componente específico según el rol */}
          {!isOpenEyes && currentTurnRole === 'werewolf' && (
            <WerewolfPhase 
              isMyTurn={isCurrentUserTurn} 
              nightActionData={nightActionData} 
              actionResult={actionResult} 
            />
          )}
          
          {!isOpenEyes && currentTurnRole === 'mason' && (
            <MasonPhase 
              isMyTurn={isCurrentUserTurn} 
              nightActionData={nightActionData} 
            />
          )}

          {!isOpenEyes && currentTurnRole === 'seer' && (
            <SeerPhase
              isMyTurn={isCurrentUserTurn}
              nightActionData={nightActionData}
              actionResult={actionResult}
            />
          )}

          {!isOpenEyes && currentTurnRole === 'robber' && (
            <RobberPhase
              isMyTurn={isCurrentUserTurn}
              nightActionData={nightActionData}
              actionResult={actionResult}
            />
          )}

          {!isOpenEyes && currentTurnRole === 'troublemaker' && (
            <TroublemakerPhase
              isMyTurn={isCurrentUserTurn}
              nightActionData={nightActionData}
              actionResult={actionResult}
            />
          )}

          {!isOpenEyes && currentTurnRole === 'drunk' && (
            <DrunkPhase
              isMyTurn={isCurrentUserTurn}
              nightActionData={nightActionData}
              actionResult={actionResult}
            />
          )}

          {!isOpenEyes && currentTurnRole === 'insomniac' && (
            <InsomniacPhase
              isMyTurn={isCurrentUserTurn}
              nightActionData={nightActionData}
            />
          )}
          
          {!isOpenEyes && currentTurnRole && currentTurnRole !== 'werewolf' && currentTurnRole !== 'mason' && currentTurnRole !== 'seer' && currentTurnRole !== 'robber' && currentTurnRole !== 'troublemaker' && currentTurnRole !== 'drunk' && currentTurnRole !== 'insomniac' && (
            <GenericPhase 
              currentTurnRole={currentTurnRole} 
              isMyTurn={isCurrentUserTurn} 
            />
          )}
        </div>

        {/* Mostrar resultado de acción cuando ya cambió el turno (ej. acción aleatoria al acabar el tiempo) */}
        {!isCurrentUserTurn && actionResult && (
          <ActionResult actionResult={actionResult} />
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="text-4xl mb-4">🌙</div>
          <h1 className="text-3xl font-bold text-white mb-2">
            Noche - Fase: {currentTurnRole ? (ROLES[currentTurnRole]?.name || currentTurnRole) : 'Preparando...'}
          </h1>
          <p className="text-slate-400">
            Los roles actúan en orden durante la noche
          </p>
        </div>

        {/* Tu rol */}
        <div className="bg-slate-800 rounded-lg p-6 mb-6 border border-slate-700">
          <h3 className="text-lg font-bold text-white mb-2">Tu Rol:</h3>
          <div className="flex items-center gap-3">
            <span className="text-3xl">{ROLES[myOriginalRole]?.emoji || '❓'}</span>
            <div>
              <p className="text-xl font-bold text-white">
                {myOriginalRole ? ROLES[myOriginalRole]?.name : 'Desconocido'}
              </p>
              <p className="text-slate-400">
                Rol inicial: {ROLES[myOriginalRole]?.name || myOriginalRole || 'rol no asignado'}
              </p>
              {myRole && myOriginalRole && myRole !== myOriginalRole && (
                <p className="text-amber-300">
                  Rol actual: {ROLES[myRole]?.name || myRole}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Fase actual */}
        {renderCurrentPhaseInfo()}

        {/* Información adicional */}
        <div className="mt-6 bg-slate-800 rounded-lg p-4 border border-slate-700">
          <h4 className="text-white font-bold mb-2 flex items-center gap-2">
            <Eye size={20} />
            Información:
          </h4>
          <div className="text-slate-300 text-sm space-y-1">
            {isCurrentUserTurn ? (
              <p>🎯 Es tu turno.</p>
            ) : (
              <p>⏱️ Esperando turno de: {ROLES[currentTurnRole]?.name || currentTurnRole}</p>
            )}
            <p>🎭 Tu rol inicial: {ROLES[myOriginalRole]?.name || myOriginalRole}</p>
            <p>👥 Jugadores en partida: {gameState?.player_count || 0}</p>
            {privateState?.night_summary ? (
              <p className="text-yellow-400 font-semibold">
                {ROLES[myOriginalRole]?.emoji || '✨'} {privateState.night_summary}
              </p>
            ) : (
              <>
                {nightNotes?.werewolf && myOriginalRole === 'werewolf' && (
                  <p className="text-yellow-400 font-semibold">🐺 {nightNotes.werewolf}</p>
                )}
                {nightNotes?.mason && myOriginalRole === 'mason' && (
                  <p className="text-yellow-400 font-semibold">🔨 {nightNotes.mason}</p>
                )}
                {nightNotes?.seer && myOriginalRole === 'seer' && (
                  <p className="text-yellow-400 font-semibold">🔮 {nightNotes.seer}</p>
                )}
                {privateState?.robber_last_target && myOriginalRole === 'robber' && (
                  <p className="text-yellow-400 font-semibold">
                    🦹 {privateState.robber_last_target.auto ? '🎲 (Aleatoria) ' : ''}Robaste a {privateState.robber_last_target.name} y ahora eres {ROLES[privateState.robber_last_target.new_role || privateState.robber_last_target.role || myRole]?.name || privateState.robber_last_target.new_role || myRole}.
                  </p>
                )}
                {privateState?.troublemaker_last_swap && myOriginalRole === 'troublemaker' && (
                  <p className="text-yellow-400 font-semibold">
                    🎭 {privateState.troublemaker_last_swap.auto ? '🎲 (Aleatoria) ' : ''}Intercambiaste las cartas de {privateState.troublemaker_last_swap.a?.name || privateState.troublemaker_last_swap[0]?.name} y {privateState.troublemaker_last_swap.b?.name || privateState.troublemaker_last_swap[1]?.name}.
                  </p>
                )}
                {privateState?.drunk_last_center !== undefined && myOriginalRole === 'drunk' && (
                  <p className="text-yellow-400 font-semibold">
                    🍺 Recuerda: intercambiaste tu carta con la carta {['izquierda', 'centro', 'derecha'][privateState.drunk_last_center] || 'izquierda'} del centro.
                  </p>
                )}
              </>
            )}
            {/* Mostrar info del turno actual para todos */}
            {currentTurnRole && (
              <div className="mt-2 p-2 rounded bg-slate-900/60 border border-slate-700">
                <span className="font-bold text-cyan-300">Turno actual:</span> <span className="font-mono">{ROLES[currentTurnRole]?.name || currentTurnRole}</span>
                {nightActionData?.message && (
                  <div className="text-slate-400 text-xs mt-1">{nightActionData.message}</div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
});
