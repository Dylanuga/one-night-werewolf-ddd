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

class Role(ABC):
    """Clase base abstracta para todos los roles del juego"""
    
    def __init__(self, role_type: RoleType):
        self.role_type = role_type
        self.turn_order = self._get_turn_order()
    
    @abstractmethod
    def _get_turn_order(self) -> int:
        """Define el orden de turnos en la noche"""
        pass
    
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
    """Rol de la vidente/pitonisa (para futuras implementaciones)"""
    
    def __init__(self):
        super().__init__(RoleType.SEER)
    
    def _get_turn_order(self) -> int:
        return 2  # La pitonisa va después de los lobos
    
    def get_night_action_data(self, player_id: str, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # TODO: Implementar en el futuro
        return None
    
    def execute_action(self, player_id: str, action_data: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: Implementar en el futuro
        return {'success': False, 'message': 'Pitonisa no implementada aún'}

class RobberRole(Role):
    """Rol del ladrón (para futuras implementaciones)"""
    
    def __init__(self):
        super().__init__(RoleType.ROBBER)
    
    def _get_turn_order(self) -> int:
        return 3  # El ladrón va después de la pitonisa
    
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
        return 4  # El alborotador va después del ladrón
    
    def get_night_action_data(self, player_id: str, game_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # TODO: Implementar en el futuro
        return None
    
    def execute_action(self, player_id: str, action_data: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: Implementar en el futuro
        return {'success': False, 'message': 'Alborotador no implementado aún'}

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
            'troublemaker': TroublemakerRole
        }
        
        if role_type not in role_map:
            raise ValueError(f"Tipo de rol desconocido: {role_type}")
        
        return role_map[role_type]()