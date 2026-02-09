// src/components/TestingPanel.jsx
import React, { useState, useEffect } from 'react';
import { Play, Square, RotateCcw, Eye, Clock, Users, Settings, ArrowLeft, Plus, Minus } from 'lucide-react';
import { ROLES } from '../utils/constants';

const TestingPanel = ({ onBack }) => {
  const [testStatus, setTestStatus] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  const [turnHistory, setTurnHistory] = useState([]);
  const [presets, setPresets] = useState({});
  const [selectedPreset, setSelectedPreset] = useState('basic_werewolf');
  const [isCreating, setIsCreating] = useState(false);
  const [logs, setLogs] = useState([]);
  const [customPlayers, setCustomPlayers] = useState([
    { name: 'TestPlayer1', role: 'werewolf' },
    { name: 'TestPlayer2', role: 'villager' },
    { name: 'TestPlayer3', role: 'villager' }
  ]);
  const [customCenterRoles, setCustomCenterRoles] = useState(['seer', 'robber', 'villager']);
  const [customAutoStart, setCustomAutoStart] = useState(true);
  const [assignMode, setAssignMode] = useState('player');
  const [selectedPlayerIndex, setSelectedPlayerIndex] = useState(0);
  const [selectedCenterIndex, setSelectedCenterIndex] = useState(0);

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

  const roleKeys = Object.keys(ROLES);

  const addPlayerRow = () => {
    setCustomPlayers(prev => [...prev, { name: `TestPlayer${prev.length + 1}`, role: 'villager' }]);
    setAssignMode('player');
    setSelectedPlayerIndex(customPlayers.length);
  };

  const removePlayerRow = (index) => {
    setCustomPlayers(prev => prev.filter((_, i) => i !== index));
    if (selectedPlayerIndex >= index && selectedPlayerIndex > 0) {
      setSelectedPlayerIndex(selectedPlayerIndex - 1);
    }
  };

  const updatePlayerField = (index, field, value) => {
    setCustomPlayers(prev => prev.map((p, i) => (
      i === index ? { ...p, [field]: value } : p
    )));
  };

  const assignRoleToTarget = (roleKey) => {
    if (assignMode === 'player') {
      setCustomPlayers(prev => prev.map((p, i) => (
        i === selectedPlayerIndex ? { ...p, role: roleKey } : p
      )));
      return;
    }
    setCustomCenterRoles(prev => prev.map((r, i) => (i === selectedCenterIndex ? roleKey : r)));
  };

  const openPlayerTabs = (roomCode, playerNames) => {
    const baseUrl = window.location.origin;
    playerNames.forEach((name) => {
      const url = `${baseUrl}/?autoJoin=1&room=${encodeURIComponent(roomCode)}&name=${encodeURIComponent(name)}`;
      const opened = window.open(url, '_blank', 'noopener,noreferrer');
      if (!opened) {
        addLog(`Popup bloqueado para jugador ${name}. Permite popups para este sitio.`, 'warning');
      }
    });
  };

  const createCustomTestRoom = async () => {
    const players = customPlayers.map(p => p.name.trim()).filter(Boolean);
    const playerRoles = customPlayers.map(p => p.role);
    const centerRoles = customCenterRoles;

    if (players.length < 3) {
      addLog('Se requieren al menos 3 jugadores', 'error');
      return;
    }
    if (players.length > 10) {
      addLog('Se permiten como maximo 10 jugadores', 'error');
      return;
    }
    if (playerRoles.length !== players.length) {
      addLog('La cantidad de roles de jugadores debe coincidir con los jugadores', 'error');
      return;
    }
    if (centerRoles.length !== 3) {
      addLog('El centro debe tener exactamente 3 roles', 'error');
      return;
    }

    const allRoles = [...playerRoles, ...centerRoles];
    const invalidRoles = allRoles.filter(r => !roleKeys.includes(r));
    if (invalidRoles.length > 0) {
      addLog(`Roles invalidos: ${invalidRoles.join(', ')}`, 'error');
      return;
    }

    const werewolfCount = allRoles.filter(r => r === 'werewolf').length;
    const maxWerewolves = Math.max(1, Math.floor(players.length / 2));
    if (werewolfCount < 1) {
      addLog('Se requiere al menos 1 lobo', 'error');
      return;
    }
    if (werewolfCount > maxWerewolves) {
      addLog(`Demasiados lobos (${werewolfCount}). Maximo permitido: ${maxWerewolves}`, 'error');
      return;
    }

    setIsCreating(true);
    addLog('Creando sala TEST personalizada...', 'info');

    try {
      const response = await fetch(`${API_BASE}/test/create-test-room`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          role_distribution: {
            players: playerRoles,
            center: centerRoles
          },
          player_names: players,
          auto_start: customAutoStart
        })
      });

      const data = await response.json();

      if (response.ok) {
        addLog(`Sala TEST creada con ${data.players.length} jugadores`, 'success');
        setTurnHistory([]);
        await checkTestStatus();
        setIsPolling(true);
        openPlayerTabs(data.room_code || 'TEST', players);
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

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Panel de Control */}
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 lg:col-span-3">
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

          {/* Configuracion personalizada */}
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 lg:col-span-6">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <Users size={20} />
              Modo Prueba Personalizado
            </h3>

            <div className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="block text-sm font-medium text-slate-300">
                    Jugadores y roles:
                  </label>
                  <button
                    onClick={addPlayerRow}
                    className="flex items-center gap-1 px-2 py-1 bg-slate-700 hover:bg-slate-600 rounded text-white text-sm"
                  >
                    <Plus size={14} />
                    Agregar
                  </button>
                </div>

                <div className="space-y-2">
                  {customPlayers.map((player, idx) => (
                    <div
                      key={idx}
                      className={`grid grid-cols-1 md:grid-cols-3 gap-2 p-2 rounded border ${
                        assignMode === 'player' && selectedPlayerIndex === idx
                          ? 'border-yellow-500 bg-slate-700/60'
                          : 'border-slate-700 bg-slate-800/40'
                      }`}
                    >
                      <input
                        value={player.name}
                        onChange={(e) => updatePlayerField(idx, 'name', e.target.value)}
                        placeholder={`Jugador ${idx + 1}`}
                        className="bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
                      />
                      <button
                        onClick={() => { setAssignMode('player'); setSelectedPlayerIndex(idx); }}
                        className="flex items-center gap-2 bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white text-left"
                      >
                        <span className="text-xl">{ROLES[player.role]?.emoji || '❓'}</span>
                        <span className="font-medium">{ROLES[player.role]?.name || player.role}</span>
                      </button>
                      <button
                        onClick={() => removePlayerRow(idx)}
                        disabled={customPlayers.length <= 3}
                        className="flex items-center justify-center gap-1 px-2 py-2 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 disabled:opacity-60 rounded text-white"
                      >
                        <Minus size={14} />
                        Quitar
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Roles del centro (3):
                </label>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                  {[0, 1, 2].map((idx) => (
                    <button
                      key={idx}
                      onClick={() => { setAssignMode('center'); setSelectedCenterIndex(idx); }}
                      className={`flex items-center gap-2 px-3 py-2 rounded border ${
                        assignMode === 'center' && selectedCenterIndex === idx
                          ? 'border-yellow-500 bg-slate-700/60'
                          : 'border-slate-700 bg-slate-800/40'
                      }`}
                    >
                      <span className="text-xl">{ROLES[customCenterRoles[idx]]?.emoji || '❓'}</span>
                      <span className="text-white font-medium">
                        Centro {idx + 1}: {ROLES[customCenterRoles[idx]]?.name || customCenterRoles[idx]}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Asignar rol a: {assignMode === 'player'
                    ? `Jugador ${selectedPlayerIndex + 1}`
                    : `Centro ${selectedCenterIndex + 1}`}
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {Object.entries(ROLES).map(([roleKey, roleInfo]) => {
                    const isSelected = assignMode === 'player'
                      ? customPlayers[selectedPlayerIndex]?.role === roleKey
                      : customCenterRoles[selectedCenterIndex] === roleKey;
                    return (
                      <button
                        key={roleKey}
                        onClick={() => assignRoleToTarget(roleKey)}
                        className={`text-left p-3 rounded-lg border transition ${
                          isSelected
                            ? 'border-yellow-400 bg-yellow-900/30'
                            : 'border-slate-700 bg-slate-800/50 hover:bg-slate-700/60'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">{roleInfo.emoji}</span>
                          <div>
                            <div className="text-white font-semibold">{roleInfo.name}</div>
                            <div className="text-slate-400 text-xs">{roleInfo.description}</div>
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              <label className="flex items-center gap-2 text-slate-300 text-sm">
                <input
                  type="checkbox"
                  checked={customAutoStart}
                  onChange={(e) => setCustomAutoStart(e.target.checked)}
                />
                Iniciar juego automaticamente
              </label>

              <button
                onClick={createCustomTestRoom}
                disabled={isCreating}
                className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-slate-600 text-white px-4 py-2 rounded flex items-center justify-center gap-2 transition-colors"
              >
                <Play size={16} />
                {isCreating ? 'Creando...' : 'Crear y abrir pestañas'}
              </button>
            </div>
          </div>

          {/* Estado Actual */}
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 lg:col-span-3">
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
          <div className="space-y-6 lg:col-span-3 lg:col-start-10">
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
