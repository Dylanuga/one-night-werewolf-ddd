# Definiciones de roles y sus habilidades
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum

class RoleType(Enum):
    WEREWOLF = "werewolf"
    VILLAGER = "villager"  
    SEER = "seer"
    ROBBER = "robber"
    TROUBLEMAKER = "troublemaker"
    TANNER = "tanner"
    DRUNK = "drunk"          # 🔧 AÑADIDO
    MASON = "mason"          # 🔧 AÑADIDO
    HUNTER = "hunter"        # 🔧 AÑADIDO
    INSOMNIAC = "insomniac"  # 🔧 AÑADIDO

class Role(ABC):
    """Clase base abstracta para todos los roles del juego"""
    
    def __init__(self, role_type: RoleType):
        self.role_type = role_type
        self.turn_order = self._get_turn_order()
    
    @abstractmethod
    def _get_turn_order(self) -> int:
        """Define el orden de turnos en la noche"""
        pass
    
    def can_act_at_night(self) -> bool:
        """Determina si este rol tiene acciones nocturnas"""
        # Por defecto, los roles con turn_order < 999 pueden actuar
        return self.get_turn_order() < 999
    
    def get_turn_order(self) -> int:
        """Retorna el orden de turno de este rol"""
        return self.turn_order
    
    @abstractmethod
    def get_night_action_data(self, player_id: str, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retorna los datos que necesita ver el jugador en su turno nocturno"""
        pass
    
    @abstractmethod
    def execute_action(self, player_id: str, action_data: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta la acción nocturna del role y retorna el resultado"""
        pass
    
    def __str__(self):
        return self.role_type.value

class WerewolfRole(Role):
    """Rol del hombre lobo"""
    
    def __init__(self):
        super().__init__(RoleType.WEREWOLF)
    
    def _get_turn_order(self) -> int:
        return 1  # Los lobos van primero
    
    def get_night_action_data(self, player_id: str, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Caso A: Si hay 2 lobos entre jugadores, muestran nombres mutuos
        Caso B: Si hay 1 lobo, puede ver una carta del centro
        Caso C: Si hay 0 lobos, no se muestra nada
        """
        werewolves_in_game = [
            pid for pid, player in game_state['players'].items() 
            if player['role'] == 'werewolf'
        ]
        
        werewolves_in_center = [
            i for i, role in enumerate(game_state['center_cards']) 
            if role == 'werewolf'
        ]
        
        # Caso A: Dos lobos entre jugadores
        if len(werewolves_in_game) == 2:
            other_werewolf = [wid for wid in werewolves_in_game if wid != player_id][0]
            other_werewolf_name = game_state['players'][other_werewolf]['name']
            return {
                'type': 'show_other_werewolf',
                'other_werewolf_name': other_werewolf_name,
                'message': f'El otro lobo es: {other_werewolf_name}'
            }
        
        # Caso B: Un lobo entre jugadores (puede ver carta del centro)
        elif len(werewolves_in_game) == 1:
            return {
                'type': 'can_view_center',
                'message': 'Eres el único lobo. Puedes ver una carta del centro.',
                'center_positions': [0, 1, 2]
            }
        
        # Caso C: No hay lobos entre jugadores
        return None
    
    def execute_action(self, player_id: str, action_data: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta la acción del lobo (ver carta del centro si está solo)"""
        werewolves_in_game = [
            pid for pid, player in game_state['players'].items() 
            if player['role'] == 'werewolf'
        ]
        
        # Solo el lobo solitario puede ejecutar acciones
        if len(werewolves_in_game) == 1 and 'center_position' in action_data:
            center_pos = action_data['center_position']
            if 0 <= center_pos <= 2:
                center_role = game_state['center_cards'][center_pos]
                return {
                    'success': True,
                    'message': f'Carta del centro {center_pos + 1}: {center_role}',
                    'center_position': center_pos,
                    'center_role': center_role
                }
        
        return {'success': False, 'message': 'Acción no válida'}

class VillagerRole(Role):
    """Rol del aldeano - sin acciones nocturnas"""
    
    def __init__(self):
        super().__init__(RoleType.VILLAGER)
    
    def _get_turn_order(self) -> int:
        return 999  # Los aldeanos no tienen turno nocturno
    
    def get_night_action_data(self, player_id: str, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return None  # Los aldeanos no hacen nada en la noche
    
    def execute_action(self, player_id: str, action_data: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        return {'success': False, 'message': 'Los aldeanos no tienen acciones nocturnas'}

class SeerRole(Role):
    """Rol de la vidente/pitonisa"""
    
    def __init__(self):
        super().__init__(RoleType.SEER)
    
    def _get_turn_order(self) -> int:
        return 3  # La pitonisa va despues de los masones
    
    def get_night_action_data(self, player_id: str, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # La pitonisa puede ver la carta de otro jugador o dos cartas del centro
        players = [
            {'id': pid, 'name': player['name']}
            for pid, player in game_state['players'].items()
            if pid != player_id
        ]

        return {
            'type': 'seer_choose',
            'message': 'Puedes ver la carta de otro jugador o dos cartas del centro.',
            'players': players,
            'center_positions': [0, 1, 2]
        }
    
    def execute_action(self, player_id: str, action_data: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        # Ver la carta de otro jugador
        target_player_id = action_data.get('target_player_id')
        if target_player_id:
            if target_player_id == player_id:
                return {'success': False, 'message': 'No puedes ver tu propia carta'}
            target_player = game_state['players'].get(target_player_id)
            if not target_player:
                return {'success': False, 'message': 'Jugador no valido'}
            target_role = target_player['role']
            target_name = target_player['name']
            return {
                'success': True,
                'message': f'Has visto el rol de {target_name}: {target_role}',
                'seen_player': {
                    'id': target_player_id,
                    'name': target_name,
                    'role': target_role
                }
            }

        # Ver dos cartas del centro
        center_positions = action_data.get('center_positions')
        if isinstance(center_positions, list) and len(center_positions) == 2:
            pos_a, pos_b = center_positions[0], center_positions[1]
            if pos_a == pos_b:
                return {'success': False, 'message': 'Debes elegir dos cartas distintas'}
            if not all(isinstance(pos, int) and 0 <= pos <= 2 for pos in [pos_a, pos_b]):
                return {'success': False, 'message': 'Posiciones de centro invalidas'}

            role_a = game_state['center_cards'][pos_a]
            role_b = game_state['center_cards'][pos_b]
            return {
                'success': True,
                'message': f'Has visto las cartas del centro {pos_a + 1} y {pos_b + 1}',
                'seen_center': [
                    {'position': pos_a, 'role': role_a},
                    {'position': pos_b, 'role': role_b}
                ]
            }

        return {'success': False, 'message': 'Accion no valida'}

class RobberRole(Role):
    """Rol del ladrón (para futuras implementaciones)"""
    
    def __init__(self):
        super().__init__(RoleType.ROBBER)
    
    def _get_turn_order(self) -> int:
        return 4  # El ladr?n va despu?s de la pitonisa
    
    def get_night_action_data(self, player_id: str, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # TODO: Implementar en el futuro
        return None
    
    def execute_action(self, player_id: str, action_data: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: Implementar en el futuro
        return {'success': False, 'message': 'Ladrón no implementado aún'}

class TroublemakerRole(Role):
    """Rol del alborotador (para futuras implementaciones)"""
    
    def __init__(self):
        super().__init__(RoleType.TROUBLEMAKER)
    
    def _get_turn_order(self) -> int:
        return 5  # El alborotador va despu?s del ladr?n
    
    def get_night_action_data(self, player_id: str, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # TODO: Implementar en el futuro
        return None
    
    def execute_action(self, player_id: str, action_data: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: Implementar en el futuro
        return {'success': False, 'message': 'Alborotador no implementado aún'}

class TannerRole(Role):
    """Rol del curtidor - gana si muere"""
    
    def __init__(self):
        super().__init__(RoleType.TANNER)
    
    def _get_turn_order(self) -> int:
        return 999  # El curtidor no tiene turno nocturno
    
    def get_night_action_data(self, player_id: str, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return None  # El curtidor no hace nada en la noche
    
    def execute_action(self, player_id: str, action_data: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        return {'success': False, 'message': 'El curtidor no tiene acciones nocturnas'}

# 🔧 NUEVOS ROLES AÑADIDOS
class DrunkRole(Role):
    """Rol del borracho - intercambia su carta con una del centro sin verla"""
    
    def __init__(self):
        super().__init__(RoleType.DRUNK)
    
    def _get_turn_order(self) -> int:
        return 6  # El borracho va despu?s del alborotador
    
    def get_night_action_data(self, player_id: str, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # TODO: Implementar en el futuro
        return None
    
    def execute_action(self, player_id: str, action_data: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: Implementar en el futuro
        return {'success': False, 'message': 'Borracho no implementado aún'}

class MasonRole(Role):
    """Rol del masón - se conocen entre ellos"""
    
    def __init__(self):
        super().__init__(RoleType.MASON)
    
    def _get_turn_order(self) -> int:
        return 2  # Los masones van después de los lobos
    
    def get_night_action_data(self, player_id: str, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Los masones se reconocen entre ellos.
        Si está solo, aparece el mensaje "Estás solo".
        Si ambos están en el centro, los demás esperan 6 segundos.
        """
        masons_in_game = [
            pid for pid, player in game_state['players'].items() 
            if player['role'] == 'mason'
        ]
        
        masons_in_center = [
            i for i, role in enumerate(game_state['center_cards']) 
            if role == 'mason'
        ]
        
        # Caso A: Dos masones entre jugadores - se reconocen
        if len(masons_in_game) == 2:
            other_mason = [mid for mid in masons_in_game if mid != player_id][0]
            other_mason_name = game_state['players'][other_mason]['name']
            return {
                'type': 'show_other_mason',
                'other_mason_name': other_mason_name,
                'message': f'Tu compañero masón es: {other_mason_name}'
            }
        
        # Caso B: Un masón entre jugadores (el otro está en el centro) - está solo
        elif len(masons_in_game) == 1:
            return {
                'type': 'alone',
                'message': 'Estás solo. Tu compañero masón no está en juego.'
            }
        
        # Caso C: Ambos masones están en el centro - no hay masones activos
        # Este caso se maneja en la lógica de juego principal (espera de 6 segundos)
        return None
    
    def execute_action(self, player_id: str, action_data: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        # Los masones no realizan acciones, solo se reconocen automáticamente
        return {'success': True, 'message': 'Los masones se han reconocido'}

class HunterRole(Role):
    """Rol del cazador - si muere, también muere el jugador al que apunte"""
    
    def __init__(self):
        super().__init__(RoleType.HUNTER)
    
    def _get_turn_order(self) -> int:
        return 999  # El cazador no tiene turno nocturno
    
    def get_night_action_data(self, player_id: str, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return None  # El cazador no hace nada en la noche
    
    def execute_action(self, player_id: str, action_data: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        return {'success': False, 'message': 'El cazador no tiene acciones nocturnas'}

class InsomniacRole(Role):
    """Rol del insomne - al final de la noche, ve su propia carta"""
    
    def __init__(self):
        super().__init__(RoleType.INSOMNIAC)
    
    def _get_turn_order(self) -> int:
        return 7  # El insomne va al final de todos los turnos
    
    def get_night_action_data(self, player_id: str, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # TODO: Implementar en el futuro
        return None
    
    def execute_action(self, player_id: str, action_data: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: Implementar en el futuro
        return {'success': False, 'message': 'Insomne no implementado aún'}

# Factory para crear roles
class RoleFactory:
    """Factory para crear instancias de roles"""
    
    @staticmethod
    def create_role(role_type: str) -> Role:
        role_map = {
            'werewolf': WerewolfRole,
            'villager': VillagerRole,
            'seer': SeerRole,
            'robber': RobberRole,
            'troublemaker': TroublemakerRole,
            'tanner': TannerRole,
            'drunk': DrunkRole,        # 🔧 AÑADIDO
            'mason': MasonRole,        # 🔧 AÑADIDO
            'hunter': HunterRole,      # 🔧 AÑADIDO
            'insomniac': InsomniacRole # 🔧 AÑADIDO
        }
        
        if role_type not in role_map:
            raise ValueError(f"Tipo de rol desconocido: {role_type}")
        
        return role_map[role_type]()