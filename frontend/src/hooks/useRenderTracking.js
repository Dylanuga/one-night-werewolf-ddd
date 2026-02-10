// src/hooks/useRenderTracking.js
import { useRef, useEffect } from 'react';

/**
 * Hook avanzado para tracking de renders y performance
 * Basado en las recomendaciones de React DevTools y best practices
 */
export const useRenderTracking = (componentName, props = {}, options = {}) => {
  const renderCountRef = useRef(0);
  const lastPropsRef = useRef(props);
  const mountTimeRef = useRef(Date.now());
  const lastRenderTimeRef = useRef(Date.now());
  const logFrequencyRef = useRef(options.logFrequency || 10); // Log cada 10 renders por defecto

  renderCountRef.current += 1;
  const currentTime = Date.now();
  const timeSinceMount = currentTime - mountTimeRef.current;
  const timeSinceLastRender = currentTime - lastRenderTimeRef.current;

  // Detectar qué props cambiaron
  const changedProps = {};
  let hasChangedProps = false;

  Object.keys(props).forEach(key => {
    if (lastPropsRef.current[key] !== props[key]) {
      changedProps[key] = {
        from: lastPropsRef.current[key],
        to: props[key]
      };
      hasChangedProps = true;
    }
  });

  // Detectar renders frecuentes (posibles problemas de performance)
  const isFrequentRender = timeSinceLastRender < 16; // Menos de 1 frame (60fps)
  const isExcessiveRenders = renderCountRef.current > 50 && timeSinceMount < 5000; // Más de 50 renders en 5 segundos

  // Logging inteligente - solo cuando es relevante
  const shouldLog = 
    options.forceLog ||
    hasChangedProps ||
    isFrequentRender ||
    isExcessiveRenders ||
    (renderCountRef.current % logFrequencyRef.current === 0);

  if (shouldLog && process.env.NODE_ENV === 'development') {
    const logLevel = isExcessiveRenders ? 'error' : isFrequentRender ? 'warn' : 'log';
    
    console[logLevel](`🔄 RENDER TRACKING - ${componentName}:`, {
      renderCount: renderCountRef.current,
      timeSinceMount: `${timeSinceMount}ms`,
      timeSinceLastRender: `${timeSinceLastRender}ms`,
      hasChangedProps,
      changedProps: hasChangedProps ? changedProps : 'No changes',
      isFrequentRender,
      isExcessiveRenders,
      timestamp: new Date().toLocaleTimeString()
    });

    if (isExcessiveRenders) {
      console.error(`⚠️ PERFORMANCE WARNING: ${componentName} has rendered ${renderCountRef.current} times in ${timeSinceMount}ms!`);
    }
  }

  lastPropsRef.current = props;
  lastRenderTimeRef.current = currentTime;

  // API para logging manual desde el componente
  const logManual = (eventName, data = {}) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`📋 ${componentName} - ${eventName}:`, {
        ...data,
        renderCount: renderCountRef.current,
        timestamp: new Date().toLocaleTimeString()
      });
    }
  };

  return {
    renderCount: renderCountRef.current,
    timeSinceMount,
    hasChangedProps,
    changedProps,
    isFrequentRender,
    isExcessiveRenders,
    logManual
  };
};

/**
 * Hook para tracking de efectos y sus dependencias
 */
export const useEffectTracking = (effectName, dependencies = [], componentName = 'Unknown') => {
  const lastDepsRef = useRef(dependencies);
  const executionCountRef = useRef(0);

  useEffect(() => {
    executionCountRef.current += 1;

    // Detectar qué dependencias cambiaron
    const changedDeps = {};
    let hasChangedDeps = false;

    dependencies.forEach((dep, index) => {
      if (lastDepsRef.current[index] !== dep) {
        changedDeps[`dep_${index}`] = {
          from: lastDepsRef.current[index],
          to: dep
        };
        hasChangedDeps = true;
      }
    });

    if (process.env.NODE_ENV === 'development') {
      console.log(`🎯 EFFECT TRACKING - ${componentName}.${effectName}:`, {
        executionCount: executionCountRef.current,
        hasChangedDeps,
        changedDeps: hasChangedDeps ? changedDeps : 'Initial execution or no changes',
        allDependencies: dependencies,
        timestamp: new Date().toLocaleTimeString()
      });
    }

    lastDepsRef.current = dependencies;
  }, dependencies);

  return {
    executionCount: executionCountRef.current
  };
};

/**
 * Hook para tracking de estado
 */
export const useStateTracking = (stateName, stateValue, componentName = 'Unknown') => {
  const lastValueRef = useRef(stateValue);
  const changeCountRef = useRef(0);

  useEffect(() => {
    if (lastValueRef.current !== stateValue) {
      changeCountRef.current += 1;

      if (process.env.NODE_ENV === 'development') {
        console.log(`📊 STATE TRACKING - ${componentName}.${stateName}:`, {
          changeCount: changeCountRef.current,
          from: lastValueRef.current,
          to: stateValue,
          timestamp: new Date().toLocaleTimeString()
        });
      }

      lastValueRef.current = stateValue;
    }
  }, [stateValue, stateName, componentName]);

  return {
    changeCount: changeCountRef.current
  };
};