// src/components/TestingPanel.jsx
import React, { useState, useEffect } from 'react';
import { Play, Square, RotateCcw, Eye, Clock, Users, Settings, ArrowLeft } from 'lucide-react';

const TestingPanel = ({ onBack }) => {
  const [testStatus, setTestStatus] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  const [turnHistory, setTurnHistory] = useState([]);
  const [presets, setPresets] = useState({});
  const [selectedPreset, setSelectedPreset] = useState('basic_werewolf');
  const [isCreating, setIsCreating] = useState(false);
  const [logs, setLogs] = useState([]);

  const API_BASE = 'http://localhost:5000';

  // Función para agregar logs con timestamp
  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev.slice(-9), { message, type, timestamp }]); // Mantener solo los últimos 10 logs
  };

  // Cargar presets al montar el componente
  useEffect(() => {
    loadPresets();
  }, []);

  const loadPresets = async () => {
    try {
      const response = await fetch(`${API_BASE}/test/presets`);
      if (response.ok) {
        const data = await response.json();
        setPresets(data.presets);
        addLog('Presets cargados correctamente', 'success');
      }
    } catch (error) {
      addLog('Error cargando presets: ' + error.message, 'error');
    }
  };

  // Función para verificar el estado de la sala TEST
  const checkTestStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/test/status`);
      const data = await response.json();
      
      if (response.ok && data.exists) {
        const prevPhase = testStatus?.phase;
        const prevTurn = testStatus?.current_turn_role;
        
        setTestStatus(data);
        
        // Detectar cambios de turno
        if (prevTurn && prevTurn !== data.current_turn_role) {
          const turnChange = {
            from: prevTurn,
            to: data.current_turn_role,
            timestamp: new Date().toLocaleTimeString(),
            phase: data.phase
          };
          setTurnHistory(prev => [...prev.slice(-9), turnChange]); // Mantener últimos 10 cambios
          addLog(`Turno cambió: ${prevTurn} → ${data.current_turn_role}`, 'info');
        }

        // Detectar cambios de fase
        if (prevPhase && prevPhase !== data.phase) {
          addLog(`Fase cambió: ${prevPhase} → ${data.phase}`, 'success');
        }
      } else {
        setTestStatus(null);
      }
    } catch (error) {
      addLog('Error verificando estado: ' + error.message, 'error');
      setTestStatus(null);
    }
  };

  // Polling automático para monitorear cambios
  useEffect(() => {
    let interval;
    if (isPolling) {
      interval = setInterval(checkTestStatus, 1000); // Cada segundo
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isPolling, testStatus]);

  const createTestRoom = async () => {
    if (!presets[selectedPreset]) return;
    
    setIsCreating(true);
    addLog(`Creando sala TEST con preset: ${selectedPreset}`, 'info');
    
    try {
      const response = await fetch(`${API_BASE}/test/create-test-room`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          role_distribution: presets[selectedPreset].role_distribution,
          auto_start: true
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        addLog(`Sala TEST creada exitosamente con ${data.players.length} jugadores`, 'success');
        setTurnHistory([]); // Limpiar historial
        await checkTestStatus();
        setIsPolling(true); // Iniciar monitoreo automático
      } else {
        addLog('Error creando sala: ' + data.error, 'error');
      }
    } catch (error) {
      addLog('Error: ' + error.message, 'error');
    } finally {
      setIsCreating(false);
    }
  };

  const resetTestRoom = async () => {
    try {
      const response = await fetch(`${API_BASE}/test/reset`, { method: 'POST' });
      if (response.ok) {
        addLog('Sala TEST reseteada', 'success');
        setTestStatus(null);
        setTurnHistory([]);
        setIsPolling(false);
      }
    } catch (error) {
      addLog('Error reseteando: ' + error.message, 'error');
    }
  };

  const advanceTurn = async () => {
    try {
      const response = await fetch(`${API_BASE}/test/advance-turn`, { method: 'POST' });
      const data = await response.json();
      
      if (response.ok) {
        addLog(`Turno avanzado manualmente a: ${data.current_turn_role || 'día'}`, 'info');
        await checkTestStatus();
      } else {
        addLog('Error avanzando turno: ' + data.error, 'error');
      }
    } catch (error) {
      addLog('Error: ' + error.message, 'error');
    }
  };

  const togglePolling = () => {
    setIsPolling(!isPolling);
    addLog(isPolling ? 'Monitoreo pausado' : 'Monitoreo iniciado', 'info');
  };

  const getLogIcon = (type) => {
    switch (type) {
      case 'success': return '✅';
      case 'error': return '❌';
      case 'warning': return '⚠️';
      default: return 'ℹ️';
    }
  };

  const getPhaseColor = (phase) => {
    switch (phase) {
      case 'night_phase': return 'text-blue-400';
      case 'day_phase': return 'text-yellow-400';
      case 'lobby': return 'text-green-400';
      default: return 'text-gray-400';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={onBack}
              className="flex items-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors text-white"
            >
              <ArrowLeft size={16} />
              Volver
            </button>
            <div className="flex-1"></div>
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">🧪 Panel de Testing</h1>
          <p className="text-slate-400">Monitoreo en tiempo real de turnos y fases</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Panel de Control */}
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <Settings size={20} />
              Control
            </h3>

            {/* Selector de Preset */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Preset de Configuración:
              </label>
              <select
                value={selectedPreset}
                onChange={(e) => setSelectedPreset(e.target.value)}
                className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
              >
                {Object.entries(presets).map(([key, preset]) => (
                  <option key={key} value={key}>
                    {preset.name} - {preset.description}
                  </option>
                ))}
              </select>
            </div>

            {/* Botones de Control */}
            <div className="space-y-3">
              <button
                onClick={createTestRoom}
                disabled={isCreating}
                className="w-full bg-green-600 hover:bg-green-700 disabled:bg-slate-600 text-white px-4 py-2 rounded flex items-center justify-center gap-2 transition-colors"
              >
                <Play size={16} />
                {isCreating ? 'Creando...' : 'Crear Sala TEST'}
              </button>

              <button
                onClick={togglePolling}
                className={`w-full px-4 py-2 rounded flex items-center justify-center gap-2 transition-colors ${
                  isPolling 
                    ? 'bg-red-600 hover:bg-red-700 text-white' 
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                }`}
              >
                {isPolling ? <Square size={16} /> : <Eye size={16} />}
                {isPolling ? 'Pausar Monitoreo' : 'Iniciar Monitoreo'}
              </button>

              {testStatus && testStatus.phase === 'night_phase' && (
                <button
                  onClick={advanceTurn}
                  className="w-full bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded flex items-center justify-center gap-2 transition-colors"
                >
                  <Clock size={16} />
                  Avanzar Turno Manual
                </button>
              )}

              <button
                onClick={resetTestRoom}
                className="w-full bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded flex items-center justify-center gap-2 transition-colors"
              >
                <RotateCcw size={16} />
                Reset Sala
              </button>
            </div>
          </div>

          {/* Estado Actual */}
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <Users size={20} />
              Estado Actual
            </h3>

            {testStatus ? (
              <div className="space-y-4">
                {/* Información General */}
                <div className="bg-slate-700 rounded p-4">
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-slate-400">Sala:</span>
                      <span className="text-white ml-2 font-mono">{testStatus.room_code}</span>
                    </div>
                    <div>
                      <span className="text-slate-400">Jugadores:</span>
                      <span className="text-white ml-2">{testStatus.players_count}</span>
                    </div>
                    <div>
                      <span className="text-slate-400">Fase:</span>
                      <span className={`ml-2 font-bold ${getPhaseColor(testStatus.phase)}`}>
                        {testStatus.phase}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400">Turno:</span>
                      <span className="text-white ml-2 font-bold">
                        {testStatus.current_turn_role || 'Ninguno'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Lista de Jugadores */}
                <div>
                  <h4 className="text-sm font-medium text-slate-300 mb-2">Jugadores:</h4>
                  <div className="space-y-1 max-h-32 overflow-y-auto">
                    {testStatus.players.map((player, index) => (
                      <div
                        key={index}
                        className="bg-slate-700 rounded px-3 py-2 text-sm flex justify-between items-center"
                      >
                        <span className="text-white">
                          {player.name} {player.is_host && '👑'}
                        </span>
                        <span className="text-slate-300 font-mono text-xs">
                          {player.role}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Indicador de Conexión */}
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${isPolling ? 'bg-green-500 animate-pulse' : 'bg-gray-500'}`}></div>
                  <span className="text-sm text-slate-400">
                    {isPolling ? 'Monitoreando...' : 'Monitoreo pausado'}
                  </span>
                </div>
              </div>
            ) : (
              <div className="text-center text-slate-400 py-8">
                <Users size={48} className="mx-auto mb-4 opacity-50" />
                <p>No hay sala TEST activa</p>
                <p className="text-sm mt-2">Crea una sala para empezar el monitoreo</p>
              </div>
            )}
          </div>

          {/* Historial y Logs */}
          <div className="space-y-6">
            {/* Historial de Turnos */}
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Clock size={20} />
                Historial de Turnos
              </h3>
              
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {turnHistory.length > 0 ? (
                  turnHistory.map((change, index) => (
                    <div key={index} className="bg-slate-700 rounded px-3 py-2 text-sm">
                      <div className="flex justify-between items-center">
                        <span className="text-white">
                          {change.from} → <span className="font-bold">{change.to}</span>
                        </span>
                        <span className="text-slate-400 text-xs">{change.timestamp}</span>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-slate-400 text-center py-4">No hay cambios registrados</p>
                )}
              </div>
            </div>

            {/* Logs del Sistema */}
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <h3 className="text-xl font-bold text-white mb-4">📝 Logs</h3>
              
              <div className="space-y-1 max-h-40 overflow-y-auto">
                {logs.length > 0 ? (
                  logs.map((log, index) => (
                    <div key={index} className="text-sm flex gap-2">
                      <span className="text-slate-400 text-xs min-w-fit">{log.timestamp}</span>
                      <span>{getLogIcon(log.type)}</span>
                      <span className="text-slate-300">{log.message}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-slate-400 text-center py-4">No hay logs aún</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestingPanel;
