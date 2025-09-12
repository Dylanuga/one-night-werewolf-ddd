// src/components/night-phases/GenericPhase.jsx
import React from 'react';
import { ROLES } from '../../utils/constants';

export const GenericPhase = ({ currentTurnRole, isMyTurn }) => {
  const roleInfo = ROLES[currentTurnRole];
  
  if (!roleInfo) return null;

  return (
    <div className="bg-slate-700/50 border border-slate-500 rounded-lg p-6 text-center">
      <h3 className="text-xl font-bold text-white mb-4">
        {roleInfo.emoji} Turno: {roleInfo.name}
      </h3>
      <p className="text-slate-300 mb-2">{roleInfo.description}</p>
      {isMyTurn ? (
        <p className="text-yellow-400 font-medium">¡Es tu turno! Actúa según tu rol.</p>
      ) : (
        <p className="text-slate-400">Esperando a que complete su turno...</p>
      )}
    </div>
  );
};