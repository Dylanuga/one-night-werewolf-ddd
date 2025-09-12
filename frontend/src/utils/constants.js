// src/utils/constants.js

export const SOCKET_URL = 'http://localhost:5000';

export const GAME_PHASES = {
  LOBBY: 'lobby',
  ROLE_SELECTION: 'role_selection',
  NIGHT_PHASE: 'night_phase',
  DAY_PHASE: 'day_phase',
  VOTING: 'voting',
  GAME_END: 'game_end'
};

export const ROLES = {
  werewolf: {
    name: 'Werewolf (Lobo)',
    description: 'Se conocen entre ellos. Si está solo, ve una carta del centro.',
    emoji: '🐺',
    color: '#dc2626'
  },
  villager: {
    name: 'Villager (Aldeano)',
    description: 'Sin habilidad especial. Debe deducir quiénes son los lobos.',
    emoji: '👨‍🌾',
    color: '#16a34a'
  },
  seer: {
    name: 'Seer (Pitonisa)',
    description: 'Ve la carta de otro jugador o dos cartas del centro.',
    emoji: '🔮',
    color: '#7c3aed'
  },
  robber: {
    name: 'Robber (Ladrón)',
    description: 'Intercambia su carta con la de otro jugador y la ve.',
    emoji: '🥷',
    color: '#ea580c'
  },
  troublemaker: {
    name: 'Troublemaker (Alborotadora)',
    description: 'Intercambia las cartas de otros dos jugadores sin verlas.',
    emoji: '🃏',
    color: '#db2777'
  },
  hunter: {
    name: 'Hunter (Cazador)',
    description: 'Si muere, también muere el jugador al que apunte.',
    emoji: '🏹',
    color: '#059669'
  },
  mason: {
    name: 'Mason (Masón)',
    description: 'Se conocen entre ellos (siempre van de 2 en 2).',
    emoji: '🔨',
    color: '#0891b2'
  },
  drunk: {
    name: 'Drunk (Borracho)',
    description: 'Intercambia su carta con una del centro sin verla.',
    emoji: '🍺',
    color: '#ca8a04'
  },
  insomniac: {
    name: 'Insomniac (Insomne)',
    description: 'Al final de la noche, ve su propia carta (que pudo cambiar).',
    emoji: '😴',
    color: '#6366f1'
  },
  tanner: {
    name: 'Tanner (Curtidor)',
    description: 'Gana si muere. Odia su vida.',
    emoji: '🪣',
    color: '#8b5cf6'
  }
};

export const TURN_DURATION = 6; // segundos

export const SOCKET_EVENTS = {
  // Cliente -> Servidor
  CREATE_ROOM: 'create_room',
  JOIN_ROOM: 'join_room',
  LEAVE_ROOM: 'leave_room',
  SET_ROLES: 'set_roles',
  START_GAME: 'start_game',
  NIGHT_ACTION: 'night_action',
  GET_GAME_STATE: 'get_game_state',
  ADVANCE_TURN: 'advance_turn', // 🆕 Nuevo evento para avanzar turno manualmente
  
  // Servidor -> Cliente
  CONNECTED: 'connected',
  ROOM_CREATED: 'room_created',
  ROOM_JOINED: 'room_joined',
  ROOM_LEFT: 'room_left',
  ROLES_SET: 'roles_set',
  GAME_STARTED: 'game_started',
  GAME_UPDATE: 'game_update',
  PRIVATE_UPDATE: 'private_update',
  TURN_START: 'turn_start',
  ACTION_RESULT: 'action_result',
  GAME_STATE: 'game_state',
  ERROR: 'error'
};

export const MAX_PLAYERS = 8;
export const MIN_PLAYERS = 3;