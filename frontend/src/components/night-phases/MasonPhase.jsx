// src/components/night-phases/MasonPhase.jsx
import React from 'react';

export const MasonPhase = ({ isMyTurn, nightActionData }) => {
  if (!isMyTurn) {
    // Mostrar info del turno actual aunque no seas mason
    return (
      <div className="bg-cyan-900/30 border border-cyan-500 rounded-lg p-6 text-center">
        <h3 className="text-xl font-bold text-cyan-400 mb-4">🔨 Turno: Masón</h3>
        <p className="text-cyan-200 mb-2">Los masones se reconocen entre sí.</p>
        <p className="text-cyan-300 text-sm">Si están solos, observan en silencio.</p>
        {nightActionData?.message && (
          <div className="text-slate-400 text-xs mt-2">{nightActionData.message}</div>
        )}
      </div>
    );
  }

  if (!nightActionData) {
    return (
      <div className="bg-cyan-900/30 border border-cyan-500 rounded-lg p-6 text-center">
        <h3 className="text-xl font-bold text-cyan-400 mb-4">🔨 Masón</h3>
        <p className="text-white">Esperando datos del servidor...</p>
      </div>
    );
  }

  // Caso A: Mostrar el otro masón
  if (nightActionData.type === 'show_other_mason') {
    return (
      <div className="bg-cyan-900/30 border border-cyan-500 rounded-lg p-6 text-center">
        <h3 className="text-xl font-bold text-cyan-400 mb-4">
          🔨 Otros Masones
        </h3>
        <p className="text-white text-lg mb-4">
          {nightActionData.message}
        </p>
        <div className="bg-cyan-800/50 rounded-lg p-4 mt-4">
          <p className="text-cyan-200 font-bold text-2xl">
            🔨 {nightActionData.other_mason_name}
          </p>
          <p className="text-cyan-300 text-sm mt-2">Es tu compañero masón</p>
        </div>
        <p className="text-cyan-200 text-sm mt-4">
          ¡Ambos conocéis vuestra identidad!
        </p>
      </div>
    );
  }

  // Caso B: Masón solo (el otro está en el centro)
  if (nightActionData.type === 'alone') {
    return (
      <div className="bg-cyan-900/30 border border-cyan-500 rounded-lg p-6 text-center">
        <h3 className="text-xl font-bold text-cyan-400 mb-4">
          🔨 Masón Solitario
        </h3>
        <p className="text-white text-lg mb-4">
          {nightActionData.message}
        </p>
        <div className="bg-slate-800/50 rounded-lg p-4 mt-4">
          <p className="text-slate-300 text-lg">😔 Estás solo</p>
          <p className="text-slate-400 text-sm mt-2">
            Tu compañero masón no está en juego (está en el centro)
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-cyan-900/30 border border-cyan-500 rounded-lg p-6 text-center">
      <h3 className="text-xl font-bold text-cyan-400 mb-4">🔨 Masón</h3>
      <p className="text-white">Tipo de acción no reconocido: {nightActionData.type}</p>
    </div>
  );
};