// src/utils/constants.js

export const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || window.location.origin;

// Logger silencioso en producción, activable en desarrollo con VITE_DEBUG_LOGS=true
const DEBUG_LOGS_ENABLED = import.meta.env.VITE_DEBUG_LOGS === 'true';
export const devLog = (...args) => {
  if (DEBUG_LOGS_ENABLED) {
    console.log(...args);
  }
};

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
    id: 'werewolf',
    name: 'Lobo',
    team: 'werewolves',
    turnOrder: 1,
    maxCount: 2,
    interactionType: 'select_center_cards',
    description: 'Se conocen entre ellos. Si está solo, ve una carta del centro.',
    emoji: '🐺',
    color: '#dc2626'
  },
  mason: {
    id: 'mason',
    name: 'Masón',
    team: 'villagers',
    turnOrder: 2,
    maxCount: 2,
    interactionType: 'passive_info',
    description: 'Se conocen entre ellos (siempre van de 2 en 2).',
    emoji: '🔨',
    color: '#0891b2'
  },
  seer: {
    id: 'seer',
    name: 'Vidente',
    team: 'villagers',
    turnOrder: 3,
    maxCount: 1,
    interactionType: 'select_player_or_center',
    description: 'Ve la carta de otro jugador o dos cartas del centro.',
    emoji: '🔮',
    color: '#7c3aed'
  },
  robber: {
    id: 'robber',
    name: 'Ladrón',
    team: 'villagers',
    turnOrder: 4,
    maxCount: 1,
    interactionType: 'select_one_player',
    description: 'Intercambia su carta con la de otro jugador y la ve.',
    emoji: '🥷',
    color: '#ea580c'
  },
  troublemaker: {
    id: 'troublemaker',
    name: 'Alborotadora',
    team: 'villagers',
    turnOrder: 5,
    maxCount: 1,
    interactionType: 'select_two_players',
    description: 'Intercambia las cartas de otros dos jugadores sin verlas.',
    emoji: '🃏',
    color: '#db2777'
  },
  drunk: {
    id: 'drunk',
    name: 'Borracho',
    team: 'villagers',
    turnOrder: 6,
    maxCount: 1,
    interactionType: 'select_center_cards',
    description: 'Intercambia su carta con una del centro sin verla.',
    emoji: '🍺',
    color: '#ca8a04'
  },
  insomniac: {
    id: 'insomniac',
    name: 'Insomne',
    team: 'villagers',
    turnOrder: 7,
    maxCount: 1,
    interactionType: 'passive_info',
    description: 'Al final de la noche, ve su propia carta (que pudo cambiar).',
    emoji: '😴',
    color: '#6366f1'
  },
  villager: {
    id: 'villager',
    name: 'Aldeano',
    team: 'villagers',
    turnOrder: 999,
    maxCount: 8,
    interactionType: 'none',
    description: 'Sin habilidad especial. Debe deducir quiénes son los lobos.',
    emoji: '👨‍🌾',
    color: '#16a34a'
  },
  hunter: {
    id: 'hunter',
    name: 'Cazador',
    team: 'villagers',
    turnOrder: 999,
    maxCount: 1,
    interactionType: 'none',
    description: 'Si muere, también muere el jugador al que apunte.',
    emoji: '🏹',
    color: '#059669'
  },
  tanner: {
    id: 'tanner',
    name: 'Curtidor',
    team: 'tanner',
    turnOrder: 999,
    maxCount: 1,
    interactionType: 'none',
    description: 'Gana si muere. Odia su vida.',
    emoji: '🪣',
    color: '#8b5cf6'
  }
};

export const TURN_DURATION = 12; // segundos

export const SOCKET_EVENTS = {
  // Cliente -> Servidor
  CREATE_ROOM: 'create_room',
  JOIN_ROOM: 'join_room',
  LEAVE_ROOM: 'leave_room',
  SET_ROLES: 'set_roles',
  START_GAME: 'start_game',
  NIGHT_ACTION: 'night_action',
  END_DISCUSSION: 'end_discussion',
  SUBMIT_VOTE: 'submit_vote',
  END_VOTING: 'end_voting',
  GET_GAME_STATE: 'get_game_state',
  ADVANCE_TURN: 'advance_turn',
  RESET_GAME: 'reset_game',

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
  VOTING_STARTED: 'voting_started',
  VOTE_RECEIVED: 'vote_received',
  REVEAL: 'reveal',
  GAME_END: 'game_end',
  GAME_RESET: 'game_reset',
  GAME_STATE: 'game_state',
  ERROR: 'error'
};
export const MAX_PLAYERS = 8;
export const MIN_PLAYERS = 3;
