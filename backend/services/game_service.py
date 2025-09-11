# backend/services/game_service.py
import time
import threading
from typing import Dict, List, Optional, Any, Callable
from domain.game_logic import GameLogic, GamePhase
from infrastructure.room_repository import RoomRepository

class GameService:
    """Servicio de aplicación que coordina la lógica del juego"""
    
    def __init__(self, room_repository: RoomRepository, emit_callback: Callable):
        self.room_repository = room_repository
        self.emit_callback = emit_callback
        self.turn_timers: Dict[str, threading.Timer] = {}
        self.TURN_DURATION = 6  # segundos

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
                    self._cancel_turn_timer(room_code)
                else:
                    self.room_repository.save_game(room_code, game)
                    self._emit_game_update(room_code)
                return True
            
            return False
        except Exception as e:
            print(f"Error en leave_room: {e}")
            return False

    def set_selected_roles(self, room_code: str, player_id: str, roles: List[str]) -> bool:
        """El host selecciona los roles para la partida - VALIDACIÓN RELAJADA"""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                print(f"🔧 ERROR: Sala {room_code} no encontrada")
                return False
            
            # Verificar que el jugador es el host
            if player_id not in game.players or not game.players[player_id].is_host:
                print(f"🔧 ERROR: {player_id} no es host o no existe")
                return False
            
            print(f"🔧 SINCRONIZANDO ROLES (sin validación estricta):")
            print(f"   Roles recibidos: {len(roles)} -> {roles}")
            
            # ✅ VALIDACIÓN MÍNIMA: Solo verificar que no esté vacío y sean roles válidos
            if not roles:
                print(f"⏭️ SKIP: Lista de roles vacía, no actualizando")
                return True  # No es error, simplemente no hay nada que hacer
            
            # Validación básica: roles válidos
            valid_roles = {'werewolf', 'villager', 'seer', 'robber', 'troublemaker', 
                          'hunter', 'mason', 'drunk', 'insomniac', 'tanner'}
            invalid_roles = [role for role in roles if role not in valid_roles]
            if invalid_roles:
                print(f"❌ ERROR: Roles inválidos: {invalid_roles}")
                return False
            
            print(f"✅ ROLES VÁLIDOS - SINCRONIZANDO...")
            
            # Aplicar los roles al juego SIN validación estricta
            success = game.set_selected_roles(roles)
            if success:
                self.room_repository.save_game(room_code, game)
                self._emit_game_update(room_code)
                print(f"✅ ROLES SINCRONIZADOS EN {room_code}")
                return True
            else:
                print(f"❌ ERROR: game.set_selected_roles falló")
                return False
            
        except Exception as e:
            print(f"❌ ERROR en set_selected_roles: {e}")
            return False

    def start_game(self, room_code: str, player_id: str) -> bool:
        """El host inicia la partida - AQUÍ SÍ VALIDACIÓN ESTRICTA"""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                print(f"❌ ERROR: Sala {room_code} no encontrada")
                return False
            
            if player_id not in game.players or not game.players[player_id].is_host:
                print(f"❌ ERROR: {player_id} no es host o no existe")
                return False
            
            # 🎯 VALIDACIÓN ESTRICTA ANTES DE INICIAR
            player_count = len(game.players)
            required_roles = player_count + 3
            current_roles = game.selected_roles or []
            
            print(f"🔧 VALIDACIÓN ESTRICTA PARA INICIAR JUEGO:")
            print(f"   Jugadores: {player_count}")
            print(f"   Roles requeridos: {required_roles}")
            print(f"   Roles actuales: {len(current_roles)} -> {current_roles}")
            
            # Validación 1: Número correcto de roles
            if len(current_roles) != required_roles:
                print(f"❌ ERROR: Se necesitan {required_roles} roles, tienes {len(current_roles)}")
                return False
            
            # Validación 2: Al menos 1 lobo
            werewolf_count = current_roles.count('werewolf')
            if werewolf_count < 1:
                print(f"❌ ERROR: Se necesita al menos 1 lobo, tienes {werewolf_count}")
                return False
            
            # Validación 3: No más de la mitad de lobos
            max_werewolves = max(1, player_count // 2)
            if werewolf_count > max_werewolves:
                print(f"❌ ERROR: Demasiados lobos ({werewolf_count}), máximo permitido: {max_werewolves}")
                return False
            
            print(f"✅ VALIDACIÓN EXITOSA - INICIANDO JUEGO:")
            print(f"   Lobos: {werewolf_count} (válido: 1-{max_werewolves})")
            print(f"   Total: {len(current_roles)} roles")
            
            # Ahora sí, iniciar el juego
            success = game.start_game()
            if success:
                self.room_repository.save_game(room_code, game)
                self._emit_game_update(room_code)
                
                print(f"🔧 INICIANDO TURNOS NOCTURNOS PARA SALA: {room_code}")
                self._start_first_night_turn(room_code)
                
                return True
            else:
                print(f"❌ ERROR: game.start_game() falló")
                return False
            
        except Exception as e:
            print(f"❌ ERROR en start_game: {e}")
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
            
            # 🔧 FIX: Iniciar timer automático para este turno
            self._start_turn_timer(room_code)
            
            # Si es turno de werewolf, emitir datos específicos
            if current_role == 'werewolf':
                print(f"🔧 EMITIENDO DATOS DE WEREWOLF")
                self._emit_werewolf_turn_data(room_code)
            elif current_role == 'mason':
                print(f"🔧 EMITIENDO DATOS DE MASON")
                self._emit_mason_turn_data(room_code)
            
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
            self._cancel_turn_timer(room_code)
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
                        
                        # 🔧 FIX: Si estamos en turno de mason y este jugador es mason
                        if (current_turn_role == 'mason' and 
                            player.get_role_name() == 'mason' and
                            game.phase.value == 'night_phase'):
                            
                            print(f"🔧 RECONEXIÓN DURANTE TURNO MASON: {player_id}")
                            
                            # Reenviar datos de night_action
                            night_action_data = game.get_night_action_data_for_player(player_id)
                            if night_action_data:
                                private_state['night_action'] = night_action_data
                                private_state['current_turn_role'] = 'mason'
                                private_state['is_your_turn'] = True
                                
                                print(f"🔧 REENVIANDO NIGHT_ACTION A MASÓN {player_id}: {night_action_data}")
                                
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
                'duration': self.TURN_DURATION
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

    def enable_test_mode(self, room_code: str, role_distribution: Dict[str, List[str]]) -> bool:
        """Activa el modo de prueba para una sala específica"""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return False
            
            game.enable_test_mode(role_distribution)
            self.room_repository.save_game(room_code, game)
            return True
        except Exception as e:
            print(f"Error en enable_test_mode: {e}")
            return False

    def disable_test_mode(self, room_code: str) -> bool:
        """Desactiva el modo de prueba para una sala específica"""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return False
            
            game.disable_test_mode()
            self.room_repository.save_game(room_code, game)
            return True
        except Exception as e:
            print(f"Error en disable_test_mode: {e}")
            return False

    def _start_turn_timer(self, room_code: str):
        """🔧 FIX: Inicia un timer que avanza automáticamente el turno después de 6 segundos"""
        try:
            # Cancelar timer anterior si existe
            self._cancel_turn_timer(room_code)
            
            # Crear nuevo timer
            timer = threading.Timer(self.TURN_DURATION, self._auto_advance_turn, [room_code])
            timer.start()
            self.turn_timers[room_code] = timer
            
            print(f"🔧 TIMER INICIADO: {self.TURN_DURATION}s para sala {room_code}")
            
        except Exception as e:
            print(f"Error iniciando timer para {room_code}: {e}")

    def _cancel_turn_timer(self, room_code: str):
        """🔧 FIX: Cancela el timer de turno para una sala"""
        try:
            if room_code in self.turn_timers:
                timer = self.turn_timers[room_code]
                timer.cancel()
                del self.turn_timers[room_code]
                print(f"🔧 TIMER CANCELADO para sala {room_code}")
        except Exception as e:
            print(f"Error cancelando timer para {room_code}: {e}")

    def _auto_advance_turn(self, room_code: str):
        """🔧 FIX: Avanza automáticamente al siguiente turno cuando expira el timer"""
        try:
            print(f"🔧 AUTO-AVANZANDO TURNO para sala {room_code}")
            
            game = self.room_repository.get_game(room_code)
            if not game or game.phase != GamePhase.NIGHT_PHASE:
                print(f"🔧 Sala {room_code} no válida o no en night_phase")
                return
            
            # Avanzar al siguiente turno
            advanced = game.advance_night_turn()
            if advanced:
                self.room_repository.save_game(room_code, game)
                
                # Verificar si la noche terminó
                if game.phase == GamePhase.DAY_PHASE:
                    print(f"🔧 NOCHE TERMINADA - AVANZANDO A FASE DE DÍA")
                    self._advance_to_day_phase(room_code)
                else:
                    # Continuar con el siguiente turno
                    print(f"🔧 CONTINUANDO CON SIGUIENTE TURNO")
                    self._emit_game_update(room_code)
                    
                    # Enviar datos del nuevo turno
                    current_role = game.get_current_turn_role()
                    if current_role:
                        self._emit_turn_start(room_code, current_role)
                        self._start_turn_timer(room_code)  # Iniciar timer para el siguiente turno
                        
                        # Enviar datos específicos del rol
                        if current_role == 'werewolf':
                            self._emit_werewolf_turn_data(room_code)
                        elif current_role == 'mason':
                            self._emit_mason_turn_data(room_code)
                        
        except Exception as e:
            print(f"Error en auto_advance_turn para {room_code}: {e}")

    def _emit_mason_turn_data(self, room_code: str):
        """🔧 FIX: Emite datos específicos para el turno de los masones"""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return
            
            # 🔧 FIX: Obtener TODOS los jugadores con rol de masón
            mason_players = []
            for player_id, player in game.players.items():
                if player.get_role_name() == 'mason':
                    mason_players.append(player_id)
            
            print(f"🔧 JUGADORES MASÓN ENCONTRADOS: {mason_players}")
            
            # 🔧 FIX: Emitir datos de acción a CADA masón individualmente
            for player_id in mason_players:
                try:
                    print(f"🔧 PROCESANDO MASÓN: {player_id}")
                    
                    # Obtener datos específicos para este masón
                    night_action_data = game.get_night_action_data_for_player(player_id)
                    
                    if night_action_data:
                        print(f"🔧 EMITIENDO NIGHT_ACTION A MASÓN {player_id}: {night_action_data}")
                        self._emit_to_player(room_code, player_id, 'night_action', night_action_data)
                        
                        # 🔧 FIX ADICIONAL: También forzar actualización del estado privado
                        private_state = game.get_private_state_for_player(player_id)
                        if private_state:
                            # Asegurar que incluye los datos de night_action
                            private_state['night_action'] = night_action_data
                            private_state['current_turn_role'] = 'mason'
                            private_state['is_your_turn'] = True
                            
                            print(f"🔧 EMITIENDO PRIVATE_UPDATE A MASÓN {player_id}")
                            self._emit_to_player(room_code, player_id, 'private_update', private_state)
                    else:
                        print(f"🔧 NO HAY NIGHT_ACTION_DATA para masón {player_id}")
                        
                except Exception as player_error:
                    print(f"❌ Error emitiendo acción nocturna a masón {player_id}: {player_error}")
                    continue
                    
        except Exception as e:
            print(f"❌ Error en _emit_mason_turn_data: {e}")