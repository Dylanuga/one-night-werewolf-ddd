# backend/services/game_service.py
import time
from typing import Dict, List, Optional, Any, Callable
from domain.game_logic import GameLogic, GamePhase
from infrastructure.room_repository import RoomRepository

class GameService:
    """Servicio de aplicación que coordina la lógica del juego"""
    
    def __init__(
        self,
        room_repository: RoomRepository,
        emit_callback: Callable,
        start_background_task: Callable,
        sleep_fn: Callable
    ):
        self.room_repository = room_repository
        self.emit_callback = emit_callback
        self.start_background_task = start_background_task
        self.sleep_fn = sleep_fn
        self.turn_timer_tokens: Dict[str, int] = {}
        self.TURN_DURATION = 6  # segundos

    def create_room(self, room_code: str, host_id: str, host_name: str, socket_id: str) -> bool:
        """Crea una nueva sala de juego"""
        try:
            print(f"🏠 CREATE_ROOM INICIADO: {room_code}, host: {host_name} ({host_id})")
            
            if self.room_repository.room_exists(room_code):
                print(f"❌ CREATE_ROOM FALLÓ: Sala {room_code} ya existe")
                return False
            
            game = GameLogic(room_code)
            success = game.add_player(host_id, host_name, socket_id, is_host=True)
            
            if success:
                print(f"✅ Jugador host {host_name} añadido exitosamente")
                self.room_repository.save_game(room_code, game)
                print(f"✅ Sala {room_code} guardada en repository")
                
                print(f"📤 Enviando game_update para sala {room_code}")
                self._emit_game_update(room_code)
                print(f"✅ CREATE_ROOM COMPLETADO: {room_code}")
                return True
            else:
                print(f"❌ CREATE_ROOM FALLÓ: No se pudo añadir jugador host")
                return False
            
        except Exception as e:
            print(f"❌ ERROR en create_room: {e}")
            import traceback
            traceback.print_exc()
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
            print(f"🔧 _start_first_night_turn INICIADO para sala {room_code}")
            
            game = self.room_repository.get_game(room_code)
            if not game or game.phase != GamePhase.NIGHT_PHASE:
                print(f"🔧 ERROR: Game no válido o no en night_phase")
                return
            
            current_role = game.get_current_turn_role()
            # 🔧 FIX: No usar get_current_turn_player() que no existe
            
            print(f"🔧 PRIMER TURNO: role={current_role}")
            
            if not current_role:
                print(f"🔧 No hay turnos nocturnos, avanzando a día")
                self._advance_to_day_phase(room_code)
                return
            
            # ✅ ARQUITECTURA UNIFICADA: _emit_turn_start maneja todo
            print(f"🔧 Emitiendo turn_start para rol: {current_role}")
            self._emit_turn_start(room_code, current_role)
            
            # 🔧 FIX: Iniciar timer automático para este turno
            print(f"🔧 Iniciando timer para el turno")
            self._start_turn_timer(room_code)
            
            # ❌ REMOVIDO: Ya no necesitamos emit específicos porque están unificados en _emit_turn_start
            # Los datos de werewolf/mason se manejan dentro de _emit_turn_start
            
            print(f"🔧 PRIMER TURNO INICIADO CORRECTAMENTE para rol: {current_role}")
            
        except Exception as e:
            print(f"❌ Error en _start_first_night_turn: {e}")
            import traceback
            traceback.print_exc()

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
            print(f"📤 _emit_game_update INICIADO para sala {room_code}")
            
            game = self.room_repository.get_game(room_code)
            if not game:
                print(f"❌ _emit_game_update: No se encontró juego para {room_code}")
                return
            
            public_state = game.get_public_state()
            print(f"📊 Enviando game_update a toda la sala {room_code}")
            print(f"   Estado público: {len(public_state.get('players', []))} jugadores, fase: {public_state.get('phase')}")
            self.emit_callback('game_update', public_state, room=room_code)
            
            # 🔧 FIX: Verificar si hay un turno activo para reenviar datos
            current_turn_role = game.get_current_turn_role()
            # No necesitamos current_turn_player, solo current_turn_role
            
            print(f"👥 Enviando private_update a {len(game.players)} jugadores individuales")
            for player_id, player in game.players.items():
                if player.is_connected and player.socket_id:
                    try:
                        print(f"   📤 Enviando private_update a {player.name} ({player_id})")
                        private_state = game.get_private_state_for_player(player_id)
                        print(f"      Estado privado: fase={private_state.get('phase')}, rol={private_state.get('your_role', 'sin_rol')}")
                        
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

                        # 🔧 FIX: Si estamos en turno de seer y este jugador es seer
                        if (current_turn_role == 'seer' and 
                            player.get_role_name() == 'seer' and
                            game.phase.value == 'night_phase'):
                            
                            print(f"🔧 RECONEXIÓN DURANTE TURNO SEER: {player_id}")
                            
                            # Reenviar datos de night_action
                            night_action_data = game.get_night_action_data_for_player(player_id)
                            if night_action_data:
                                private_state['night_action'] = night_action_data
                                private_state['current_turn_role'] = 'seer'
                                private_state['is_your_turn'] = True
                                
                                print(f"🔧 REENVIANDO NIGHT_ACTION A SEER {player_id}: {night_action_data}")
                                
                                # Enviar tanto private_update como night_action separado
                                self.emit_callback('private_update', private_state, room=player.socket_id)
                                self.emit_callback('night_action', night_action_data, room=player.socket_id)
                                continue
                        
                        # Emisión normal
                        self.emit_callback('private_update', private_state, room=player.socket_id)
                        print(f"      ✅ private_update enviado a {player.name}")
                        
                    except Exception as player_error:
                        print(f"❌ Error emitiendo a jugador {player_id}: {player_error}")
                        import traceback
                        traceback.print_exc()
                        continue
                        
            print(f"✅ _emit_game_update COMPLETADO para sala {room_code}")
        except Exception as e:
            print(f"❌ Error en _emit_game_update: {e}")
            import traceback
            traceback.print_exc()

    def _emit_turn_start(self, room_code: str, role: str):
        """🔧 FIX ARQUITECTURAL: Emite el evento de inicio de turno Y actualiza estados privados de manera unificada"""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                print(f"❌ No se encontró juego para emitir turn_start: {room_code}")
                return
            
            # Crear timestamp único para este turno
            turn_timestamp = time.time()
            
            # Emitir a toda la sala que comenzó el turno de un rol
            turn_data = {
                'role': role,
                'phase': f'Fase: {role}',
                'duration': self.TURN_DURATION,
                'timestamp': turn_timestamp
            }
            
            print(f"🔧 EMITIENDO TURN_START UNIFICADO: {turn_data}")
            
            # 1. Emitir turn_start a toda la sala (para UI)
            self.emit_callback('turn_start', turn_data, room=room_code)
            
            # 2. CRÍTICO: Actualizar inmediatamente los estados privados de todos los jugadores
            # Esto elimina el race condition entre turn_start y private_update
            for player_id, player in game.players.items():
                if player.is_connected and player.socket_id:
                    try:
                        # Obtener estado privado actualizado con el nuevo turno
                        private_state = game.get_private_state_for_player(player_id)
                        
                        # CRÍTICO: Añadir el timestamp del turno para detectar cambios
                        private_state['turn_timestamp'] = turn_timestamp
                        private_state['current_turn_role'] = role
                        
                        # Determinar si es el turno de este jugador
                        player_role = player.get_role_name()
                        private_state['is_your_turn'] = (player_role == role)
                        
                        # Si es su turno, añadir datos de night_action
                        if private_state['is_your_turn']:
                            night_action_data = game.get_night_action_data_for_player(player_id)
                            if night_action_data:
                                private_state['night_action'] = night_action_data
                        
                        print(f"� EMITIENDO PRIVATE_UPDATE UNIFICADO a {player_id} ({player_role}): is_your_turn={private_state['is_your_turn']}")
                        
                        # Emitir private_update con datos completos y timestamp
                        self.emit_callback('private_update', private_state, room=player.socket_id)
                        
                    except Exception as player_error:
                        print(f"⚠️ Error emitiendo private_update unificado a {player_id}: {str(player_error)}")
                        continue
            
            print(f"✅ TURN_START UNIFICADO COMPLETADO para rol: {role}")
            
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
        """🔧 FIX MEJORADO: Inicia un timer compatible con eventlet para avanzar turno cada 6 segundos"""
        try:
            # Verificar si el juego sigue activo y en fase nocturna
            game = self.room_repository.get_game(room_code)
            if not game or game.phase != GamePhase.NIGHT_PHASE:
                print(f"⚠️ No se inicia timer: Sala {room_code} no válida o no en night_phase")
                return
            
            # Verificar si hay un rol actual válido
            current_role = game.get_current_turn_role()
            if not current_role:
                print(f"⚠️ No se inicia timer: No hay rol actual en sala {room_code}")
                return
                
            # Invalidar cualquier timer anterior y generar un token nuevo
            token = self.turn_timer_tokens.get(room_code, 0) + 1
            self.turn_timer_tokens[room_code] = token
            
            def timer_task(expected_token: int):
                try:
                    # Sleep no bloqueante compatible con eventlet/Socket.IO
                    self.sleep_fn(self.TURN_DURATION)
                    
                    # Si hubo un cancel o un nuevo timer, abortar
                    if self.turn_timer_tokens.get(room_code) != expected_token:
                        print(f"⚠️ Timer invalidado para sala {room_code}, token {expected_token}")
                        return
                    
                    self._auto_advance_turn(room_code)
                except Exception as e:
                    print(f"🔴 ERROR en timer_task para {room_code}: {str(e)}")
            
            # Iniciar tarea en background
            self.start_background_task(timer_task, token)
            
            print(f"🔧 TIMER INICIADO: {self.TURN_DURATION}s para sala {room_code}, rol {current_role}")
            
            # Registrar un log con el momento exacto del inicio del timer
            start_time = time.strftime("%H:%M:%S", time.localtime())
            expected_end = time.strftime("%H:%M:%S", 
                                         time.localtime(time.time() + self.TURN_DURATION))
            print(f"⏱️ Timer iniciado a las {start_time}, terminará a las {expected_end}")
            
        except Exception as e:
            print(f"🔴 ERROR iniciando timer para {room_code}: {str(e)}")
            import traceback
            traceback.print_exc()

    def _cancel_turn_timer(self, room_code: str):
        """🔧 FIX: Cancela el timer de turno para una sala (invalida token)"""
        try:
            if room_code in self.turn_timer_tokens:
                # Invalidar el token actual
                del self.turn_timer_tokens[room_code]
                print(f"🔧 TIMER CANCELADO (token invalidado) para sala {room_code}")
        except Exception as e:
            print(f"🔴 ERROR cancelando timer para {room_code}: {str(e)}")
            # Intentar limpiar el token incluso si falla la cancelación
            if room_code in self.turn_timer_tokens:
                del self.turn_timer_tokens[room_code]

    def _auto_advance_turn(self, room_code: str):
        """🔧 FIX MEJORADO: Avanza automáticamente al siguiente turno cuando expira el timer"""
        try:
            print(f"🔧 AUTO-AVANZANDO TURNO para sala {room_code}")
            
            game = self.room_repository.get_game(room_code)
            if not game:
                print(f"❌ Sala {room_code} no encontrada")
                return
                
            if game.phase != GamePhase.NIGHT_PHASE:
                print(f"⚠️ Sala {room_code} no está en fase nocturna: {game.phase}")
                return
            
            # Registrar el turno actual antes de avanzar (para debugging)
            current_role_before = game.get_current_turn_role()
            print(f"🔄 Avanzando desde rol: {current_role_before}, turno {game.current_turn_index}/{len(game.night_turns)}")
            
            # Avanzar al siguiente turno
            advanced = game.advance_night_turn()
            
            # Guardar el estado actualizado del juego incluso si no avanzó
            # (podría haber cambios de estado internos)
            self.room_repository.save_game(room_code, game)
            
            if not advanced:
                print(f"⚠️ No se pudo avanzar el turno en sala {room_code}")
                return
                
            print(f"✅ Turno avanzado correctamente: {game.current_turn_index}/{len(game.night_turns)}")
            
            # Verificar si la noche terminó
            if game.phase == GamePhase.DAY_PHASE:
                print(f"🌞 NOCHE TERMINADA - AVANZANDO A FASE DE DÍA")
                
                # ✅ ARQUITECTURA UNIFICADA: Solo usar _emit_game_update que ya incluye private_update para todos
                print(f"📤 Enviando actualizaciones unificadas tras finalizar noche")
                self._emit_game_update(room_code)
                    
                # Pequeña pausa para asegurar que los clientes reciban las actualizaciones
                time.sleep(0.1)
                
                # Avanzar a la fase de día
                print(f"🌞 Avanzando a fase de día")
                self._advance_to_day_phase(room_code)
            else:
                # Continuar con el siguiente turno
                current_role = game.get_current_turn_role()
                print(f"� CONTINUANDO CON SIGUIENTE TURNO: {current_role}")
                
                if not current_role:
                    print(f"⚠️ ERROR: Rol actual es None después de avanzar turno")
                    return
                
                # ✅ ARQUITECTURA UNIFICADA: _emit_turn_start ahora maneja TODO
                # (turn_start + private_update + night_action data)
                self._emit_turn_start(room_code, current_role)
                
                # ❌ REMOVIDO: Ya no necesitamos emit separados porque están unificados
                # self._emit_game_update(room_code)  # Redundante
                # self._emit_werewolf_turn_data()    # Redundante, ya incluido en _emit_turn_start
                # self._emit_mason_turn_data()       # Redundante, ya incluido en _emit_turn_start
                
                # Iniciar timer para el siguiente turno (después de todo lo demás)
                self._start_turn_timer(room_code)
                
        except Exception as e:
            print(f"🔴 ERROR EN AUTO-AVANCE: {str(e)}")
            import traceback
            traceback.print_exc()

    def advance_turn(self, room_code: str):
        """Avanza manualmente al siguiente turno (método público)"""
        try:
            print(f"🔧 AVANCE MANUAL DE TURNO para sala {room_code}")
            
            # Cancelar cualquier timer existente
            self._cancel_turn_timer(room_code)
            
            # Utilizar directamente el método _auto_advance_turn que ya tiene toda la lógica necesaria
            self._auto_advance_turn(room_code)
            
            return True
        except Exception as e:
            print(f"🔴 ERROR EN AVANCE MANUAL: {str(e)}")
            return False

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

    def get_private_state(self, room_code: str, player_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el estado privado de un jugador específico"""
        try:
            game = self.room_repository.get_game(room_code)
            if not game or player_id not in game.players:
                return None
            
            # Obtener el estado privado base
            private_state = game.get_private_state_for_player(player_id)
            
            # Si el juego está en fase nocturna, añadir información del turno actual
            if game.phase == GamePhase.NIGHT_PHASE:
                current_turn_role = game.get_current_turn_role()
                if current_turn_role:
                    private_state['current_turn_role'] = current_turn_role
                    
                    # Verificar si es el turno del jugador
                    player_role = game.players[player_id].get_role_name()
                    private_state['is_your_turn'] = (player_role == current_turn_role)
                    
                    # Si es su turno, incluir night_action data si está disponible
                    if private_state['is_your_turn']:
                        night_action_data = game.get_night_action_for_role(current_turn_role, player_id)
                        if night_action_data:
                            private_state['night_action'] = night_action_data
            
            return private_state
            
        except Exception as e:
            print(f"Error en get_private_state: {e}")
            return None
