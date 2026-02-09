
import React from 'react';
import { render, screen } from '@testing-library/react';
import { act } from 'react-dom/test-utils';
import { useGameStore } from '../store/gameStore';
import { NightPhase } from '../components/NightPhase';

// Utilidad para mockear el estado del store
function setPrivateStateMock(state) {
  act(() => {
    useGameStore.setState({ privateState: state });
  });
}

describe('NightPhase - avance de turno', () => {
  afterEach(() => {
    act(() => {
      useGameStore.getState().reset();
    });
  });

  it('muestra "Preparando fase nocturna..." si no hay current_turn_role', () => {
    setPrivateStateMock({});
    render(<NightPhase />);
    expect(screen.getByText(/Preparando fase nocturna/i)).toBeInTheDocument();
  });

  it('muestra el turno del lobo cuando es su turno', () => {
    setPrivateStateMock({
      your_role: 'werewolf',
      current_turn_role: 'werewolf',
      is_your_turn: true,
      night_action: { type: 'can_view_center', message: 'Eres el único lobo.' }
    });
    render(<NightPhase />);
    // Hay dos elementos con "Fase: werewolf" (h1 y h3), así que usamos getAllByText
    const faseElements = screen.getAllByText(/Fase: werewolf/i);
    expect(faseElements.length).toBeGreaterThan(0);
  expect(screen.getByText(/¡Es tu turno!/i)).toBeInTheDocument();
  expect(screen.getAllByText(/Eres el único lobo/i).length).toBeGreaterThan(0);
  });

  it('muestra el turno del masón cuando es su turno', () => {
    setPrivateStateMock({
      your_role: 'mason',
      current_turn_role: 'mason',
      is_your_turn: true,
      night_action: { type: 'show_other_mason', message: 'Tu compañero masón es: 4', other_mason_name: '4' }
    });

  it('muestra el turno de la pitonisa cuando es su turno', () => {
    setPrivateStateMock({
      your_role: 'seer',
      current_turn_role: 'seer',
      is_your_turn: true,
      night_action: { 
        type: 'seer_choose', 
        message: 'Puedes ver la carta de otro jugador o dos cartas del centro.',
        players: [{ id: 'p2', name: 'Ana' }],
        center_positions: [0, 1, 2]
      }
    });
    render(<NightPhase />);
    const faseElements = screen.getAllByText(/Fase: seer/i);
    expect(faseElements.length).toBeGreaterThan(0);
    expect(screen.getByText(/¡Es tu turno!/i)).toBeInTheDocument();
    expect(screen.getByText(/Ver jugador/i)).toBeInTheDocument();
  });
    render(<NightPhase />);
    const faseElements = screen.getAllByText(/Fase: mason/i);
    expect(faseElements.length).toBeGreaterThan(0);
  expect(screen.getByText(/¡Es tu turno!/i)).toBeInTheDocument();
  expect(screen.getAllByText(/Tu compañero masón es: 4/i).length).toBeGreaterThan(0);
  });

  it('muestra mensaje de espera cuando no es tu turno', () => {
    setPrivateStateMock({
      your_role: 'mason',
      current_turn_role: 'werewolf',
      is_your_turn: false,
      night_action: null
    });
    render(<NightPhase />);
    expect(screen.getByText(/Esperando turno de: werewolf/i)).toBeInTheDocument();
  });

  it('avanza correctamente de fase al cambiar current_turn_role', () => {
    // Simula el turno del lobo
    setPrivateStateMock({
      your_role: 'werewolf',
      current_turn_role: 'werewolf',
      is_your_turn: true,
      night_action: { type: 'can_view_center', message: 'Eres el único lobo.' }
    });
    const { rerender } = render(<NightPhase />);
    expect(screen.getAllByText(/Fase: werewolf/i).length).toBeGreaterThan(0);
    // Simula avance a mason
    setPrivateStateMock({
      your_role: 'mason',
      current_turn_role: 'mason',
      is_your_turn: true,
      night_action: { type: 'show_other_mason', message: 'Tu compañero masón es: 4', other_mason_name: '4' }
    });
    rerender(<NightPhase />);
  expect(screen.getAllByText(/Fase: mason/i).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/Tu compañero masón es: 4/i).length).toBeGreaterThan(0);
  });
});
