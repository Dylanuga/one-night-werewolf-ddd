# Clase Player: representa a un jugador

from typing import Dict, Any, Optional
from .roles import Role, RoleFactory

class Player:
    """Entidad que representa a un jugador en el juego"""
    
    def __init__(self, player_id: str, name: str, socket_id: str, is_host: bool = False):
        self.player_id = player_id
        self.name = name
        self.socket_id = socket_id
        self.is_host = is_host
        self.role: Optional[Role] = None
        self.original_role: Optional[str] = None  # Para tracking si cambia de rol
        self.is_connected = True
    
    def assign_role(self, role_type: str):
        """Asigna un rol al jugador"""
        self.role = RoleFactory.create_role(role_type)
        self.original_role = role_type
    
    def get_role_name(self) -> str:
        """Retorna el nombre del rol actual"""
        return self.role.role_type.value if self.role else "sin_rol"
    
    def can_act_at_night(self) -> bool:
        """Verifica si el jugador tiene acciones nocturnas"""
        return self.role and self.role.turn_order < 999
    
    def get_turn_order(self) -> int:
        """Retorna el orden de turno nocturno"""
        return self.role.turn_order if self.role else 999
    
    def disconnect(self):
        """Marca al jugador como desconectado"""
        self.is_connected = False
        self.socket_id = None
    
    def reconnect(self, socket_id: str):
        """Reconecta al jugador con un nuevo socket_id"""
        self.socket_id = socket_id
        self.is_connected = True
    
    def to_dict(self, include_role: bool = False) -> Dict[str, Any]:
        """Convierte el jugador a diccionario para serialización"""
        data = {
            'player_id': self.player_id,
            'name': self.name,
            'is_host': self.is_host,
            'is_connected': self.is_connected
        }
        
        if include_role and self.role:
            data['role'] = self.get_role_name()
            data['original_role'] = self.original_role
        
        return data
    
    def __str__(self):
        role_str = f" ({self.get_role_name()})" if self.role else ""
        host_str = " [HOST]" if self.is_host else ""
        return f"{self.name}{role_str}{host_str}"