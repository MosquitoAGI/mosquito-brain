"""Configuration objects.

Everything the bridge does is driven by this file. Values are validated on
construction, so a typo in ``config.yaml`` fails at startup with a readable
message instead of steering a robot with a wrong number.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when a configuration value is outside its allowed range."""


@dataclass
class CameraConfig:
    index: int = 0
    width: int = 320
    height: int = 240
    fps: int = 30

    def validate(self) -> None:
        if self.index < 0:
            raise ConfigError("camera.index must be >= 0")
        if self.width < 32 or self.height < 32:
            raise ConfigError("camera size must be at least 32x32")
        if not 1 <= self.fps <= 240:
            raise ConfigError("camera.fps must be in 1..240")


@dataclass
class VisionConfig:
    width: int = 160
    height: int = 120
    gain: float = 6.0
    looming_gain: float = 1.5
    blur: int = 3

    def validate(self) -> None:
        if self.width < 16 or self.height < 16:
            raise ConfigError("vision size must be at least 16x16")
        if self.gain <= 0 or self.looming_gain <= 0:
            raise ConfigError("vision gains must be positive")
        if self.blur < 0 or (self.blur != 0 and self.blur % 2 == 0):
            raise ConfigError("vision.blur must be 0 or an odd number")


@dataclass
class BrainConfig:
    backend: str = "mock"
    leak_ms: float = 120.0
    escape_threshold: float = 0.72
    seed: int = 7

    def validate(self) -> None:
        if self.backend not in ("mock", "connectome"):
            raise ConfigError("brain.backend must be 'mock' or 'connectome'")
        if self.leak_ms <= 0:
            raise ConfigError("brain.leak_ms must be positive")
        if not 0.0 < self.escape_threshold <= 1.0:
            raise ConfigError("brain.escape_threshold must be in (0, 1]")


@dataclass
class MotorConfig:
    max_command: float = 60.0
    dead_zone: float = 4.0
    smoothing: float = 0.35
    invert_left: bool = False
    invert_right: bool = False
    command_timeout_ms: float = 500.0

    def validate(self) -> None:
        if not 1.0 <= self.max_command <= 100.0:
            raise ConfigError("motor.max_command must be in 1..100")
        if not 0.0 <= self.dead_zone < self.max_command:
            raise ConfigError("motor.dead_zone must be smaller than max_command")
        if not 0.0 <= self.smoothing < 1.0:
            raise ConfigError("motor.smoothing must be in [0, 1)")
        if self.command_timeout_ms <= 0:
            raise ConfigError("motor.command_timeout_ms must be positive")


@dataclass
class NetworkConfig:
    robot_host: str = "192.168.4.1"
    robot_port: int = 9000
    bind_port: int = 9001
    telemetry_timeout_ms: float = 400.0

    def validate(self) -> None:
        for name, port in (("robot_port", self.robot_port), ("bind_port", self.bind_port)):
            if not 1 <= port <= 65535:
                raise ConfigError("network.%s must be a valid port" % name)
        if self.robot_port == self.bind_port:
            raise ConfigError("network ports must differ")
        if self.telemetry_timeout_ms <= 0:
            raise ConfigError("network.telemetry_timeout_ms must be positive")
        if not self.robot_host:
            raise ConfigError("network.robot_host must not be empty")


@dataclass
class LogConfig:
    dir: str = "runs"
    jsonl: bool = True
    every_n_frames: int = 5

    def validate(self) -> None:
        if not self.dir:
            raise ConfigError("log.dir must not be empty")
        if self.every_n_frames < 1:
            raise ConfigError("log.every_n_frames must be >= 1")


@dataclass
class Config:
    camera: CameraConfig = field(default_factory=CameraConfig)
    vision: VisionConfig = field(default_factory=VisionConfig)
    brain: BrainConfig = field(default_factory=BrainConfig)
    motor: MotorConfig = field(default_factory=MotorConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    log: LogConfig = field(default_factory=LogConfig)

    def validate(self) -> "Config":
        for section in (self.camera, self.vision, self.brain, self.motor, self.network, self.log):
            section.validate()
        return self

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_SECTIONS = {
    "camera": CameraConfig,
    "vision": VisionConfig,
    "brain": BrainConfig,
    "motor": MotorConfig,
    "network": NetworkConfig,
    "log": LogConfig,
}


def from_dict(data: dict[str, Any] | None) -> Config:
    """Build a validated config from a plain dictionary."""
    data = data or {}
    unknown = set(data) - set(_SECTIONS)
    if unknown:
        raise ConfigError("unknown config sections: %s" % ", ".join(sorted(unknown)))
    kwargs = {}
    for name, cls in _SECTIONS.items():
        raw = data.get(name) or {}
        if not isinstance(raw, dict):
            raise ConfigError("config section %r must be a mapping" % name)
        allowed = set(cls.__dataclass_fields__)
        extra = set(raw) - allowed
        if extra:
            raise ConfigError("unknown keys in %s: %s" % (name, ", ".join(sorted(extra))))
        kwargs[name] = cls(**raw)
    return Config(**kwargs).validate()


def load(path: str | Path) -> Config:
    p = Path(path)
    if not p.exists():
        raise ConfigError("config file not found: %s" % p)
    with p.open(encoding="utf-8") as fh:
        return from_dict(yaml.safe_load(fh))
