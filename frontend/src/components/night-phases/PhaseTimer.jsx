// src/components/night-phases/PhaseTimer.jsx
import React, { useState, useEffect } from 'react';
import { Clock } from 'lucide-react';
import { TURN_DURATION } from '../../utils/constants';

export const PhaseTimer = ({ currentTurnRole, isMyTurn }) => {
  const [timeLeft, setTimeLeft] = useState(TURN_DURATION);

  useEffect(() => {
    if (currentTurnRole) {
      setTimeLeft(TURN_DURATION);
      
      const timer = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [currentTurnRole]);

  return (
    <div className="flex items-center gap-2 text-white">
      <Clock size={20} />
      <span className="font-bold text-lg">{timeLeft}s</span>
    </div>
  );
};