/**
 * Script completo para exportar datos detallados de React Developer Tools
 * Ejecutar en la consola del navegador mientras la app está corriendo
 */

window.ReactUIDebugger = {
  // 1. Exportar árbol completo de componentes con props y estado
  exportComponentTree() {
    console.log('📊 Exportando árbol de componentes...');
    
    try {
      // Método 1: Intentar acceder a React DevTools
      const reactDevTools = window.__REACT_DEVTOOLS_GLOBAL_HOOK__;
      
      if (reactDevTools?.renderers && reactDevTools.renderers.size > 0) {
        console.log('🔧 Usando React DevTools...');
        const renderer = Array.from(reactDevTools.renderers.values())[0];
        const rootContainer = document.querySelector('#root');
        
        if (rootContainer) {
          const fiber = renderer?.findFiberByHostInstance?.(rootContainer);
          if (fiber) {
            const componentData = this.extractFiberData(fiber);
            this.downloadJSON(componentData, 'react-component-tree');
            console.log('✅ Árbol de componentes exportado (DevTools):', componentData);
            return componentData;
          }
        }
      }
      
      console.log('🔧 DevTools no disponible, usando método alternativo...');
      
      // Método 2: Acceso directo al React Root
      const rootElement = document.querySelector('#root');
      if (rootElement && rootElement._reactInternalFiber) {
        console.log('🔧 Usando _reactInternalFiber...');
        const componentData = this.extractFiberData(rootElement._reactInternalFiber);
        this.downloadJSON(componentData, 'react-component-tree-fiber');
        console.log('✅ Árbol exportado (fiber):', componentData);
        return componentData;
      }
      
      // Método 3: Buscar en las propiedades del elemento root
      if (rootElement) {
        console.log('🔧 Buscando fiber en propiedades del root...');
        const fiberKey = Object.keys(rootElement).find(key => 
          key.startsWith('__reactInternalInstance') || 
          key.startsWith('__reactFiber') ||
          key.startsWith('_reactInternalFiber')
        );
        
        if (fiberKey) {
          const fiber = rootElement[fiberKey];
          const componentData = this.extractFiberData(fiber);
          this.downloadJSON(componentData, 'react-component-tree-alt');
          console.log('✅ Árbol exportado (alternativo):', componentData);
          return componentData;
        }
      }
      
      // Método 4: Fallback - exportar solo el DOM visible
      console.log('🔧 Usando fallback - solo DOM...');
      const domData = this.exportDOMStructure();
      this.downloadJSON(domData, 'dom-structure-fallback');
      console.log('✅ Estructura DOM exportada:', domData);
      return domData;
      
    } catch (error) {
      console.error('❌ Error exportando árbol de componentes:', error);
      
      // Último recurso - información básica
      const basicInfo = {
        error: error.message,
        timestamp: Date.now(),
        url: window.location.href,
        reactPresent: !!window.React,
        reactVersion: window.React?.version,
        devToolsPresent: !!window.__REACT_DEVTOOLS_GLOBAL_HOOK__,
        rootElement: !!document.querySelector('#root')
      };
      
      this.downloadJSON(basicInfo, 'error-info');
      console.log('📋 Información básica exportada:', basicInfo);
      return basicInfo;
    }
  },
  
  // Método fallback para exportar estructura DOM
  exportDOMStructure() {
    const rootElement = document.querySelector('#root');
    if (!rootElement) return { error: 'Root element not found' };
    
    const extractDOMNode = (element, depth = 0, maxDepth = 8) => {
      if (depth > maxDepth) return { type: 'MAX_DEPTH_REACHED' };
      
      const node = {
        tagName: element.tagName,
        id: element.id,
        className: element.className,
        textContent: element.textContent?.substring(0, 200),
        attributes: {},
        children: [],
        depth
      };
      
      // Extraer atributos importantes
      ['data-testid', 'role', 'aria-label', 'type'].forEach(attr => {
        if (element.hasAttribute(attr)) {
          node.attributes[attr] = element.getAttribute(attr);
        }
      });
      
      // Extraer hijos
      Array.from(element.children).slice(0, 20).forEach(child => {
        node.children.push(extractDOMNode(child, depth + 1, maxDepth));
      });
      
      return node;
    };
    
    return {
      timestamp: Date.now(),
      type: 'DOM_STRUCTURE',
      root: extractDOMNode(rootElement)
    };
  },
  
  // 2. Exportar estado actual de Zustand
  exportZustandState() {
    console.log('📊 Exportando estado de Zustand...');
    
    try {
      // Método 1: Acceso directo a window.useGameStore
      if (window.useGameStore && typeof window.useGameStore.getState === 'function') {
        console.log('🔧 Usando window.useGameStore...');
        const storeState = window.useGameStore.getState();
        const exportData = this.buildZustandExport(storeState);
        this.downloadJSON(exportData, 'zustand-state');
        console.log('✅ Estado de Zustand exportado:', exportData);
        return exportData;
      }
      
      // Método 2: Buscar en todos los elementos React posibles
      console.log('🔧 Buscando store en elementos React...');
      const allElements = document.querySelectorAll('*');
      
      for (const element of allElements) {
        const reactProps = Object.keys(element).find(key => 
          key.startsWith('__reactInternalInstance') || 
          key.startsWith('__reactFiber')
        );
        
        if (reactProps && element[reactProps]) {
          // Buscar en el árbol de componentes
          const storeData = this.findZustandInFiber(element[reactProps]);
          if (storeData) {
            const exportData = this.buildZustandExport(storeData);
            this.downloadJSON(exportData, 'zustand-state-fiber');
            console.log('✅ Estado encontrado en fiber:', exportData);
            return exportData;
          }
        }
      }
      
      // Método 3: Exportar información disponible del store
      console.log('🔧 Método fallback...');
      const fallbackData = {
        timestamp: Date.now(),
        error: 'Store no encontrado',
        windowKeys: Object.keys(window).filter(key => 
          key.includes('store') || key.includes('Store') || key.includes('zustand')
        ),
        reactPresent: !!window.React,
        availableGlobals: Object.keys(window).filter(key => 
          key.startsWith('use') || key.includes('Game')
        )
      };
      
      this.downloadJSON(fallbackData, 'zustand-fallback');
      console.log('📋 Información fallback exportada:', fallbackData);
      return fallbackData;
      
    } catch (error) {
      console.error('❌ Error exportando estado de Zustand:', error);
      const errorData = {
        error: error.message,
        stack: error.stack,
        timestamp: Date.now()
      };
      this.downloadJSON(errorData, 'zustand-error');
      return errorData;
    }
  },
  
  // Construir exportación completa de Zustand
  buildZustandExport(storeState) {
    return {
      timestamp: Date.now(),
      zustandState: {
        // Estados principales
        gameState: storeState.gameState,
        privateState: storeState.privateState,
        currentTurnDisplay: storeState.currentTurnDisplay,
        actionResult: storeState.actionResult,
        
        // Estados de conexión
        isConnected: storeState.isConnected,
        connectionState: storeState.connectionState,
        
        // Estados optimistas
        optimisticState: storeState.optimisticState,
        
        // Estados de formulario
        playerName: storeState.playerName,
        roomCode: storeState.roomCode,
        selectedRoles: storeState.selectedRoles,
        
        // Errores y logs
        error: storeState.error,
        logs: storeState.logs,
        
        // Computados (ejecutar getters de forma segura)
        computed: this.safeGetters(storeState)
      }
    };
  },
  
  // Ejecutar getters de forma segura
  safeGetters(storeState) {
    const computed = {};
    const getters = [
      'getCurrentPhase', 'getPlayerRole', 'isHost', 'getPlayers',
      'getPlayerCount', 'getRoomCode', 'getCurrentTurnRole', 'isMyTurn',
      'getNightAction', 'getEffectiveActionResult', 'canStartGame', 'areRolesComplete'
    ];
    
    getters.forEach(getter => {
      try {
        if (typeof storeState[getter] === 'function') {
          computed[getter] = storeState[getter]();
        }
      } catch (error) {
        computed[getter] = `[Error: ${error.message}]`;
      }
    });
    
    return computed;
  },
  
  // Buscar Zustand en el árbol de fibras
  findZustandInFiber(fiber, depth = 0, maxDepth = 10) {
    if (!fiber || depth > maxDepth) return null;
    
    // Buscar en hooks
    if (fiber.memoizedState) {
      let hook = fiber.memoizedState;
      while (hook) {
        if (hook.memoizedState && typeof hook.memoizedState === 'object') {
          // Verificar si parece un store de Zustand
          if (hook.memoizedState.gameState || hook.memoizedState.privateState) {
            return hook.memoizedState;
          }
        }
        hook = hook.next;
      }
    }
    
    // Buscar en hijos
    let child = fiber.child;
    while (child) {
      const found = this.findZustandInFiber(child, depth + 1, maxDepth);
      if (found) return found;
      child = child.sibling;
    }
    
    return null;
  },
  
  // 3. Monitorear cambios en tiempo real
  startMonitoring(duration = 60000) {
    console.log(`🔍 Iniciando monitoreo por ${duration/1000} segundos...`);
    
    const changes = [];
    const startTime = Date.now();
    
    // Monitorear cambios de Zustand
    if (window.useGameStore) {
      const originalSetState = window.useGameStore.setState;
      window.useGameStore.setState = function(newState, shouldReplace) {
        const changeData = {
          timestamp: Date.now() - startTime,
          type: 'zustand-change',
          oldState: this.getState(),
          newState: typeof newState === 'function' ? newState(this.getState()) : newState,
          stackTrace: new Error().stack.split('\n').slice(0, 5)
        };
        
        changes.push(changeData);
        console.log('🔄 Zustand Change:', changeData);
        
        return originalSetState.call(this, newState, shouldReplace);
      };
    }
    
    // Monitorear errores de React
    const originalConsoleError = console.error;
    console.error = function(...args) {
      changes.push({
        timestamp: Date.now() - startTime,
        type: 'console-error',
        message: args.join(' '),
        stackTrace: new Error().stack.split('\n').slice(0, 5)
      });
      
      return originalConsoleError.apply(console, args);
    };
    
    // Monitorear warnings de React
    const originalConsoleWarn = console.warn;
    console.warn = function(...args) {
      const message = args.join(' ');
      if (message.includes('React') || message.includes('Warning')) {
        changes.push({
          timestamp: Date.now() - startTime,
          type: 'react-warning',
          message: message,
          stackTrace: new Error().stack.split('\n').slice(0, 5)
        });
      }
      
      return originalConsoleWarn.apply(console, args);
    };
    
    // Exportar después del tiempo especificado
    setTimeout(() => {
      this.downloadJSON(changes, 'monitoring-changes');
      console.log('✅ Monitoreo completado. Cambios exportados:', changes);
      
      // Restaurar funciones originales
      if (window.useGameStore) {
        // Nota: en un entorno real necesitarías guardar la referencia original
        console.log('⚠️ Restaurar manualmente las funciones originales');
      }
    }, duration);
    
    return changes;
  },
  
  // 4. Capturar snapshot completo del DOM + React
  captureFullSnapshot() {
    console.log('📸 Capturando snapshot completo...');
    
    const snapshot = {
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      
      // DOM info
      domInfo: {
        title: document.title,
        bodyClassName: document.body.className,
        headContent: document.head.innerHTML.length,
        bodyContent: document.body.innerHTML.length
      },
      
      // Elementos visibles
      visibleElements: Array.from(document.querySelectorAll('*')).map(el => {
        const rect = el.getBoundingClientRect();
        const style = getComputedStyle(el);
        
        return {
          tagName: el.tagName,
          id: el.id,
          className: el.className,
          textContent: el.textContent?.substring(0, 100),
          isVisible: rect.width > 0 && rect.height > 0 && style.display !== 'none',
          position: {
            top: rect.top,
            left: rect.left,
            width: rect.width,
            height: rect.height
          },
          styles: {
            display: style.display,
            visibility: style.visibility,
            opacity: style.opacity,
            zIndex: style.zIndex
          }
        };
      }).filter(el => el.isVisible),
      
      // Performance info
      performanceInfo: {
        memory: performance.memory ? {
          usedJSHeapSize: performance.memory.usedJSHeapSize,
          totalJSHeapSize: performance.memory.totalJSHeapSize,
          jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
        } : null,
        navigation: performance.getEntriesByType('navigation')[0],
        resources: performance.getEntriesByType('resource').length
      }
    };
    
    // Añadir datos de React y Zustand si están disponibles
    try {
      snapshot.reactData = this.exportComponentTree();
    } catch (e) {
      snapshot.reactError = e.message;
    }
    
    try {
      snapshot.zustandData = this.exportZustandState();
    } catch (e) {
      snapshot.zustandError = e.message;
    }
    
    this.downloadJSON(snapshot, 'full-snapshot');
    console.log('✅ Snapshot completo capturado:', snapshot);
    return snapshot;
  },
  
  // Utilidades
  extractFiberData(fiber, depth = 0, maxDepth = 10) {
    if (depth > maxDepth) return { type: 'MAX_DEPTH_REACHED' };
    
    const data = {
      depth,
      type: this.getFiberType(fiber),
      key: fiber.key,
      props: this.sanitizeProps(fiber.memoizedProps),
      state: fiber.memoizedState,
      hooks: this.extractHooks(fiber),
      children: []
    };
    
    // Extraer hijos
    let child = fiber.child;
    while (child && data.children.length < 50) { // Limitar hijos para evitar archivos gigantes
      data.children.push(this.extractFiberData(child, depth + 1, maxDepth));
      child = child.sibling;
    }
    
    return data;
  },
  
  getFiberType(fiber) {
    if (typeof fiber.type === 'string') return fiber.type;
    if (fiber.type?.name) return fiber.type.name;
    if (fiber.type?.displayName) return fiber.type.displayName;
    if (fiber.elementType?.name) return fiber.elementType.name;
    return 'Unknown';
  },
  
  sanitizeProps(props) {
    if (!props) return null;
    
    const sanitized = {};
    for (const [key, value] of Object.entries(props)) {
      // Evitar serializar funciones y elementos complejos
      if (typeof value === 'function') {
        sanitized[key] = '[Function]';
      } else if (React.isValidElement(value)) {
        sanitized[key] = '[ReactElement]';
      } else if (value && typeof value === 'object' && value.constructor === Object) {
        sanitized[key] = this.sanitizeProps(value);
      } else {
        try {
          JSON.stringify(value);
          sanitized[key] = value;
        } catch {
          sanitized[key] = '[Unserializable]';
        }
      }
    }
    return sanitized;
  },
  
  extractHooks(fiber) {
    const hooks = [];
    let hook = fiber.memoizedState;
    let index = 0;
    
    while (hook && index < 20) { // Limitar hooks para evitar loops infinitos
      hooks.push({
        index,
        memoizedState: this.sanitizeValue(hook.memoizedState),
        baseState: this.sanitizeValue(hook.baseState),
        queue: hook.queue ? '[Queue Object]' : null
      });
      
      hook = hook.next;
      index++;
    }
    
    return hooks;
  },
  
  sanitizeValue(value) {
    if (typeof value === 'function') return '[Function]';
    if (React.isValidElement(value)) return '[ReactElement]';
    try {
      JSON.stringify(value);
      return value;
    } catch {
      return '[Unserializable]';
    }
  },
  
  downloadJSON(data, filename) {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
};

// Hacer disponible globalmente
console.log('🛠️ ReactUIDebugger cargado. Comandos disponibles:');
console.log('   ReactUIDebugger.exportComponentTree() - Exportar árbol de componentes');
console.log('   ReactUIDebugger.exportZustandState() - Exportar estado de Zustand');
console.log('   ReactUIDebugger.quickExport() - Exportación rápida garantizada');
console.log('   ReactUIDebugger.startMonitoring(60000) - Monitorear cambios por 60s');
console.log('   ReactUIDebugger.captureFullSnapshot() - Snapshot completo');

// Método rápido garantizado
window.ReactUIDebugger.quickExport = function() {
  console.log('⚡ Exportación rápida...');
  
  const quickData = {
    timestamp: Date.now(),
    url: window.location.href,
    
    // Información del DOM
    domElements: Array.from(document.querySelectorAll('*')).slice(0, 100).map(el => ({
      tag: el.tagName,
      id: el.id,
      class: el.className,
      text: el.textContent?.substring(0, 50)
    })),
    
    // Información de React si está disponible
    reactInfo: {
      present: !!window.React,
      version: window.React?.version,
      devTools: !!window.__REACT_DEVTOOLS_GLOBAL_HOOK__
    },
    
    // Estado del store si está disponible
    storeInfo: {},
    
    // Errores en consola
    consoleErrors: window.console._errors || []
  };
  
  // Intentar capturar estado del store
  try {
    if (window.useGameStore && window.useGameStore.getState) {
      const state = window.useGameStore.getState();
      quickData.storeInfo = {
        hasGameState: !!state.gameState,
        hasPrivateState: !!state.privateState,
        playerName: state.playerName,
        roomCode: state.roomCode,
        phase: state.getCurrentPhase?.() || 'unknown',
        isConnected: state.isConnected,
        errors: state.error
      };
    }
  } catch (e) {
    quickData.storeInfo.error = e.message;
  }
  
  this.downloadJSON(quickData, 'quick-export');
  console.log('✅ Exportación rápida completada:', quickData);
  return quickData;
};