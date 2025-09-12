// src/components/night-phases/ActionResult.jsx
import React from 'react';

export const ActionResult = ({ actionResult }) => {
  if (!actionResult || !actionResult.success) return null;

  return (
    <div className="bg-green-900/30 border border-green-500 rounded-lg p-4 mt-4">
      <h4 className="text-green-400 font-bold mb-2">Resultado:</h4>
      <p className="text-white">{actionResult.message}</p>
    </div>
  );
};