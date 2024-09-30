import pytest

from fruitfly_brain.config import Config, ConfigError, from_dict, load


def test_defaults_are_valid():
    cfg = Config().validate()
    assert cfg.camera.fps == 30
    assert cfg.brain.backend == "mock"


def test_unknown_section_rejected():
    with pytest.raises(ConfigError, match="unknown config sections"):
        from_dict({"brainz": {}})


def test_unknown_key_rejected():
    with pytest.raises(ConfigError, match="unknown keys in motor"):
        from_dict({"motor": {"max_speed": 10}})


def test_bad_values_rejected():
    with pytest.raises(ConfigError, match="dead_zone"):
        from_dict({"motor": {"max_command": 40, "dead_zone": 50}})
    with pytest.raises(ConfigError, match="backend"):
        from_dict({"brain": {"backend": "gpt"}})
    with pytest.raises(ConfigError, match="fps"):
        from_dict({"camera": {"fps": 0}})
    with pytest.raises(ConfigError, match="blur"):
        from_dict({"vision": {"blur": 4}})


def test_ports_must_differ():
    with pytest.raises(ConfigError, match="ports must differ"):
        from_dict({"network": {"robot_port": 9000, "bind_port": 9000}})


def test_load_roundtrip(tmp_path):
    text = """
camera:
  fps: 24
brain:
  backend: connectome
motor:
  max_command: 45
"""
    p = tmp_path / "config.yaml"
    p.write_text(text, encoding="utf-8")
    cfg = load(p)
    assert cfg.camera.fps == 24
    assert cfg.brain.backend == "connectome"
    assert cfg.motor.max_command == 45


def test_missing_file_is_a_config_error():
    with pytest.raises(ConfigError, match="not found"):
        load("/nonexistent/config.yaml")
