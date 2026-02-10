// src/hooks/useDebugState.js
import { useEffect, useRef } from 'react';

/**
 * Hook personalizado para debugging exhaustivo de cambios de estado
 * 
 * @param {string} stateName - Nombre identificativo del estado para los logs
 * @param {any} state - El estado a monitorear
 * @param {Array} deps - Dependencias específicas para detectar cambios (opcional)
 * @param {Object} options - Opciones de configuración
 * @param {boolean} options.enabled - Si el debugging está habilitado (default: true en desarrollo)
 * @param {boolean} options.deep - Si debe hacer comparación profunda (default: true)
 * @param {boolean} options.logRenders - Si debe logear todos los re-renders (default: false)
 * @param {Array} options.ignoreKeys - Keys a ignorar en comparación profunda
 * @returns {any} El estado sin modificar
 */
export const useDebugState = (stateName, state, deps = [state], options = {}) => {
  const {
    enabled = process.env.NODE_ENV === 'development',
    deep = true,
    logRenders = false,
    ignoreKeys = []
  } = options;

  const prevStateRef = useRef();
  const renderCountRef = useRef(0);
  const lastChangeTimeRef = useRef(Date.now());
  const initTimeRef = useRef(Date.now());

  // ✅ Función para comparación profunda inteligente
  const deepCompare = (prev, current, path = stateName) => {
    if (!enabled) return { hasChanged: false, changes: [] };

    const changes = [];

    // Comparación básica
    if (prev === current) {
      return { hasChanged: false, changes };
    }

    // Si alguno es null/undefined
    if (prev == null || current == null) {
      if (prev !== current) {
        changes.push({
          path,
          type: 'value_change',
          before: prev,
          after: current
        });
      }
      return { hasChanged: changes.length > 0, changes };
    }

    // Si son tipos diferentes
    if (typeof prev !== typeof current) {
      changes.push({
        path,
        type: 'type_change',
        before: `${typeof prev}: ${prev}`,
        after: `${typeof current}: ${current}`
      });
      return { hasChanged: true, changes };
    }

    // Si son primitivos
    if (typeof prev !== 'object' || typeof current !== 'object') {
      if (prev !== current) {
        changes.push({
          path,
          type: 'value_change',
          before: prev,
          after: current
        });
      }
      return { hasChanged: changes.length > 0, changes };
    }

    // Si son arrays
    if (Array.isArray(prev) && Array.isArray(current)) {
      if (prev.length !== current.length) {
        changes.push({
          path: `${path}.length`,
          type: 'array_length_change',
          before: prev.length,
          after: current.length
        });
      }

      const maxLength = Math.max(prev.length, current.length);
      for (let i = 0; i < maxLength; i++) {
        const itemChanges = deepCompare(prev[i], current[i], `${path}[${i}]`);
        changes.push(...itemChanges.changes);
      }

      return { hasChanged: changes.length > 0, changes };
    }

    // Si son objetos
    if (typeof prev === 'object' && typeof current === 'object') {
      const allKeys = new Set([...Object.keys(prev), ...Object.keys(current)]);
      
      for (const key of allKeys) {
        // Ignorar keys especificados
        if (ignoreKeys.includes(key)) continue;

        if (!(key in prev)) {
          changes.push({
            path: `${path}.${key}`,
            type: 'property_added',
            before: undefined,
            after: current[key]
          });
        } else if (!(key in current)) {
          changes.push({
            path: `${path}.${key}`,
            type: 'property_removed',
            before: prev[key],
            after: undefined
          });
        } else {
          const propChanges = deepCompare(prev[key], current[key], `${path}.${key}`);
          changes.push(...propChanges.changes);
        }
      }

      return { hasChanged: changes.length > 0, changes };
    }

    return { hasChanged: false, changes };
  };

  // ✅ Función para formatear logs de manera legible
  const formatLogOutput = (type, data) => {
    const now = Date.now();
    const timeSinceInit = now - initTimeRef.current;
    const timeSinceLastChange = now - lastChangeTimeRef.current;

    const baseLog = {
      component: stateName,
      render: renderCountRef.current,
      timeSinceInit: `${timeSinceInit}ms`,
      timeSinceLastChange: `${timeSinceLastChange}ms`,
      timestamp: new Date().toISOString().split('T')[1].split('.')[0]
    };

    switch (type) {
      case 'init':
        return {
          ...baseLog,
          type: '🆕 INIT',
          state: data.state
        };

      case 'change':
        return {
          ...baseLog,
          type: '🔄 CHANGE',
          changeCount: data.changes.length,
          changes: data.changes,
          previous: data.previous,
          current: data.current
        };

      case 'render':
        return {
          ...baseLog,
          type: '🎨 RENDER',
          reason: 'No state changes detected'
        };

      default:
        return { ...baseLog, type: '❓ UNKNOWN', data };
    }
  };

  // ✅ Efecto principal para detectar cambios
  useEffect(() => {
    renderCountRef.current += 1;

    if (!enabled) return;

    // Primera inicialización
    if (prevStateRef.current === undefined) {
      prevStateRef.current = deep ? JSON.parse(JSON.stringify(state)) : state;
      
      console.log(`🔍 DEBUG ${stateName}:`, formatLogOutput('init', { state }));
      return;
    }

    // Detectar cambios
    const { hasChanged, changes } = deep 
      ? deepCompare(prevStateRef.current, state)
      : { hasChanged: prevStateRef.current !== state, changes: [] };

    if (hasChanged) {
      const logData = formatLogOutput('change', {
        changes,
        previous: prevStateRef.current,
        current: state
      });

      console.group(`🔍 DEBUG ${stateName} - CAMBIO DETECTADO (#${renderCountRef.current})`);
      console.log('📊 Resumen:', logData);
      
      if (changes.length > 0) {
        console.log('📋 Cambios detallados:');
        changes.forEach((change, index) => {
          console.log(`  ${index + 1}. ${change.type} en ${change.path}:`, {
            antes: change.before,
            después: change.after
          });
        });
      }
      
      console.log('📈 Estados completos:', {
        anterior: prevStateRef.current,
        nuevo: state
      });
      console.groupEnd();

      // Actualizar referencias
      prevStateRef.current = deep ? JSON.parse(JSON.stringify(state)) : state;
      lastChangeTimeRef.current = Date.now();

    } else if (logRenders) {
      console.log(`🔍 DEBUG ${stateName}:`, formatLogOutput('render'));
    }

  }, deps);

  // ✅ Efecto para cleanup en unmount
  useEffect(() => {
    return () => {
      if (enabled) {
        console.log(`🧹 DEBUG ${stateName} - CLEANUP:`, {
          totalRenders: renderCountRef.current,
          totalTime: `${Date.now() - initTimeRef.current}ms`
        });
      }
    };
  }, []);

  return state;
};

/**
 * Hook simplificado para debugging básico sin comparación profunda
 */
export const useDebugStateSimple = (stateName, state, deps = [state]) => {
  return useDebugState(stateName, state, deps, { 
    deep: false, 
    logRenders: true 
  });
};

/**
 * Hook para debugging específico de objetos complejos con keys ignoradas
 */
export const useDebugStateObject = (stateName, state, ignoreKeys = [], deps = [state]) => {
  return useDebugState(stateName, state, deps, { 
    deep: true, 
    ignoreKeys,
    logRenders: false 
  });
};

/**
 * Hook para debugging con throttling para estados que cambian muy frecuentemente
 */
export const useDebugStateThrottled = (stateName, state, throttleMs = 500, deps = [state]) => {
  const lastLogTimeRef = useRef(0);
  const pendingLogRef = useRef(null);

  const throttledLog = (logFn) => {
    const now = Date.now();
    if (now - lastLogTimeRef.current >= throttleMs) {
      logFn();
      lastLogTimeRef.current = now;
      
      if (pendingLogRef.current) {
        clearTimeout(pendingLogRef.current);
        pendingLogRef.current = null;
      }
    } else {
      // Programar log pendiente
      if (pendingLogRef.current) {
        clearTimeout(pendingLogRef.current);
      }
      
      pendingLogRef.current = setTimeout(() => {
        logFn();
        lastLogTimeRef.current = Date.now();
        pendingLogRef.current = null;
      }, throttleMs - (now - lastLogTimeRef.current));
    }
  };

  // Override del console.log para throttling
  const originalState = useDebugState(stateName, state, deps, {
    enabled: false // Deshabilitamos logs automáticos
  });

  useEffect(() => {
    throttledLog(() => {
      console.log(`🔍 DEBUG ${stateName} (throttled):`, {
        state,
        timestamp: Date.now()
      });
    });
  }, deps);

  return originalState;
};

export default useDebugState;