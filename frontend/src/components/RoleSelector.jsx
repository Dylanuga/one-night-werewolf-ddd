// src/components/RoleSelector.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { Crown, Play, ArrowLeft, Plus, Minus, Eye, Users, Clock, CheckCircle } from 'lucide-react';
import { useGameStore } from '../store/gameStore';
import { useSocket } from '../hooks/useSocket';
import { ROLES } from '../utils/constants';

export const RoleSelector = ({ onBack }) => {
  const { gameState, error } = useGameStore();
  const { setRoles, startGame } = useSocket();
  
  const [selectedRoles, setSelectedRoles] = useState({});
  const [isStarting, setIsStarting] = useState(false);
  // 🆕 NUEVO: Estado para controlar cuándo enviar al servidor
  const [lastSentRoles, setLastSentRoles] = useState('');

  const players = gameState?.players || [];
  const playerCount = players.length;
  const requiredRoles = playerCount + 3; // jugadores + 3 cartas del centro
  const hostPlayer = players.find(p => p.is_host);
  const isHost = hostPlayer && players.some(p => p.is_host);

  // Calcular total de roles seleccionados
  const totalSelected = Object.values(selectedRoles).reduce((sum, count) => sum + count, 0);

  // 🔧 NUEVO: Escuchar cambios de roles del servidor usando useSocket
  const { isConnected } = useSocket();
  
  useEffect(() => {
    const handleRolesSet = (data) => {
      console.log('🔧 ROLES RECIBIDOS DEL SERVIDOR:', data.roles);
      
      // Convertir array de roles a objeto contador
      const roleCount = {};
      data.roles.forEach(role => {
        roleCount[role] = (roleCount[role] || 0) + 1;
      });
      
      setSelectedRoles(roleCount);
    };

    // Escuchar eventos de roles_set desde el gameStore (que los recibe del socket)
    // Por ahora usamos una implementación temporal hasta que se agregue al useSocket
    if (!isHost && isConnected) {
      // El evento ya se maneja en useSocket.js - los roles se sincronizan automáticamente
      console.log('👥 No-host: escuchando cambios de roles...');
    }

    return () => {
      console.log('🧹 RoleSelector cleanup');
    };
  }, [isHost, isConnected]);

  // Inicializar con 2 lobos solo si es host
  useEffect(() => {
    if (isHost) {
      setSelectedRoles(prev => ({ ...prev, werewolf: 2 }));
    }
  }, [isHost]);

  // 🆕 NUEVO: Debounced sender - solo envía cuando para de cambiar por 500ms
  const sendRolesToServer = useCallback((roles) => {
    const rolesArray = [];
    Object.entries(roles).forEach(([type, count]) => {
      for (let i = 0; i < count; i++) {
        rolesArray.push(type);
      }
    });

    const rolesString = JSON.stringify(rolesArray.sort());
    
    // 🎯 SOLO ENVIAR SI ES DIFERENTE AL ÚLTIMO ENVIADO
    if (rolesString !== lastSentRoles && rolesArray.length > 0) {
      console.log('📤 ENVIANDO ROLES AL SERVIDOR:', rolesArray);
      setRoles(rolesArray);
      setLastSentRoles(rolesString);
    } else {
      console.log('⏭️ SKIP: Roles idénticos o vacíos, no enviando');
    }
  }, [setRoles, lastSentRoles]);

  // 🆕 NUEVO: Debouncer para evitar spam
  useEffect(() => {
    if (!isHost) return;

    const timer = setTimeout(() => {
      sendRolesToServer(selectedRoles);
    }, 500); // Esperar 500ms después del último cambio

    return () => clearTimeout(timer);
  }, [selectedRoles, isHost, sendRolesToServer]);

  const updateRoleCount = (roleType, change) => {
    if (!isHost) return; // Solo el host puede cambiar roles
    
    setSelectedRoles(prev => {
      const currentCount = prev[roleType] || 0;
      const newCount = Math.max(0, currentCount + change);
      
      // 🔧 CAMBIO CRÍTICO: Solo actualizar estado local, NO enviar inmediatamente
      return {
        ...prev,
        [roleType]: newCount
      };
    });
  };

  const canStartGame = () => {
    const werewolfCount = selectedRoles.werewolf || 0;
    return (
      isHost &&
      totalSelected === requiredRoles &&
      werewolfCount >= 1 &&
      playerCount >= 3 &&
      playerCount <= 8
    );
  };

  const handleStartGame = async () => {
    if (!canStartGame()) return;
    
    // 🆕 NUEVO: Asegurar que los roles finales se envíen antes de iniciar
    sendRolesToServer(selectedRoles);
    
    // Pequeño delay para asegurar que lleguen al servidor
    setTimeout(() => {
      setIsStarting(true);
      startGame();
      
      setTimeout(() => {
        setIsStarting(false);
      }, 1000);
    }, 200);
  };

  // 🆕 NUEVO: Componente para mostrar roles seleccionados (vista de no-host)
  const RoleDisplay = ({ roleType, roleInfo, count }) => {
    if (count === 0) return null;
    
    return (
      <div className="bg-slate-700 rounded-lg p-4 border border-green-500/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{roleInfo.emoji}</span>
            <div>
              <h4 className="font-bold text-white">{roleInfo.name}</h4>
              <div className="flex items-center gap-2 mt-1">
                <CheckCircle size={14} className="text-green-400" />
                <span className="text-xs text-green-400">
                  {count} en juego
                </span>
              </div>
            </div>
          </div>
          
          <div className="text-center">
            <span className="text-2xl font-bold text-green-400">{count}</span>
            <p className="text-xs text-slate-400">carta{count > 1 ? 's' : ''}</p>
          </div>
        </div>
        
        <p className="text-slate-300 text-sm mt-3 pl-9">{roleInfo.description}</p>
      </div>
    );
  };

  // 🆕 NUEVO: Componente para control de roles (vista de host)
  const RoleControl = ({ roleType, roleInfo }) => {
    const count = selectedRoles[roleType] || 0;
    
    return (
      <div
        className={`bg-slate-800 rounded-lg p-6 border transition-all duration-200 ${
          count > 0 
            ? 'border-yellow-500 bg-slate-700' 
            : 'border-slate-600 hover:border-slate-500'
        }`}
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{roleInfo.emoji}</span>
            <div>
              <h4 className="font-bold text-white text-lg">{roleInfo.name}</h4>
              {count > 0 && (
                <span className="text-xs bg-green-600 px-2 py-1 rounded text-white">
                  Seleccionado: {count}
                </span>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={() => updateRoleCount(roleType, -1)}
              disabled={count === 0}
              className="w-8 h-8 bg-red-600 hover:bg-red-700 disabled:bg-slate-600 disabled:opacity-50 text-white rounded flex items-center justify-center transition-colors"
            >
              <Minus size={16} />
            </button>
            
            <span className="w-8 text-center text-white font-bold text-xl">
              {count}
            </span>
            
            <button
              onClick={() => updateRoleCount(roleType, 1)}
              disabled={totalSelected >= requiredRoles}
              className="w-8 h-8 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 disabled:opacity-50 text-white rounded flex items-center justify-center transition-colors"
            >
              <Plus size={16} />
            </button>
          </div>
        </div>
        
        <p className="text-slate-300 text-sm">{roleInfo.description}</p>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="text-4xl mb-4">🐺</div>
          <h1 className="text-3xl font-bold text-white mb-2">
            {isHost ? 'Selección de Roles' : 'Configuración de la Partida'}
          </h1>
          {!isHost && (
            <div className="flex items-center justify-center gap-2 text-blue-400">
              <Clock size={20} />
              <p>El host está configurando los roles...</p>
            </div>
          )}
        </div>

        {/* Info de la sala */}
        <div className={`bg-slate-800 rounded-lg p-6 mb-6 border ${
          isHost ? 'border-cyan-500' : 'border-blue-500'
        }`}>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-white">
            <div>
              <p className="text-slate-400">Sala:</p>
              <p className="text-xl font-bold">{gameState?.room_code}</p>
            </div>
            <div>
              <p className="text-slate-400">Jugadores conectados:</p>
              <div className="flex items-center gap-2">
                <Users size={16} />
                <span className="text-xl font-bold">{playerCount}</span>
              </div>
            </div>
            <div>
              <p className="text-slate-400">Roles necesarios:</p>
              <p className="text-xl font-bold">{requiredRoles} (jugadores + 3)</p>
            </div>
            <div>
              <p className="text-slate-400">Roles seleccionados:</p>
              <p className={`text-xl font-bold ${
                totalSelected === requiredRoles ? 'text-green-400' : 'text-white'
              }`}>
                {totalSelected}
                {totalSelected === requiredRoles && (
                  <CheckCircle size={20} className="inline ml-2 text-green-400" />
                )}
              </p>
            </div>
          </div>
          
          {isHost ? (
            <div className="mt-4 flex items-center gap-2 text-cyan-400">
              <Crown size={16} />
              <span className="text-sm">Eres el host - configura los roles para comenzar</span>
            </div>
          ) : (
            <div className="mt-4 flex items-center gap-2 text-blue-400">
              <Eye size={16} />
              <span className="text-sm">
                Host actual: <span className="font-semibold text-white">{hostPlayer?.name}</span>
              </span>
            </div>
          )}
        </div>

        {error && (
          <div className="bg-red-900/50 border border-red-500 rounded-lg p-4 mb-6">
            <p className="text-red-200">{error}</p>
          </div>
        )}

        {/* 🆕 NUEVO: Instrucciones diferentes según el rol */}
        <div className="bg-slate-800 rounded-lg p-6 mb-6 border border-slate-700">
          {isHost ? (
            <>
              <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Crown size={20} className="text-yellow-400" />
                Configuración de Roles
              </h3>
              <div className="space-y-2 text-slate-300">
                <p>• Selecciona exactamente {requiredRoles} roles para la partida</p>
                <p>• Se recomienda incluir al menos 1-2 lobos</p>
                <p>• {playerCount} jugadores recibirán roles, 3 cartas irán al centro</p>
                {/* 🆕 NUEVO: Indicador de estado de envío */}
                <div className="flex items-center gap-2 text-xs text-slate-500 mt-2">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                  <span>Los cambios se envían automáticamente cada 500ms</span>
                </div>
              </div>
              {totalSelected === requiredRoles && (
                <div className="mt-4 flex items-center gap-2 text-green-400">
                  <CheckCircle size={16} />
                  <span className="text-sm font-medium">¡Configuración completa! Ya puedes iniciar la partida.</span>
                </div>
              )}
            </>
          ) : (
            <>
              <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Eye size={20} className="text-blue-400" />
                Roles en Esta Partida
              </h3>
              <div className="space-y-2 text-slate-300">
                <p>• El host está seleccionando los roles para la partida</p>
                <p>• Verás aquí qué roles estarán en juego</p>
                <p>• La partida comenzará automáticamente cuando esté todo listo</p>
              </div>
              {totalSelected > 0 && (
                <div className="mt-4 flex items-center gap-2 text-blue-400">
                  <Clock size={16} />
                  <span className="text-sm">
                    Progreso: {totalSelected}/{requiredRoles} roles configurados
                  </span>
                </div>
              )}
            </>
          )}
        </div>

        {/* 🆕 NUEVO: Grid de roles - diferentes vistas según el usuario */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {Object.entries(ROLES).map(([roleType, roleInfo]) => 
            isHost ? (
              <RoleControl key={roleType} roleType={roleType} roleInfo={roleInfo} />
            ) : (
              <RoleDisplay 
                key={roleType} 
                roleType={roleType} 
                roleInfo={roleInfo} 
                count={selectedRoles[roleType] || 0} 
              />
            )
          )}
        </div>

        {/* 🆕 NUEVO: Panel de estado y controles */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div>
              <h3 className="text-lg font-bold text-white mb-2">
                {isHost ? 'Resumen de Configuración' : 'Estado de la Partida'}
              </h3>
              
              {totalSelected > 0 ? (
                <div className="flex flex-wrap gap-2 mb-3">
                  {Object.entries(selectedRoles).map(([roleType, count]) => {
                    if (count === 0) return null;
                    return (
                      <span
                        key={roleType}
                        className="bg-yellow-600 text-white px-3 py-1 rounded-full text-sm font-medium"
                      >
                        {ROLES[roleType].emoji} {ROLES[roleType].name.split(' ')[0]} × {count}
                      </span>
                    );
                  })}
                </div>
              ) : (
                <p className="text-slate-400 mb-3">
                  {isHost ? 'Selecciona roles para comenzar' : 'El host aún no ha seleccionado roles'}
                </p>
              )}
              
              <p className="text-slate-400 text-sm">
                Total: {totalSelected} / {requiredRoles} roles
                {totalSelected === requiredRoles && (
                  <span className="text-green-400 ml-2 font-medium">✓ Configuración completa</span>
                )}
              </p>
            </div>

            <div className="flex gap-3">
              {isHost && (
                <>
                  <button
                    onClick={onBack}
                    className="bg-slate-600 hover:bg-slate-700 text-white font-medium py-3 px-6 rounded-lg transition-colors flex items-center gap-2"
                  >
                    <ArrowLeft size={20} />
                    Volver
                  </button>
                  
                  <button
                    onClick={handleStartGame}
                    disabled={!canStartGame() || isStarting}
                    className="bg-green-600 hover:bg-green-700 disabled:bg-slate-600 disabled:opacity-50 text-white font-bold py-3 px-6 rounded-lg transition-colors flex items-center gap-2"
                  >
                    {isStarting ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        Iniciando...
                      </>
                    ) : (
                      <>
                        <Play size={20} />
                        Iniciar Juego
                      </>
                    )}
                  </button>
                </>
              )}
              
              {!isHost && (
                <div className="text-center">
                  <div className="flex items-center gap-3 text-blue-400 mb-2">
                    <div className="w-3 h-3 bg-blue-400 rounded-full animate-pulse"></div>
                    <p className="text-sm">Esperando al host...</p>
                  </div>
                  {totalSelected === requiredRoles && (
                    <p className="text-xs text-green-400">¡La partida comenzará pronto!</p>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 🆕 NUEVO: Lista de jugadores esperando */}
        {!isHost && (
          <div className="mt-6 bg-slate-800 rounded-lg p-4 border border-slate-700">
            <h4 className="text-white font-bold mb-3 flex items-center gap-2">
              <Users size={16} />
              Jugadores Listos ({playerCount})
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
              {players.map((player) => (
                <div
                  key={player.player_id}
                  className="flex items-center gap-2 bg-slate-700 rounded-lg p-2"
                >
                  <div className={`w-2 h-2 rounded-full ${player.is_connected ? 'bg-green-400' : 'bg-red-400'}`}></div>
                  <span className="text-white text-sm truncate">{player.name}</span>
                  {player.is_host && (
                    <Crown size={12} className="text-yellow-400 flex-shrink-0" />
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 🆕 NUEVO: Debug info para desarrollo */}
        {process.env.NODE_ENV === 'development' && isHost && (
          <div className="mt-6 bg-black/50 rounded p-3 text-xs text-green-400 font-mono">
            <div>Roles actuales: {JSON.stringify(selectedRoles)}</div>
            <div>Último enviado: {lastSentRoles}</div>
            <div>Total seleccionado: {totalSelected}</div>
            <div>Puede iniciar: {canStartGame() ? 'SÍ' : 'NO'}</div>
          </div>
        )}
      </div>
    </div>
  );
};