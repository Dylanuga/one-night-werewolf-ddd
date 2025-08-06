// src/components/GameLog.jsx
import React, { useEffect, useRef } from 'react';
import { ScrollText, Clock } from 'lucide-react';
import { useGameStore } from '../store/gameStore';

export const GameLog = ({ isMinimized = false }) => {
  const { gameState, logs } = useGameStore();
  const logEndRef = useRef(null);
  
  const gameLogs = gameState?.logs || [];
  const localLogs = logs || [];
  
  // Combinar logs del servidor y locales, evitando duplicados
  const allLogs = [...gameLogs, ...localLogs].slice(-20);

  // Auto-scroll al final cuando llegan nuevos logs
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [allLogs]);

  const formatTimestamp = (timestamp) => {
    if (typeof timestamp === 'string') {
      return timestamp; // Ya es un timestamp formateado localmente
    }
    
    if (typeof timestamp === 'number') {
      return new Date(timestamp * 1000).toLocaleTimeString();
    }
    
    return new Date().toLocaleTimeString();
  };

  const getLogIcon = (message) => {
    if (message.includes('🐺') || message.includes('lobo')) return '🐺';
    if (message.includes('🌙') || message.includes('noche')) return '🌙';
    if (message.includes('☀️') || message.includes('día')) return '☀️';
    if (message.includes('🎯')) return '🎯';
    if (message.includes('👑') || message.includes('host')) return '👑';
    if (message.includes('se unió') || message.includes('joined')) return '🚪';
    if (message.includes('salió') || message.includes('left')) return '👋';
    if (message.includes('Fase:')) return '⏰';
    if (message.includes('comenzado') || message.includes('started')) return '🎮';
    return '📝';
  };

  const getLogStyle = (message) => {
    if (message.includes('Fase:')) return 'text-yellow-300 font-semibold';
    if (message.includes('🌙') || message.includes('noche')) return 'text-blue-300';
    if (message.includes('☀️') || message.includes('día')) return 'text-orange-300';
    if (message.includes('🎯')) return 'text-green-300';
    if (message.includes('Error') || message.includes('error')) return 'text-red-300';
    return 'text-slate-300';
  };

  if (isMinimized) {
    return (
      <div className="bg-slate-800 rounded-lg p-3 border border-slate-700">
        <div className="flex items-center gap-2 text-slate-400 text-sm">
          <ScrollText size={16} />
          <span>Log del juego ({allLogs.length})</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 rounded-lg border border-slate-700 h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-slate-700">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <ScrollText size={20} />
          Log del juego:
        </h3>
      </div>

      {/* Logs container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2 max-h-80">
        {allLogs.length === 0 ? (
          <div className="text-center text-slate-500 py-8">
            <ScrollText size={48} className="mx-auto mb-2 opacity-50" />
            <p>No hay eventos aún</p>
          </div>
        ) : (
          allLogs.map((log, index) => {
            const timestamp = log.timestamp || log.time || Date.now();
            const message = log.message || log;
            const formattedTime = formatTimestamp(timestamp);
            const icon = getLogIcon(message);
            const style = getLogStyle(message);
            
            return (
              <div
                key={`${timestamp}-${index}`}
                className="flex items-start gap-3 py-1 px-2 rounded hover:bg-slate-700/50 transition-colors"
              >
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <span className="text-lg flex-shrink-0">{icon}</span>
                  <div className="min-w-0 flex-1">
                    <p className={`text-sm ${style} break-words`}>
                      {message}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1 text-xs text-slate-500 flex-shrink-0">
                  <Clock size={12} />
                  {formattedTime}
                </div>
              </div>
            );
          })
        )}
        <div ref={logEndRef} />
      </div>
    </div>
  );
};