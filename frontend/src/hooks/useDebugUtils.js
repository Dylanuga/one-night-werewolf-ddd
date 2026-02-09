// src/hooks/useDebugUtils.js
import { useEffect, useRef, useCallback } from 'react';

/**
 * Hook para debugging de performance y re-renders
 */
export const useDebugRenders = (componentName, props = {}) => {
  const renderCount = useRef(0);
  const prevProps = useRef(props);
  const startTime = useRef(Date.now());

  useEffect(() => {
    renderCount.current += 1;
    const renderTime = Date.now();
    
    // Detectar qué props cambiaron
    const changedProps = {};
    Object.keys(props).forEach(key => {
      if (prevProps.current[key] !== props[key]) {
        changedProps[key] = {
          from: prevProps.current[key],
          to: props[key]
        };
      }
    });

    const hasChangedProps = Object.keys(changedProps).length > 0;

    console.log(`🎨 RENDER #${renderCount.current} - ${componentName}:`, {
      totalRenders: renderCount.current,
      timeSinceMount: `${renderTime - startTime.current}ms`,
      hasChangedProps,
      ...(hasChangedProps && { changedProps }),
      allProps: props
    });

    prevProps.current = { ...props };
  });

  return renderCount.current;
};

/**
 * Hook para debugging de efectos específicos
 */
export const useDebugEffect = (effectName, callback, deps) => {
  const prevDeps = useRef(deps);
  const runCount = useRef(0);

  useEffect(() => {
    runCount.current += 1;
    
    // Detectar qué dependencias cambiaron
    const changedDeps = [];
    deps?.forEach((dep, index) => {
      if (prevDeps.current && prevDeps.current[index] !== dep) {
        changedDeps.push({
          index,
          from: prevDeps.current[index],
          to: dep
        });
      }
    });

    console.log(`⚡ EFFECT #${runCount.current} - ${effectName}:`, {
      totalRuns: runCount.current,
      changedDeps: changedDeps.length > 0 ? changedDeps : 'Initial run or no deps',
      allDeps: deps
    });

    prevDeps.current = deps ? [...deps] : undefined;
    
    return callback();
  }, deps);
};

/**
 * Hook para medir performance de funciones específicas
 */
export const useDebugPerformance = (functionName) => {
  const measurePerformance = useCallback((fn, ...args) => {
    const startTime = performance.now();
    const result = fn(...args);
    const endTime = performance.now();
    
    console.log(`⏱️ PERFORMANCE ${functionName}:`, {
      duration: `${(endTime - startTime).toFixed(2)}ms`,
      args: args.length > 0 ? args : 'No args',
      timestamp: new Date().toISOString()
    });
    
    return result;
  }, [functionName]);

  const measureAsync = useCallback(async (asyncFn, ...args) => {
    const startTime = performance.now();
    try {
      const result = await asyncFn(...args);
      const endTime = performance.now();
      
      console.log(`⏱️ ASYNC PERFORMANCE ${functionName}:`, {
        duration: `${(endTime - startTime).toFixed(2)}ms`,
        status: 'success',
        args: args.length > 0 ? args : 'No args',
        timestamp: new Date().toISOString()
      });
      
      return result;
    } catch (error) {
      const endTime = performance.now();
      
      console.error(`⏱️ ASYNC PERFORMANCE ${functionName} (ERROR):`, {
        duration: `${(endTime - startTime).toFixed(2)}ms`,
        status: 'error',
        error: error.message,
        args: args.length > 0 ? args : 'No args',
        timestamp: new Date().toISOString()
      });
      
      throw error;
    }
  }, [functionName]);

  return { measurePerformance, measureAsync };
};

/**
 * Hook para debugging de lifecycle events
 */
export const useDebugLifecycle = (componentName) => {
  const mountTime = useRef(Date.now());

  useEffect(() => {
    console.log(`🏗️ MOUNT - ${componentName}:`, {
      timestamp: new Date().toISOString()
    });

    return () => {
      const unmountTime = Date.now();
      const lifespan = unmountTime - mountTime.current;
      
      console.log(`🗑️ UNMOUNT - ${componentName}:`, {
        lifespan: `${lifespan}ms`,
        timestamp: new Date().toISOString()
      });
    };
  }, [componentName]);
};

/**
 * Hook para crear snapshots de estado para debugging
 */
export const useDebugSnapshot = (stateName) => {
  const snapshots = useRef([]);
  
  const takeSnapshot = useCallback((state, label = '') => {
    const snapshot = {
      id: snapshots.current.length,
      timestamp: Date.now(),
      label,
      state: JSON.parse(JSON.stringify(state))
    };
    
    snapshots.current.push(snapshot);
    
    console.log(`📸 SNAPSHOT #${snapshot.id} - ${stateName}${label ? ` (${label})` : ''}:`, {
      snapshot,
      totalSnapshots: snapshots.current.length
    });
    
    return snapshot.id;
  }, [stateName]);

  const compareSnapshots = useCallback((id1, id2) => {
    const snap1 = snapshots.current[id1];
    const snap2 = snapshots.current[id2];
    
    if (!snap1 || !snap2) {
      console.warn('⚠️ SNAPSHOT COMPARE: Invalid snapshot IDs');
      return null;
    }
    
    console.group(`🔍 SNAPSHOT COMPARE - ${stateName}: #${id1} vs #${id2}`);
    console.log('Snapshot 1:', snap1);
    console.log('Snapshot 2:', snap2);
    console.log('Time difference:', `${snap2.timestamp - snap1.timestamp}ms`);
    console.groupEnd();
    
    return {
      snap1,
      snap2,
      timeDiff: snap2.timestamp - snap1.timestamp
    };
  }, [stateName]);

  const listSnapshots = useCallback(() => {
    console.table(snapshots.current.map(s => ({
      id: s.id,
      label: s.label || 'No label',
      timestamp: new Date(s.timestamp).toLocaleTimeString()
    })));
  }, []);

  return { takeSnapshot, compareSnapshots, listSnapshots };
};

/**
 * Hook para debugging de eventos y interacciones
 */
export const useDebugEvents = (componentName) => {
  const eventLog = useRef([]);

  const logEvent = useCallback((eventType, eventData = {}) => {
    const event = {
      id: eventLog.current.length,
      timestamp: Date.now(),
      type: eventType,
      data: eventData,
      component: componentName
    };
    
    eventLog.current.push(event);
    
    console.log(`🎯 EVENT #${event.id} - ${componentName}:`, {
      type: eventType,
      data: eventData,
      timestamp: new Date(event.timestamp).toLocaleTimeString()
    });
    
    return event.id;
  }, [componentName]);

  const getEventHistory = useCallback((limit = 10) => {
    const recent = eventLog.current.slice(-limit);
    console.table(recent.map(e => ({
      id: e.id,
      type: e.type,
      timestamp: new Date(e.timestamp).toLocaleTimeString(),
      hasData: Object.keys(e.data).length > 0
    })));
    return recent;
  }, []);

  return { logEvent, getEventHistory };
};

export default {
  useDebugRenders,
  useDebugEffect,
  useDebugPerformance,
  useDebugLifecycle,
  useDebugSnapshot,
  useDebugEvents
};