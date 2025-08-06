# Orquestación de turnos y lógica del juego

import asyncio
from typing import Dict, List, Optional, Any, Callable
from domain.game_logic import GameLogic, GamePhase
from infrastructure.room_repository import RoomRepository

class GameService:
    """Servicio de aplicación que coordina la lógica del juego"""
    
    def __init__(self, room_repository: RoomRepository, emit_callback: Callable):
        self.room_repository = room_repository
        self.emit_callback = emit_callback  # Callback para emitir eventos Socket.IO
        self.turn_timers: Dict[str, asyncio.Task] = {}  # Timers activos por sala
    
    async def create_room(self, room_code: str, host_id: str, host_name: str, socket_id: str) -> bool:
        """Crea una nueva sala de juego"""
        if self.room_repository.room_exists(room_code):
            return False
        
        game = GameLogic(room_code)
        success = game.add_player(host_id, host_name, socket_id, is_host=True)
        
        if success:
            self.room_repository.save_game(room_code, game)
            await self._emit_game_update(room_code)
            return True
        
        return False
    
    async def join_room(self, room_code: str, player_id: str, player_name: str, socket_id: str) -> bool:
        """Un jugador se une a una sala existente"""
        game = self.room_repository.get_game(room_code)
        if not game:
            return False
        
        success = game.add_player(player_id, player_name, socket_id)
        if success:
            self.room_repository.save_game(room_code, game)
            await self._emit_game_update(room_code)
            return True
        
        return False
    
    async def leave_room(self, room_code: str, player_id: str) -> bool:
        """Un jugador abandona la sala"""
        game = self.room_repository.get_game(room_code)
        if not game:
            return False
        
        success = game.remove_player(player_id)
        if success:
            # Si no quedan jugadores, eliminar la sala
            if not game.players:
                self.room_repository.delete_game(room_code)
                # Cancelar timer si existe
                if room_code in self.turn_timers:
                    self.turn_timers[room_code].cancel()
                    del self.turn_timers[room_code]
            else:
                self.room_repository.save_game(room_code, game)
                await self._emit_game_update(room_code)
            return True
        
        return False
    
    async def set_selected_roles(self, room_code: str, player_id: str, roles: List[str]) -> bool:
        """El host selecciona los roles para la partida"""
        game = self.room_repository.get_game(room_code)
        if not game:
            return False
        
        # Verificar que el jugador es el host
        if player_id not in game.players or not game.players[player_id].is_host:
            return False
        
        success = game.set_selected_roles(roles)
        if success:
            self.room_repository.save_game(room_code, game)
            await self._emit_game_update(room_code)
            return True
        
        return False
    
    async def start_game(self, room_code: str, player_id: str) -> bool:
        """El host inicia la partida"""
        game = self.room_repository.get_game(room_code)
        if not game:
            return False
        
        # Verificar que el jugador es el host
        if player_id not in game.players or not game.players[player_id].is_host:
            return False
        
        success = game.start_game()
        if success:
            self.room_repository.save_game(room_code, game)
            await self._emit_game_update(room_code)
            # Iniciar el primer turno nocturno
            await self._start_night_turn_timer(room_code)
            return True
        
        return False
    
    async def execute_night_action(self, room_code: str, player_id: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Un jugador ejecuta su acción nocturna"""
        game = self.room_repository.get_game(room_code)
        if not game:
            return {'success': False, 'message': 'Sala no encontrada'}
        
        result = game.execute_night_action(player_id, action_data)
        
        if result.get('success'):
            self.room_repository.save_game(room_code, game)
            # Emitir resultado solo al jugador que ejecutó la acción
            await self._emit_to_player(room_code, player_id, 'action_result', result)
        
        return result
    
    async def _start_night_turn_timer(self, room_code: str):
        """Inicia el timer para el turno nocturno actual"""
        game = self.room_repository.get_game(room_code)
        if not game or game.phase != GamePhase.NIGHT_PHASE:
            return
        
        current_player = game.get_current_turn_player()
        current_role = game.get_current_turn_role()
        
        if not current_role:
            # No hay más turnos, avanzar a día
            await self._advance_to_day_phase(room_code)
            return
        
        # Cancelar timer anterior si existe
        if room_code in self.turn_timers:
            self.turn_timers[room_code].cancel()
        
        # Emitir evento de inicio de turno
        await self._emit_turn_start(room_code, current_role)
        
        # Crear nuevo timer de 6 segundos
        self.turn_timers[room_code] = asyncio.create_task(
            self._turn_timer_countdown(room_code, 6)
        )
    
    async def _turn_timer_countdown(self, room_code: str, duration_seconds: int):
        """Timer countdown para los turnos nocturnos"""
        try:
            await asyncio.sleep(duration_seconds)
            # El timer expiró, avanzar turno
            await self._advance_night_turn(room_code)
        except asyncio.CancelledError:
            # El timer fue cancelado (probablemente porque el jugador actuó)
            pass
    
    async def _advance_night_turn(self, room_code: str):
        """Avanza al siguiente turno nocturno"""
        game = self.room_repository.get_game(room_code)
        if not game:
            return
        
        success = game.advance_night_turn()
        if success:
            self.room_repository.save_game(room_code, game)
            
            if game.phase == GamePhase.DAY_PHASE:
                # Se terminó la noche, emitir fin de fase nocturna
                await self._advance_to_day_phase(room_code)
            else:
                # Siguiente turno nocturno
                await self._start_night_turn_timer(room_code)
    
    async def _advance_to_day_phase(self, room_code: str):
        """Avanza a la fase de día"""
        # Limpiar timer
        if room_code in self.turn_timers:
            self.turn_timers[room_code].cancel()
            del self.turn_timers[room_code]
        
        # Emitir actualización del juego
        await self._emit_game_update(room_code)
    
    async def _emit_game_update(self, room_code: str):
        """Emite actualización del estado del juego a todos los jugadores"""
        game = self.room_repository.get_game(room_code)
        if not game:
            return
        
        # Emitir estado público a toda la sala
        public_state = game.get_public_state()
        await self.emit_callback('game_update', public_state, room=room_code)
        
        # Emitir estado privado a cada jugador
        for player_id, player in game.players.items():
            if player.is_connected and player.socket_id:
                private_state = game.get_private_state_for_player(player_id)
                await self.emit_callback('private_update', private_state, room=player.socket_id)
    
    async def _emit_turn_start(self, room_code: str, role: str):
        """Emite el evento de inicio de turno"""
        game = self.room_repository.get_game(room_code)
        if not game:
            return
        
        current_player = game.get_current_turn_player()
        
        # Emitir a toda la sala que comenzó el turno de un rol
        await self.emit_callback('turn_start', {
            'role': role,
            'phase': f'Fase: {role}',
            'duration': 6
        }, room=room_code)
        
        # Emitir datos específicos solo a los jugadores que necesitan actuar
        if current_player and role == 'werewolf':
            await self._emit_werewolf_turn_data(room_code)
    
    async def _emit_werewolf_turn_data(self, room_code: str):
        """Emite datos específicos para el turno de los lobos"""
        game = self.room_repository.get_game(room_code)
        if not game:
            return
        
        # Obtener todos los jugadores con rol de lobo
        werewolf_players = [
            player_id for player_id, player in game.players.items()
            if player.get_role_name() == 'werewolf'
        ]
        
        # Emitir datos de acción a cada lobo
        for player_id in werewolf_players:
            night_action_data = game.get_night_action_data_for_player(player_id)
            if night_action_data:
                await self._emit_to_player(room_code, player_id, 'night_action', night_action_data)
    
    async def _emit_to_player(self, room_code: str, player_id: str, event: str, data: Any):
        """Emite un evento a un jugador específico"""
        game = self.room_repository.get_game(room_code)
        if not game or player_id not in game.players:
            return
        
        player = game.players[player_id]
        if player.is_connected and player.socket_id:
            await self.emit_callback(event, data, room=player.socket_id)
    
    def get_game_state(self, room_code: str, player_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Obtiene el estado del juego (público o privado según el jugador)"""
        game = self.room_repository.get_game(room_code)
        if not game:
            return None
        
        if player_id and player_id in game.players:
            return game.get_private_state_for_player(player_id)
        else:
            return game.get_public_state()
    
    def room_exists(self, room_code: str) -> bool:
        """Verifica si existe una sala"""
        return self.room_repository.room_exists(room_code)
    
    def get_player_room(self, player_id: str) -> Optional[str]:
        """Encuentra la sala donde está un jugador"""
        return self.room_repository.find_player_room(player_id)