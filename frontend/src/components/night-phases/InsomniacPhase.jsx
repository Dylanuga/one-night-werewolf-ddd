// src/components/night-phases/InsomniacPhase.jsx
import React from 'react';
import { useGameStore } from '../../store/gameStore';
import { ROLES } from '../../utils/constants';

export const InsomniacPhase = ({ isMyTurn, nightActionData }) => {
  const { privateState } = useGameStore();
  // ROLES importado de constants

  if (!isMyTurn) {
    return (
      <div className="bg-indigo-900/30 border border-indigo-500 rounded-lg p-6 text-center">
        <h3 className="text-xl font-bold text-indigo-300 mb-4">😴 Turno: Insomne</h3>
        <p className="text-indigo-200 mb-2">Al final de la noche, ve su rol actual.</p>
      </div>
    );
  }

  if (!nightActionData) {
    return (
      <div className="bg-indigo-900/30 border border-indigo-500 rounded-lg p-6 text-center">
        <h3 className="text-xl font-bold text-indigo-300 mb-4">😴 Insomne</h3>
        <p className="text-white">Esperando datos del servidor...</p>
      </div>
    );
  }

  const currentRole = nightActionData.current_role || privateState?.your_role;
  const roleName = ROLES[currentRole]?.name || currentRole;

  return (
    <div className="bg-indigo-900/20 border border-indigo-500 rounded-lg p-6 text-center">
      <h3 className="text-xl font-bold text-indigo-300 mb-4">😴 Tu información</h3>
      <p className="text-indigo-200 mb-4">
        {nightActionData.message}
      </p>
      <div className="bg-indigo-800/40 border border-indigo-400 rounded-lg p-4">
        <p className="text-white text-lg">
          Tu rol actual es: <span className="font-bold text-yellow-300">{roleName}</span>
        </p>
      </div>
    </div>
  );
};
