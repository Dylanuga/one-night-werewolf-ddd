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
        self.discussion_timer_tokens: Dict[str, int] = {}
        self.voting_timer_tokens: Dict[str, int] = {}
        self.TURN_DURATION = 12  # segundos (default)
        self.turn_duration_by_room: Dict[str, int] = {}

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
                print(f"[ROOM] creada {room_code} host={host_name} ({host_id})")
                return True
            else:
                return False
            
        except Exception as e:
            print(f"❌ ERROR en create_room: {e}")
            import traceback
            traceback.print_exc()
            return False

    def set_turn_duration(self, room_code: str, duration_seconds: int) -> bool:
        """Ajusta la duracion del turno para una sala especifica (solo testing)"""
        try:
            if not isinstance(duration_seconds, int) or duration_seconds < 1:
                return False
            self.turn_timer_tokens[room_code] = self.turn_timer_tokens.get(room_code, 0)
            self.turn_duration_by_room[room_code] = duration_seconds
            print(f"🕒 TURN_DURATION actualizado a {duration_seconds}s para sala {room_code}")
            return True
        except Exception as e:
            print(f"Error en set_turn_duration: {e}")
            return False

    def _get_turn_duration(self, room_code: str) -> int:
        return self.turn_duration_by_room.get(room_code, self.TURN_DURATION)

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
                print(f"[ROOM] join {room_code} player={player_name} ({player_id})")
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
            
            # Validación 1: Número correcto de roles
            if len(current_roles) != required_roles:
                return False
            
            # Validación 2: Al menos 1 lobo
            werewolf_count = current_roles.count('werewolf')
            if werewolf_count < 1:
                return False
            
            # Validación 3: No más de la mitad de lobos
            max_werewolves = max(1, player_count // 2)
            if werewolf_count > max_werewolves:
                return False
            
            # Ahora sí, iniciar el juego
            success = game.start_game()
            if success:
                self.room_repository.save_game(room_code, game)
                self._emit_game_update(room_code)
                
                print(f"[GAME] iniciado sala {room_code} por {player_id}")
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
                self._start_open_eyes_phase(room_code)
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

    def set_discussion_timer(self, room_code: str, host_id: str, duration: int) -> bool:
        """Configura la duración del debate en segundos (120, 300 o 600)"""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return False
            if host_id not in game.players or not game.players[host_id].is_host:
                return False
            success = game.set_discussion_duration(duration)
            if success:
                self.room_repository.save_game(room_code, game)
                self._emit_game_update(room_code)
                print(f"⏱️ Duración de discusión actualizada a {duration}s en sala {room_code}")
            return success
        except Exception as e:
            print(f"Error en set_discussion_timer: {e}")
            return False

    def _advance_to_day_phase(self, room_code: str):
        """Avanza a la fase de día e inicia el temporizador de debate"""
        try:
            self._cancel_turn_timer(room_code)
            game = self.room_repository.get_game(room_code)
            if not game:
                return

            import time
            game.phase = GamePhase.DAY_PHASE
            game.discussion_end_timestamp = time.time() + game.discussion_duration
            self.room_repository.save_game(room_code, game)
            self._emit_game_update(room_code)
            print(f"[PHASE] día en sala {room_code}, duración={game.discussion_duration}s")
            
            # Iniciar temporizador de discusión en background
            self._start_discussion_timer(room_code)
        except Exception as e:
            print(f"Error en _advance_to_day_phase: {e}")

    def _start_discussion_timer(self, room_code: str):
        """Inicia el temporizador de debate en segundo plano"""
        try:
            game = self.room_repository.get_game(room_code)
            if not game or game.phase != GamePhase.DAY_PHASE:
                return

            token = self.discussion_timer_tokens.get(room_code, 0) + 1
            self.discussion_timer_tokens[room_code] = token
            duration = game.discussion_duration

            def discussion_task(expected_token: int, wait_seconds: int):
                try:
                    self.sleep_fn(wait_seconds)
                    if self.discussion_timer_tokens.get(room_code) != expected_token:
                        return

                    print(f"⏰ [TIMER] Debate terminado en sala {room_code}. Iniciando votación automáticamente.")
                    self.start_voting_phase(room_code, host_id=None, auto=True)
                except Exception as e:
                    print(f"Error en discussion_task: {e}")

            self.start_background_task(discussion_task, token, duration)
        except Exception as e:
            print(f"Error en _start_discussion_timer: {e}")

    def _cancel_discussion_timer(self, room_code: str):
        """Cancela el temporizador de debate"""
        try:
            if room_code in self.discussion_timer_tokens:
                del self.discussion_timer_tokens[room_code]
        except Exception as e:
            print(f"Error en _cancel_discussion_timer: {e}")

    def _start_open_eyes_phase(self, room_code: str):
        """Muestra mensaje de transición antes del día."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return

            # Emitir mensaje "Abrid los ojos todos" por 6 segundos
            self._emit_turn_start(room_code, 'open_eyes', duration_override=6)

            def finish_transition():
                try:
                    game = self.room_repository.get_game(room_code)
                    if not game:
                        return
                    game.phase = GamePhase.DAY_PHASE
                    game.night_finished = False
                    self.room_repository.save_game(room_code, game)
                    self._advance_to_day_phase(room_code)
                except Exception as e:
                    print(f"Error en finish_transition: {e}")

            def transition_task():
                self.sleep_fn(6)
                finish_transition()
            self.start_background_task(transition_task)
        except Exception as e:
            print(f"Error en _start_open_eyes_phase: {e}")

    def start_voting_phase(self, room_code: str, host_id: Optional[str] = None, auto: bool = False) -> bool:
        """El host finaliza discusión o el temporizador expira e inicia votación."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return False
            if not auto:
                if not host_id or host_id not in game.players or not game.players[host_id].is_host:
                    return False

            self._cancel_discussion_timer(room_code)
            if not game.start_voting_phase():
                return False

            self.room_repository.save_game(room_code, game)
            self._emit_game_update(room_code)
            self.emit_callback('voting_started', {'room_code': room_code}, room=room_code)
            
            # Iniciar temporizador de votación (60 segundos)
            self._start_voting_timer(room_code)
            return True
        except Exception as e:
            print(f"Error en start_voting_phase: {e}")
            return False

    def _start_voting_timer(self, room_code: str):
        """Inicia el temporizador de votación (60s) en segundo plano"""
        try:
            game = self.room_repository.get_game(room_code)
            if not game or game.phase != GamePhase.VOTING:
                return

            token = self.voting_timer_tokens.get(room_code, 0) + 1
            self.voting_timer_tokens[room_code] = token
            duration = game.voting_duration

            def voting_task(expected_token: int, wait_seconds: int):
                try:
                    self.sleep_fn(wait_seconds)
                    if self.voting_timer_tokens.get(room_code) != expected_token:
                        return

                    print(f"⏰ [TIMER] Tiempo de votación terminado en sala {room_code}. Finalizando con votos emitidos.")
                    self.end_voting_phase(room_code, host_id=None, force=True)
                except Exception as e:
                    print(f"Error en voting_task: {e}")

            self.start_background_task(voting_task, token, duration)
        except Exception as e:
            print(f"Error en _start_voting_timer: {e}")

    def _cancel_voting_timer(self, room_code: str):
        """Cancela el temporizador de votación"""
        try:
            if room_code in self.voting_timer_tokens:
                del self.voting_timer_tokens[room_code]
        except Exception as e:
            print(f"Error en _cancel_voting_timer: {e}")

    def submit_vote(self, room_code: str, player_id: str, target_id: str) -> Dict[str, Any]:
        """Registra un voto y finaliza partida si todos votaron."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return {'success': False, 'message': 'Sala no encontrada'}

            result = game.submit_vote(player_id, target_id)
            if result.get('success'):
                self.room_repository.save_game(room_code, game)
                self._emit_game_update(room_code)

                # Si todos los jugadores conectados han votado, auto-finalizar tras breve pausa
                if result.get('all_connected_voted') or result.get('all_voted'):
                    def auto_finalize():
                        self.sleep_fn(1)
                        self.end_voting_phase(room_code, host_id=None, force=True)
                    self.start_background_task(auto_finalize)

            return result
        except Exception as e:
            print(f"Error en submit_vote: {e}")
            return {'success': False, 'message': 'Error interno del servidor'}

    def end_voting_phase(self, room_code: str, host_id: Optional[str] = None, force: bool = False) -> bool:
        """El host (o temporizador) finaliza votación y revela resultados."""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return False
            if game.phase == GamePhase.GAME_END:
                return True
            if not force:
                if not host_id or host_id not in game.players or not game.players[host_id].is_host:
                    return False
                if not game.can_finalize(allow_partial=True):
                    return False

            self._cancel_voting_timer(room_code)
            # Finalizar y revelar
            game._finalize_game()
            self.room_repository.save_game(room_code, game)
            self._emit_game_update(room_code)
            reveal_data = game.get_reveal_data()
            self.emit_callback('reveal', reveal_data, room=room_code)
            self.emit_callback('game_end', reveal_data, room=room_code)
            return True
        except Exception as e:
            print(f"Error en end_voting_phase: {e}")
            return False

    def reset_game(self, room_code: str, player_id: str, to_phase: str) -> bool:
        """El host reinicia la partida a LOBBY o ROLE_SELECTION"""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return False
            
            # Verificar que es el host
            if player_id not in game.players or not game.players[player_id].is_host:
                return False
                
            success = game.reset_game(to_phase)
            if success:
                self.room_repository.save_game(room_code, game)
                # Emitir a todos que el juego se actualizo
                self._emit_game_update(room_code)
                # Emitir evento especifico de reset_game
                self.emit_callback('game_reset', {'room_code': room_code, 'to_phase': to_phase}, room=room_code)
                # Si se reinicia a role_selection, emitir los roles actuales seleccionados
                if to_phase == "role_selection" and game.selected_roles:
                    self.emit_callback('roles_set', {'roles': game.selected_roles}, room=room_code)
                return True
            return False
        except Exception as e:
            print(f"Error en reset_game de GameService: {e}")
            return False

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
            # No necesitamos current_turn_player, solo current_turn_role
            
            for player_id, player in game.players.items():
                if player.is_connected and player.socket_id:
                    try:
                        private_state = game.get_private_state_for_player(player_id)
                        
                        # 🔧 FIX: Si estamos en turno de werewolf y este jugador es werewolf
                        if (current_turn_role == 'werewolf' and 
                            player.original_role == 'werewolf' and
                            game.phase.value == 'night_phase'):
                            
                            # Reenviar datos de night_action
                            night_action_data = game.get_night_action_data_for_player(player_id)
                            if night_action_data:
                                private_state['night_action'] = night_action_data
                                private_state['current_turn_role'] = 'werewolf'
                                private_state['is_your_turn'] = True
                                # Enviar tanto private_update como night_action separado
                                self.emit_callback('private_update', private_state, room=player.socket_id)
                                self.emit_callback('night_action', night_action_data, room=player.socket_id)
                                continue
                        
                        # 🔧 FIX: Si estamos en turno de mason y este jugador es mason
                        if (current_turn_role == 'mason' and 
                            player.original_role == 'mason' and
                            game.phase.value == 'night_phase'):
                            
                            # Reenviar datos de night_action
                            night_action_data = game.get_night_action_data_for_player(player_id)
                            if night_action_data:
                                private_state['night_action'] = night_action_data
                                private_state['current_turn_role'] = 'mason'
                                private_state['is_your_turn'] = True
                                # Enviar tanto private_update como night_action separado
                                self.emit_callback('private_update', private_state, room=player.socket_id)
                                self.emit_callback('night_action', night_action_data, room=player.socket_id)
                                continue

                        # 🔧 FIX: Si estamos en turno de seer y este jugador es seer
                        if (current_turn_role == 'seer' and 
                            player.original_role == 'seer' and
                            game.phase.value == 'night_phase'):
                            
                            # Reenviar datos de night_action
                            night_action_data = game.get_night_action_data_for_player(player_id)
                            if night_action_data:
                                private_state['night_action'] = night_action_data
                                private_state['current_turn_role'] = 'seer'
                                private_state['is_your_turn'] = True
                                # Enviar tanto private_update como night_action separado
                                self.emit_callback('private_update', private_state, room=player.socket_id)
                                self.emit_callback('night_action', night_action_data, room=player.socket_id)
                                continue
                        
                        # Emisión normal
                        self.emit_callback('private_update', private_state, room=player.socket_id)
                        
                    except Exception as player_error:
                        print(f"❌ Error emitiendo a jugador {player_id}: {player_error}")
                        import traceback
                        traceback.print_exc()
                        continue
        except Exception as e:
            print(f"❌ Error en _emit_game_update: {e}")
            import traceback
            traceback.print_exc()

    def _emit_turn_start(self, room_code: str, role: str, duration_override: Optional[int] = None):
        """🔧 FIX ARQUITECTURAL: Emite el evento de inicio de turno Y actualiza estados privados de manera unificada"""
        try:
            game = self.room_repository.get_game(room_code)
            if not game:
                return
            
            # Crear timestamp único para este turno
            turn_timestamp = time.time()
            
            # Emitir a toda la sala que comenzó el turno de un rol
            turn_data = {
                'role': role,
                'phase': f'Fase: {role}',
                'duration': duration_override if duration_override is not None else self._get_turn_duration(room_code),
                'timestamp': turn_timestamp
            }
            
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
                        
                        # Determinar si es el turno de este jugador (basado en rol original)
                        private_state['is_your_turn'] = (player.original_role == role)
                        
                        # Si es su turno, añadir datos de night_action
                        if private_state['is_your_turn']:
                            night_action_data = game.get_night_action_data_for_player(player_id)
                            if night_action_data:
                                private_state['night_action'] = night_action_data
                        
                        # Emitir private_update con datos completos y timestamp
                        self.emit_callback('private_update', private_state, room=player.socket_id)
                        
                    except Exception as player_error:
                        print(f"⚠️ Error emitiendo private_update unificado a {player_id}: {str(player_error)}")
                        continue
            
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
                return
            
            # Verificar si hay un rol actual válido
            current_role = game.get_current_turn_role()
            if not current_role:
                return
                
            # Invalidar cualquier timer anterior y generar un token nuevo
            token = self.turn_timer_tokens.get(room_code, 0) + 1
            self.turn_timer_tokens[room_code] = token
            
            def timer_task(expected_token: int):
                try:
                    # Sleep no bloqueante compatible con eventlet/Socket.IO
                    self.sleep_fn(self._get_turn_duration(room_code))
                    
                    # Si hubo un cancel o un nuevo timer, abortar
                    if self.turn_timer_tokens.get(room_code) != expected_token:
                        print(f"⚠️ Timer invalidado para sala {room_code}, token {expected_token}")
                        return
                    
                    self._auto_advance_turn(room_code)
                except Exception as e:
                    print(f"🔴 ERROR en timer_task para {room_code}: {str(e)}")
            
            # Iniciar tarea en background
            self.start_background_task(timer_task, token)
            
            # Registrar un log con el momento exacto del inicio del timer
            start_time = time.strftime("%H:%M:%S", time.localtime())
            expected_end = time.strftime("%H:%M:%S", 
                                         time.localtime(time.time() + self._get_turn_duration(room_code)))
            print(f"[TIMER] inicio sala {room_code} rol={current_role} dur={self._get_turn_duration(room_code)}s ({start_time} -> {expected_end})")
            
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
            game = self.room_repository.get_game(room_code)
            if not game:
                return
                
            if game.phase != GamePhase.NIGHT_PHASE:
                return
            
            # Registrar el turno actual antes de avanzar (para debugging)
            current_role_before = game.get_current_turn_role()
            print(f"[TIMER] fin sala {room_code} rol={current_role_before}")

            # ✅ Auto-acción del ladrón si no hizo click antes de expirar el turno
            if current_role_before == 'robber':
                auto_result = game.execute_robber_auto_action()
                if auto_result.get('success'):
                    robber_id = auto_result.get('robber_player_id')
                    if robber_id:
                        self._emit_to_player(room_code, robber_id, 'action_result', auto_result)
            # ✅ Auto-acción de la alborotadora si no hizo click antes de expirar el turno
            if current_role_before == 'troublemaker':
                auto_result = game.execute_troublemaker_auto_action()
                if auto_result.get('success'):
                    troublemaker_id = auto_result.get('troublemaker_player_id')
                    if troublemaker_id:
                        self._emit_to_player(room_code, troublemaker_id, 'action_result', auto_result)
            
            # ✅ Auto-acción del borracho si no hizo click antes de expirar el turno
            if current_role_before == 'drunk':
                auto_result = game.execute_drunk_auto_action()
                if auto_result.get('success'):
                    drunk_id = auto_result.get('drunk_player_id')
                    if drunk_id:
                        self._emit_to_player(room_code, drunk_id, 'action_result', auto_result)
            
            # Avanzar al siguiente turno
            advanced = game.advance_night_turn()
            
            # Guardar el estado actualizado del juego incluso si no avanzó
            # (podría haber cambios de estado internos)
            self.room_repository.save_game(room_code, game)
            
            if not advanced:
                return
            
            # Verificar si la noche terminó
            if game.night_finished:
                # Transición de 6 segundos antes del día
                self.room_repository.save_game(room_code, game)
                self._start_open_eyes_phase(room_code)
            else:
                # Continuar con el siguiente turno
                current_role = game.get_current_turn_role()
                
                if not current_role:
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
                    
                    # Verificar si es el turno del jugador (por rol original)
                    player_role = game.players[player_id].original_role
                    private_state['is_your_turn'] = (player_role == current_turn_role)
                    
                    # Si es su turno, incluir night_action data si está disponible
                    if private_state['is_your_turn']:
                        night_action_data = game.get_night_action_data_for_player(player_id)
                        if night_action_data:
                            private_state['night_action'] = night_action_data
            
            return private_state
            
        except Exception as e:
            print(f"Error en get_private_state: {e}")
            return None
