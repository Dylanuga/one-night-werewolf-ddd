// src/components/night-phases/PhaseTimer.jsx
import React, { useState, useEffect, useRef } from 'react';
import { Clock } from 'lucide-react';
import { TURN_DURATION } from '../../utils/constants';

export const PhaseTimer = ({ currentTurn, isMyTurn }) => {
  const [timeLeft, setTimeLeft] = useState(TURN_DURATION);
  const timerRef = useRef(null);
  const endTimeRef = useRef(null);
  const turnKeyRef = useRef(null);

  // ✅ FIX CRÍTICO: Timer visual sincronizado con el tiempo restante real del servidor (sin desfase de reloj)
  useEffect(() => {
    if (!currentTurn?.role) {
      setTimeLeft(TURN_DURATION);
      return;
    }

    const duration = currentTurn?.duration ?? TURN_DURATION;
    const turnKey = `${currentTurn.role}_${currentTurn.timestamp || 0}`;

    // Calcular los segundos restantes reales según el servidor (inmune a desfase de reloj cliente/servidor)
    let serverRemainingSec = duration;
    if (typeof currentTurn.remaining === 'number') {
      serverRemainingSec = Math.max(0, currentTurn.remaining);
    } else if (currentTurn.end_timestamp && currentTurn.server_time) {
      serverRemainingSec = Math.max(0, currentTurn.end_timestamp - currentTurn.server_time);
    } else if (currentTurn.timestamp && currentTurn.server_time) {
      const serverElapsed = Math.max(0, currentTurn.server_time - currentTurn.timestamp);
      serverRemainingSec = Math.max(0, duration - serverElapsed);
    } else if (currentTurn.timestamp) {
      const clientElapsed = Math.max(0, (Date.now() - currentTurn.timestamp * 1000) / 1000);
      serverRemainingSec = Math.max(0, Math.min(duration, duration - clientElapsed));
    }

    const candidateEndTime = Date.now() + serverRemainingSec * 1000;

    // Si es un turno nuevo o hay una resincronización con diferencia > 800ms, actualizar deadline local
    if (
      turnKeyRef.current !== turnKey ||
      !endTimeRef.current ||
      Math.abs(candidateEndTime - endTimeRef.current) > 800
    ) {
      turnKeyRef.current = turnKey;
      endTimeRef.current = candidateEndTime;
    }

    const updateRemaining = () => {
      if (!endTimeRef.current) return;
      const msLeft = Math.max(0, endTimeRef.current - Date.now());
      const secLeft = Math.max(0, Math.round(msLeft / 1000));
      setTimeLeft(secLeft);

      if (msLeft <= 0 && timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };

    updateRemaining();

    if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    timerRef.current = setInterval(updateRemaining, 200);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [
    currentTurn?.role,
    currentTurn?.timestamp,
    currentTurn?.end_timestamp,
    currentTurn?.duration,
    currentTurn?.remaining,
    currentTurn?.server_time
  ]);

  // Aplicar clases de CSS según el tiempo restante
  const getTimerClasses = () => {
    if (timeLeft === 0) return 'text-red-400';
    if (timeLeft <= 2) return 'text-orange-400';
    return 'text-white';
  };

  return (
    <div className="flex items-center gap-2">
      <Clock size={20} className={timeLeft <= 2 ? 'animate-pulse text-orange-400' : 'text-white'} />
      <span className={`font-bold text-lg ${getTimerClasses()}`}>
        {timeLeft}s
      </span>
    </div>
  );
};
