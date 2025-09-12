// src/hooks/useSocket.js
// ⚠️ DEPRECADO: Este hook ya no se utiliza
// El socket ahora se maneja centralizadamente en App.jsx y el gameStore
// Todas las funciones del socket están disponibles directamente en useGameStore()

// NOTA: Este archivo se mantiene temporalmente para evitar errores,
// pero debe ser eliminado en el futuro.

console.warn('⚠️ useSocket está DEPRECADO. Usar gameStore directamente.');

export const useSocket = () => {
  console.error('❌ useSocket ya no debe usarse. Utilizar useGameStore() directamente.');
  return {
    isConnected: false,
    createRoom: () => console.error('Usar gameStore.createRoom'),
    joinRoom: () => console.error('Usar gameStore.joinRoom'),
    leaveRoom: () => console.error('Usar gameStore.leaveRoom'),
    setRoles: () => console.error('Usar gameStore.setRoles'),
    startGame: () => console.error('Usar gameStore.startGame'),
    executeNightAction: () => console.error('Usar gameStore.executeNightAction'),
    getGameState: () => console.error('Usar gameStore.getGameState')
  };
};