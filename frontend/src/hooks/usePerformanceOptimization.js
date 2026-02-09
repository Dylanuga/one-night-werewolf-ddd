// src/hooks/usePerformanceOptimization.js
import { useMemo, useCallback, useRef, useEffect } from 'react';

/**
 * Hook avanzado para optimización de performance siguiendo React best practices
 */
export const useStableMemo = (factory, deps) => {
  const lastDepsRef = useRef(deps);
  const lastResultRef = useRef();

  // Comparación profunda optimizada para evitar re-computaciones innecesarias
  const depsChanged = useMemo(() => {
    if (!lastDepsRef.current) return true;
    if (lastDepsRef.current.length !== deps.length) return true;
    
    return deps.some((dep, index) => {
      const lastDep = lastDepsRef.current[index];
      
      // Comparación especial para objetos simples
      if (typeof dep === 'object' && dep !== null && typeof lastDep === 'object' && lastDep !== null) {
        return JSON.stringify(dep) !== JSON.stringify(lastDep);
      }
      
      return dep !== lastDep;
    });
  }, deps);

  if (depsChanged || lastResultRef.current === undefined) {
    lastResultRef.current = factory();
    lastDepsRef.current = deps;
  }

  return lastResultRef.current;
};

/**
 * Hook para callbacks estables con logging de cambios
 */
export const useStableCallback = (callback, deps, debugName = 'Unknown') => {
  const callbackRef = useRef(callback);
  const depsRef = useRef(deps);

  // Solo actualizar si las dependencias realmente cambiaron
  const needsUpdate = useMemo(() => {
    if (!depsRef.current) return true;
    if (depsRef.current.length !== deps.length) return true;
    
    return deps.some((dep, index) => depsRef.current[index] !== dep);
  }, deps);

  if (needsUpdate) {
    if (process.env.NODE_ENV === 'development' && depsRef.current) {
      console.log(`🔄 CALLBACK UPDATE - ${debugName}:`, {
        oldDeps: depsRef.current,
        newDeps: deps,
        timestamp: new Date().toLocaleTimeString()
      });
    }
    
    callbackRef.current = callback;
    depsRef.current = deps;
  }

  return useCallback((...args) => callbackRef.current(...args), []);
};

/**
 * Hook para prevenir renders innecesarios con whitelist de props importantes
 */
export const useRenderOptimization = (props, importantProps = []) => {
  const lastImportantPropsRef = useRef();

  const optimizedProps = useMemo(() => {
    const importantPropsObj = {};
    
    importantProps.forEach(propName => {
      if (props.hasOwnProperty(propName)) {
        importantPropsObj[propName] = props[propName];
      }
    });

    return importantPropsObj;
  }, importantProps.map(prop => props[prop]));

  // Solo re-render si las props importantes cambiaron
  const shouldRender = useMemo(() => {
    if (!lastImportantPropsRef.current) {
      lastImportantPropsRef.current = optimizedProps;
      return true;
    }

    const hasChanged = Object.keys(optimizedProps).some(key => 
      lastImportantPropsRef.current[key] !== optimizedProps[key]
    );

    if (hasChanged) {
      lastImportantPropsRef.current = optimizedProps;
    }

    return hasChanged;
  }, [optimizedProps]);

  return { shouldRender, optimizedProps };
};

/**
 * Hook para debouncing de efectos que pueden dispararse frecuentemente
 */
export const useDebouncedEffect = (effect, deps, delay = 100) => {
  useEffect(() => {
    const timeoutId = setTimeout(effect, delay);
    return () => clearTimeout(timeoutId);
  }, [...deps, delay]);
};

/**
 * Hook para throttling de funciones (útil para eventos frecuentes)
 */
export const useThrottledCallback = (callback, deps, delay = 100) => {
  const lastCallRef = useRef(0);
  const timeoutRef = useRef();

  return useCallback((...args) => {
    const now = Date.now();
    
    if (now - lastCallRef.current >= delay) {
      lastCallRef.current = now;
      callback(...args);
    } else {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => {
        lastCallRef.current = Date.now();
        callback(...args);
      }, delay - (now - lastCallRef.current));
    }
  }, [...deps, delay]);
};

/**
 * Hook para detectar y prevenir memory leaks
 */
export const useMemoryLeakPrevention = (componentName) => {
  const mountedRef = useRef(true);
  const timersRef = useRef(new Set());
  const listenersRef = useRef(new Map());

  useEffect(() => {
    return () => {
      mountedRef.current = false;
      
      // Limpiar todos los timers registrados
      timersRef.current.forEach(timer => {
        clearTimeout(timer);
        clearInterval(timer);
      });
      
      // Limpiar todos los listeners registrados
      listenersRef.current.forEach((cleanup, listener) => {
        if (typeof cleanup === 'function') {
          cleanup();
        }
      });

      if (process.env.NODE_ENV === 'development') {
        console.log(`🧹 CLEANUP - ${componentName}: Cleaned ${timersRef.current.size} timers and ${listenersRef.current.size} listeners`);
      }
    };
  }, [componentName]);

  const safeSetTimeout = useCallback((callback, delay) => {
    const timeoutId = setTimeout(() => {
      if (mountedRef.current) {
        callback();
      }
      timersRef.current.delete(timeoutId);
    }, delay);
    
    timersRef.current.add(timeoutId);
    return timeoutId;
  }, []);

  const safeSetInterval = useCallback((callback, delay) => {
    const intervalId = setInterval(() => {
      if (mountedRef.current) {
        callback();
      } else {
        clearInterval(intervalId);
        timersRef.current.delete(intervalId);
      }
    }, delay);
    
    timersRef.current.add(intervalId);
    return intervalId;
  }, []);

  const registerListener = useCallback((element, event, handler, options = {}) => {
    const cleanup = () => {
      element.removeEventListener(event, handler, options);
    };

    element.addEventListener(event, handler, options);
    listenersRef.current.set(`${event}_${Date.now()}`, cleanup);
    
    return cleanup;
  }, []);

  return {
    isMounted: () => mountedRef.current,
    safeSetTimeout,
    safeSetInterval,
    registerListener
  };
};