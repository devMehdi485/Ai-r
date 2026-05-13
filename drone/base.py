"""Interface abstraite pour tout drone (réel ou simulé)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass
class DroneState:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    yaw: float = 0.0
    battery: float = 100.0
    is_flying: bool = False


class BaseDrone(ABC):
    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def disconnect(self) -> None: ...

    @abstractmethod
    async def takeoff(self) -> None: ...

    @abstractmethod
    async def land(self) -> None: ...

    @abstractmethod
    async def move(self, dx: float, dy: float, dz: float) -> None:
        """Déplacement relatif en mètres dans le repère du drone."""

    @abstractmethod
    async def rotate(self, degrees: float) -> None:
        """Rotation autour de l'axe yaw, positif = horaire."""

    @abstractmethod
    async def get_video_frame(self) -> np.ndarray: ...

    @abstractmethod
    async def get_state(self) -> DroneState: ...

    @abstractmethod
    async def emergency_stop(self) -> None: ...
