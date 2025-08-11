# backend/services/game_service.py
import time
from typing import Dict, List, Optional, Any, Callable
from domain.game_logic import GameLogic, GamePhase
from infrastructure.room_repository import RoomRepository

class GameService:
    """Servicio de aplicación que coordina la lógica del juego"""
    
    def __init__(self, room_repository: RoomRepository, emit_callback: Callable):
        self.room_repository = room_repository
        self.emit_callback = emit_callback
        self.turn_timers: Dict[str, float] = {}

    def create_room(self, room_code: str, host_id: str, host_name: str, socket_id: str) -> bool:
        """Crea una nueva sala de juego"""
        try:
            if self.room_repository.room_exists(room_code):
                return False
            
            game = GameLogic(room_code)
            success = game.add_player(host_id, host_name, socket_id, is_host=True)
            
            if success:
                self.room_repository.save_game(room_code, game)
                self._emit_game_update(room_code)
                return True
            
            return False
        except Exception as e:
            print(f"Error en create_room: {e}")
            return False

    def join_room(self, room_code: str, player_id: str, player_name: str, socket_id: str) -> bool:
        """Un jugador se une a una sala existente"""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return False
            
            success = game.add_player(player_id, player_name, socket_id)
            if success:
                self.room_repository.save_game(room_code, game)
                self._emit_game_update(room_code)
                return True
            
            return False
        except Exception as e:
            print(f"Error en join_room: {e}")
            return False

    def leave_room(self, room_code: str, player_id: str) -> bool:
        """Un jugador abandona la sala"""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return False
            
            success = game.remove_player(player_id)
            if success:
                if not game.players:
                    self.room_repository.delete_game(room_code)
                    if room_code in self.turn_timers:
                        del self.turn_timers[room_code]
                else:
                    self.room_repository.save_game(room_code, game)
                    self._emit_game_update(room_code)
                return True
            
            return False
        except Exception as e:
            print(f"Error en leave_room: {e}")
            return False

    def set_selected_roles(self, room_code: str, player_id: str, roles: List[str]) -> bool:
        """El host selecciona los roles para la partida"""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return False
            
            if player_id not in game.players or not game.players[player_id].is_host:
                return False
            
            success = game.set_selected_roles(roles)
            if success:
                self.room_repository.save_game(room_code, game)
                self._emit_game_update(room_code)
                return True
            
            return False
        except Exception as e:
            print(f"Error en set_selected_roles: {e}")
            return False

    def start_game(self, room_code: str, player_id: str) -> bool:
        """El host inicia la partida"""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return False
            
            if player_id not in game.players or not game.players[player_id].is_host:
                return False
            
            success = game.start_game()
            if success:
                self.room_repository.save_game(room_code, game)
                self._emit_game_update(room_code)
                
                # 🔧 FIX: INICIAR EL PRIMER TURNO NOCTURNO
                print(f"🔧 INICIANDO TURNOS NOCTURNOS PARA SALA: {room_code}")
                self._start_first_night_turn(room_code)
                
                return True
            
            return False
        except Exception as e:
            print(f"Error en start_game: {e}")
            return False

    def _start_first_night_turn(self, room_code: str):
        """🔧 FIX: Inicia el primer turno nocturno"""
        try:
            game = self.room_repository.get_game(room_code)
            if not game or game.phase != GamePhase.NIGHT_PHASE:
                print(f"🔧 ERROR: Game no válido o no en night_phase")
                return
            
            current_role = game.get_current_turn_role()
            current_player = game.get_current_turn_player()
            
            print(f"🔧 PRIMER TURNO: role={current_role}, player={current_player}")
            
            if not current_role:
                print(f"🔧 No hay turnos nocturnos, avanzando a día")
                self._advance_to_day_phase(room_code)
                return
            
            # Emitir evento de inicio de turno
            self._emit_turn_start(room_code, current_role)
            
            # Si es turno de werewolf, emitir datos específicos
            if current_role == 'werewolf':
                print(f"🔧 EMITIENDO DATOS DE WEREWOLF")
                self._emit_werewolf_turn_data(room_code)
            
            print(f"🔧 PRIMER TURNO INICIADO CORRECTAMENTE")
            
        except Exception as e:
            print(f"Error en _start_first_night_turn: {e}")

    def execute_night_action(self, room_code: str, player_id: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Un jugador ejecuta su acción nocturna"""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return {'success': False, 'message': 'Sala no encontrada'}
            
            result = game.execute_night_action(player_id, action_data)
            
            if result.get('success'):
                self.room_repository.save_game(room_code, game)
                self._emit_to_player(room_code, player_id, 'action_result', result)
            
            return result
        except Exception as e:
            print(f"Error en execute_night_action: {e}")
            return {'success': False, 'message': 'Error interno del servidor'}

    def _advance_to_day_phase(self, room_code: str):
        """Avanza a la fase de día"""
        try:
            if room_code in self.turn_timers:
                del self.turn_timers[room_code]
            
            self._emit_game_update(room_code)
        except Exception as e:
            print(f"Error en _advance_to_day_phase: {e}")

    def _emit_game_update(self, room_code: str):
        """Emite actualización del estado del juego a todos los jugadores"""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return
            
            public_state = game.get_public_state()
            self.emit_callback('game_update', public_state, room=room_code)
            
            # 🔧 FIX: Verificar si hay un turno activo para reenviar datos
            current_turn_role = game.get_current_turn_role()
            current_turn_player = game.get_current_turn_player()
            
            for player_id, player in game.players.items():
                if player.is_connected and player.socket_id:
                    try:
                        private_state = game.get_private_state_for_player(player_id)
                        
                        # 🔧 FIX: Si estamos en turno de werewolf y este jugador es werewolf
                        if (current_turn_role == 'werewolf' and 
                            player.get_role_name() == 'werewolf' and
                            game.phase.value == 'night_phase'):
                            
                            print(f"🔧 RECONEXIÓN DURANTE TURNO WEREWOLF: {player_id}")
                            
                            # Reenviar datos de night_action
                            night_action_data = game.get_night_action_data_for_player(player_id)
                            if night_action_data:
                                private_state['night_action'] = night_action_data
                                private_state['current_turn_role'] = 'werewolf'
                                private_state['is_your_turn'] = True
                                
                                print(f"🔧 REENVIANDO NIGHT_ACTION A {player_id}: {night_action_data}")
                                
                                # Enviar tanto private_update como night_action separado
                                self.emit_callback('private_update', private_state, room=player.socket_id)
                                self.emit_callback('night_action', night_action_data, room=player.socket_id)
                                continue
                        
                        # Emisión normal
                        self.emit_callback('private_update', private_state, room=player.socket_id)
                        
                    except Exception as player_error:
                        print(f"Error emitiendo a jugador {player_id}: {player_error}")
                        continue
                        
        except Exception as e:
            print(f"Error en _emit_game_update: {e}")

    def _emit_turn_start(self, room_code: str, role: str):
        """🔧 FIX: Emite el evento de inicio de turno"""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return
            
            # Emitir a toda la sala que comenzó el turno de un rol
            turn_data = {
                'role': role,
                'phase': f'Fase: {role}',
                'duration': 6
            }
            
            print(f"🔧 EMITIENDO TURN_START: {turn_data}")
            self.emit_callback('turn_start', turn_data, room=room_code)
            
        except Exception as e:
            print(f"Error en _emit_turn_start: {e}")

    def _emit_werewolf_turn_data(self, room_code: str):
        """🔧 FIX: Emite datos específicos para el turno de los lobos"""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return
            
            # 🔧 FIX: Obtener TODOS los jugadores con rol de lobo
            werewolf_players = []
            for player_id, player in game.players.items():
                if player.get_role_name() == 'werewolf':
                    werewolf_players.append(player_id)
            
            print(f"🔧 JUGADORES LOBO ENCONTRADOS: {werewolf_players}")
            
            # 🔧 FIX: Emitir datos de acción a CADA lobo individualmente
            for player_id in werewolf_players:
                try:
                    print(f"🔧 PROCESANDO LOBO: {player_id}")
                    
                    # Obtener datos específicos para este lobo
                    night_action_data = game.get_night_action_data_for_player(player_id)
                    
                    if night_action_data:
                        print(f"🔧 EMITIENDO NIGHT_ACTION A {player_id}: {night_action_data}")
                        self._emit_to_player(room_code, player_id, 'night_action', night_action_data)
                        
                        # 🔧 FIX ADICIONAL: También forzar actualización del estado privado
                        private_state = game.get_private_state_for_player(player_id)
                        if private_state:
                            # Asegurar que incluye los datos de night_action
                            private_state['night_action'] = night_action_data
                            private_state['current_turn_role'] = 'werewolf'
                            private_state['is_your_turn'] = True
                            
                            print(f"🔧 EMITIENDO PRIVATE_UPDATE A {player_id}")
                            self._emit_to_player(room_code, player_id, 'private_update', private_state)
                    else:
                        print(f"🔧 NO HAY NIGHT_ACTION_DATA para {player_id}")
                        
                except Exception as player_error:
                    print(f"❌ Error emitiendo acción nocturna a {player_id}: {player_error}")
                    continue
                    
        except Exception as e:
            print(f"❌ Error en _emit_werewolf_turn_data: {e}")

    def _emit_to_player(self, room_code: str, player_id: str, event: str, data: Any):
        """🔧 FIX: Emite un evento a un jugador específico"""
        try:
            game = self.room_repository.get_game(room_code)
            if not game or player_id not in game.players:
                return
            
            player = game.players[player_id]
            if player.is_connected and player.socket_id:
                print(f"🔧 EMITIENDO {event} A JUGADOR {player_id} (socket: {player.socket_id})")
                self.emit_callback(event, data, room=player.socket_id)
        except Exception as e:
            print(f"Error en _emit_to_player para {player_id}: {e}")

    def get_game_state(self, room_code: str, player_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Obtiene el estado del juego"""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return None
            
            if player_id and player_id in game.players:
                return game.get_private_state_for_player(player_id)
            else:
                return game.get_public_state()
        except Exception as e:
            print(f"Error en get_game_state: {e}")
            return None

    def room_exists(self, room_code: str) -> bool:
        """Verifica si existe una sala"""
        try:
            return self.room_repository.room_exists(room_code)
        except Exception as e:
            print(f"Error en room_exists: {e}")
            return False

    def get_player_room(self, player_id: str) -> Optional[str]:
        """Encuentra la sala donde está un jugador"""
        try:
            return self.room_repository.find_player_room(player_id)
        except Exception as e:
            print(f"Error en get_player_room: {e}")
            return None