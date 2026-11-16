from typing import Any, Dict

from .base import ROLE_METADATA, Role
from .drunk import DrunkRole
from .insomniac import InsomniacRole
from .mason import MasonRole
from .passive_roles import HunterRole, TannerRole, VillagerRole
from .robber import RobberRole
from .seer import SeerRole
from .troublemaker import TroublemakerRole
from .werewolf import WerewolfRole


class RoleFactory:
    """Factory para crear instancias de roles y consultar el catálogo"""

    _ROLE_CLASSES = {
        "werewolf": WerewolfRole,
        "villager": VillagerRole,
        "seer": SeerRole,
        "robber": RobberRole,
        "troublemaker": TroublemakerRole,
        "tanner": TannerRole,
        "drunk": DrunkRole,
        "mason": MasonRole,
        "hunter": HunterRole,
        "insomniac": InsomniacRole
    }

    @classmethod
    def create_role(cls, role_type: str) -> Role:
        if role_type not in cls._ROLE_CLASSES:
            raise ValueError(f"Tipo de rol desconocido: {role_type}")
        return cls._ROLE_CLASSES[role_type]()

    @classmethod
    def get_catalog(cls) -> Dict[str, Dict[str, Any]]:
        return ROLE_METADATA.copy()

