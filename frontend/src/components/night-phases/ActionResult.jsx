// src/components/night-phases/ActionResult.jsx
import React from 'react';
import { ROLES } from '../../utils/constants';

export const ActionResult = ({ actionResult }) => {
  if (!actionResult || !actionResult.success) return null;

  const posNames = ['Izquierda', 'Centro', 'Derecha'];

  return (
    <div className="bg-green-900/30 border border-green-500 rounded-lg p-4 mt-4">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-green-400 font-bold">
          ✓ Resultado de tu acción:
        </h4>
        {actionResult.auto && (
          <span className="text-xs bg-amber-500/20 border border-amber-400/50 text-amber-300 px-2.5 py-0.5 rounded-full font-medium">
            🎲 Acción aleatoria (tiempo agotado)
          </span>
        )}
      </div>
      <p className="text-white font-medium">{actionResult.message}</p>

      {actionResult.seen_player && (
        <p className="text-yellow-300 mt-2 font-semibold">
          🔮 {actionResult.seen_player.name || actionResult.seen_player.player_id} tiene el rol:{' '}
          <span className="text-white underline">
            {ROLES[actionResult.seen_player.role]?.name || actionResult.seen_player.role}
          </span>
        </p>
      )}

      {Array.isArray(actionResult.seen_center) && (
        <div className="text-yellow-300 mt-2 space-y-1 font-semibold">
          {actionResult.seen_center.map((card) => (
            <div key={card.position}>
              🃏 Carta {posNames[card.position] || `#${card.position + 1}`}:{' '}
              <span className="text-white underline">
                {ROLES[card.role]?.name || card.role}
              </span>
            </div>
          ))}
        </div>
      )}

      {actionResult.center_role && actionResult.center_position !== undefined && (
        <p className="text-yellow-300 mt-2 font-semibold">
          🐺 Carta del centro ({posNames[actionResult.center_position] || `#${actionResult.center_position + 1}`}):{' '}
          <span className="text-white underline">
            {ROLES[actionResult.center_role]?.name || actionResult.center_role}
          </span>
        </p>
      )}

      {actionResult.robbed_player && (
        <p className="text-yellow-300 mt-2 font-semibold">
          🦹 Intercambiaste con {actionResult.robbed_player.name}. Tu nuevo rol es:{' '}
          <span className="text-white underline">
            {ROLES[actionResult.new_role || actionResult.robbed_player.role]?.name || actionResult.new_role || actionResult.robbed_player.role}
          </span>
        </p>
      )}

      {actionResult.swapped_players && (
        <p className="text-yellow-300 mt-2 font-semibold">
          🎭 Intercambiaste los roles de{' '}
          <span className="text-white">{actionResult.swapped_players.a?.name || actionResult.swapped_players[0]?.name}</span> y{' '}
          <span className="text-white">{actionResult.swapped_players.b?.name || actionResult.swapped_players[1]?.name}</span>
        </p>
      )}

      {actionResult.center_position !== undefined && !actionResult.center_role && (
        <p className="text-yellow-300 mt-2 font-semibold">
          🍺 Intercambiaste tu carta con la carta del centro:{' '}
          <span className="text-white">{posNames[actionResult.center_position] || `#${actionResult.center_position + 1}`}</span>
        </p>
      )}
    </div>
  );
};