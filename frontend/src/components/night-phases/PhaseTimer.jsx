// src/components/night-phases/PhaseTimer.jsx
import React, { useState, useEffect, useRef } from 'react';
import { Clock } from 'lucide-react';
import { TURN_DURATION } from '../../utils/constants';

export const PhaseTimer = ({ currentTurn, isMyTurn }) => {
  const [timeLeft, setTimeLeft] = useState(TURN_DURATION);
  const timerRef = useRef(null);
  const startTimeRef = useRef(null);

  // ✅ FIX CRÍTICO: Timer puramente visual sincronizado con el servidor
  useEffect(() => {
    console.log('⏰ PhaseTimer - Nuevo currentTurn:', {
      currentTurn,
      timestamp: currentTurn?.timestamp,
      role: currentTurn?.role
    });

    // Limpiar timer anterior
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    if (currentTurn?.timestamp) {
      const serverStartTime = currentTurn.timestamp * 1000;
      startTimeRef.current = serverStartTime;
      
      // Calcular tiempo inicial basado en timestamp del servidor
      const now = Date.now();
      const elapsed = Math.floor((now - serverStartTime) / 1000);
      const duration = currentTurn?.duration ?? TURN_DURATION;
      const initialTime = Math.max(0, duration - elapsed);
      
      console.log('⏰ PhaseTimer - Calculando tiempo:', {
        elapsed,
        initialTime,
        TURN_DURATION,
        duration
      });
      
      setTimeLeft(initialTime);

      // Solo iniciar timer si queda tiempo
      if (initialTime > 0) {
        console.log('⏰ PhaseTimer - Iniciando countdown visual');
        
        timerRef.current = setInterval(() => {
          const currentTime = Date.now();
          const totalElapsed = Math.floor((currentTime - serverStartTime) / 1000);
          const remaining = Math.max(0, duration - totalElapsed);
          
          setTimeLeft(remaining);
          
          if (remaining === 0) {
            console.log('⏰ PhaseTimer - Countdown terminado');
            clearInterval(timerRef.current);
            timerRef.current = null;
          }
        }, 1000);
      } else {
        console.log('⏰ PhaseTimer - Sin tiempo restante');
        setTimeLeft(0);
      }
    } else {
      console.log('⏰ PhaseTimer - Sin timestamp, reseteando');
      setTimeLeft(currentTurn?.duration ?? TURN_DURATION);
    }

    // Cleanup
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [currentTurn?.timestamp, currentTurn?.role]); // ✅ Dependencias específicas

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
