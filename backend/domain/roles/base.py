# Definiciones base de roles y catálogo centralizado
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional


class RoleType(Enum):
    WEREWOLF = "werewolf"
    VILLAGER = "villager"
    SEER = "seer"
    ROBBER = "robber"
    TROUBLEMAKER = "troublemaker"
    TANNER = "tanner"
    DRUNK = "drunk"
    MASON = "mason"
    HUNTER = "hunter"
    INSOMNIAC = "insomniac"


POS_NAMES_ES: Dict[int, str] = {
    0: "izquierda",
    1: "centro",
    2: "derecha"
}

# Catálogo único de metadatos de roles (fuente de verdad para dominio y API)
ROLE_METADATA: Dict[str, Dict[str, Any]] = {
    "werewolf": {
        "id": "werewolf",
        "name": "Lobo",
        "team": "werewolves",
        "turn_order": 1,
        "max_count": 2,
        "emoji": "🐺",
        "color": "#dc2626",
        "interaction_type": "select_center_cards",
        "description": "Se conocen entre ellos. Si está solo, ve una carta del centro."
    },
    "mason": {
        "id": "mason",
        "name": "Masón",
        "team": "villagers",
        "turn_order": 2,
        "max_count": 2,
        "emoji": "🔨",
        "color": "#0891b2",
        "interaction_type": "passive_info",
        "description": "Se conocen entre ellos (siempre van de 2 en 2)."
    },
    "seer": {
        "id": "seer",
        "name": "Vidente",
        "team": "villagers",
        "turn_order": 3,
        "max_count": 1,
        "emoji": "🔮",
        "color": "#7c3aed",
        "interaction_type": "select_player_or_center",
        "description": "Ve la carta de otro jugador o dos cartas del centro."
    },
    "robber": {
        "id": "robber",
        "name": "Ladrón",
        "team": "villagers",
        "turn_order": 4,
        "max_count": 1,
        "emoji": "🥷",
        "color": "#ea580c",
        "interaction_type": "select_one_player",
        "description": "Intercambia su carta con la de otro jugador y ve su nuevo rol."
    },
    "troublemaker": {
        "id": "troublemaker",
        "name": "Alborotadora",
        "team": "villagers",
        "turn_order": 5,
        "max_count": 1,
        "emoji": "🃏",
        "color": "#db2777",
        "interaction_type": "select_two_players",
        "description": "Intercambia las cartas de dos jugadores sin verlas."
    },
    "drunk": {
        "id": "drunk",
        "name": "Borracho",
        "team": "villagers",
        "turn_order": 6,
        "max_count": 1,
        "emoji": "🍺",
        "color": "#ca8a04",
        "interaction_type": "select_center_cards",
        "description": "Intercambia su carta con una del centro sin verla."
    },
    "insomniac": {
        "id": "insomniac",
        "name": "Insomne",
        "team": "villagers",
        "turn_order": 7,
        "max_count": 1,
        "emoji": "😴",
        "color": "#6366f1",
        "interaction_type": "passive_info",
        "description": "Al final de la noche, ve su propia carta (que pudo haber cambiado)."
    },
    "villager": {
        "id": "villager",
        "name": "Aldeano",
        "team": "villagers",
        "turn_order": 999,
        "max_count": 8,
        "emoji": "👨‍🌾",
        "color": "#16a34a",
        "interaction_type": "none",
        "description": "Sin habilidad especial. Debe deducir quiénes son los lobos."
    },
    "hunter": {
        "id": "hunter",
        "name": "Cazador",
        "team": "villagers",
        "turn_order": 999,
        "max_count": 1,
        "emoji": "🏹",
        "color": "#059669",
        "interaction_type": "none",
        "description": "Si muere linchado, también muere el jugador al que haya votado."
    },
    "tanner": {
        "id": "tanner",
        "name": "Curtidor",
        "team": "tanner",
        "turn_order": 999,
        "max_count": 1,
        "emoji": "🪣",
        "color": "#8b5cf6",
        "interaction_type": "none",
        "description": "Gana únicamente si consigue ser linchado."
    }
}

ROLE_NAMES_ES: Dict[str, str] = {
    role_id: meta["name"] for role_id, meta in ROLE_METADATA.items()
}


class Role(ABC):
    """Clase base abstracta para todos los roles del juego"""

    def __init__(self, role_type: RoleType):
        self.role_type = role_type
        self.turn_order = self._get_turn_order()

    @abstractmethod
    def _get_turn_order(self) -> int:
        """Define el orden de turnos en la noche"""
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """Retorna los metadatos estáticos del rol desde el catálogo central"""
        return ROLE_METADATA.get(self.role_type.value, {})

    def can_act_at_night(self) -> bool:
        """Determina si este rol tiene turno durante la noche"""
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
        """Ejecuta la acción nocturna sobre un snapshot de estado (compatibilidad)"""
        pass

    def execute_night_action_on_game(
        self,
        game: Any,
        player_id: str,
        action_data: Dict[str, Any],
        is_auto: bool = False
    ) -> Dict[str, Any]:
        """Ejecuta la acción nocturna directamente sobre la instancia de GameLogic"""
        return self.execute_action(player_id, action_data, game._get_game_state())

    def execute_auto_action_on_game(self, game: Any) -> Dict[str, Any]:
        """Ejecuta la acción automática aleatoria al expirar el tiempo del turno"""
        return {"success": False, "message": "Este rol no tiene acción automática"}

    def on_death_trigger(
        self,
        game: Any,
        dead_player_id: str,
        votes: Dict[str, Optional[str]]
    ) -> List[str]:
        """Hook polimórfico al morir en la votación (p. ej. disparo del Cazador)"""
        return []

    def __str__(self):
        return self.role_type.value

