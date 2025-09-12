// src/components/night-phases/PhaseTimer.jsx
import React, { useState, useEffect, useRef } from 'react';
import { Clock } from 'lucide-react';
import { TURN_DURATION } from '../../utils/constants';
import { useGameStore } from '../../store/gameStore';

export const PhaseTimer = ({ currentTurnRole, isMyTurn }) => {
  const { addLog } = useGameStore();
  const [timeLeft, setTimeLeft] = useState(TURN_DURATION);
  const timerRef = useRef(null);
  const timerExpiredRef = useRef(false);
  const roleRef = useRef(currentTurnRole);

  // Reset timer cuando cambia el turno
  useEffect(() => {
    console.log('⏱️ PhaseTimer - Nuevo turno:', currentTurnRole);
    
    // Si el rol cambió, registrar en el log
    if (roleRef.current !== currentTurnRole && currentTurnRole) {
      console.log(`⏱️ PhaseTimer - Cambio de rol: ${roleRef.current || 'ninguno'} → ${currentTurnRole}`);
      roleRef.current = currentTurnRole;
    }
    
    if (currentTurnRole) {
      // Reiniciar el timer completamente
      setTimeLeft(TURN_DURATION);
      timerExpiredRef.current = false;
      
      // Limpiar cualquier timer existente
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      
      // Iniciar un nuevo timer de cuenta regresiva
      timerRef.current = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            clearInterval(timerRef.current);
            timerRef.current = null;
            timerExpiredRef.current = true;
            console.log('⏱️ PhaseTimer - Tiempo expirado para:', currentTurnRole);
            
            // Añadir al log cuando expira el tiempo
            addLog(`⏱️ Tiempo agotado para ${currentTurnRole}`);
            
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }

    // Limpiar el timer cuando se desmonta el componente o cambia el turno
    return () => {
      if (timerRef.current) {
        console.log('⏱️ PhaseTimer - Limpiando timer para:', currentTurnRole);
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [currentTurnRole, addLog]);

  // Aplicar clases de CSS según el tiempo restante
  const getTimerClasses = () => {
    if (timeLeft === 0) return 'text-red-400';
    if (timeLeft <= 2) return 'text-orange-400';
    return '';
  };

  return (
    <div className="flex items-center gap-2 text-white">
      <Clock size={20} className={timeLeft <= 2 ? 'animate-pulse' : ''} />
      <span className={`font-bold text-lg ${getTimerClasses()}`}>{timeLeft}s</span>
    </div>
  );
};