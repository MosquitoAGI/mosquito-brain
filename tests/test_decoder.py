import pytest

from fruitfly_brain.config import MotorConfig
from fruitfly_brain.decoder import MotorDecoder


def make(max_command=60.0, dead_zone=4.0, smoothing=0.0, **kw):
    return MotorDecoder(MotorConfig(max_command=max_command, dead_zone=dead_zone, smoothing=smoothing, **kw))


def test_full_drive_maps_to_max_command():
    dec = make()
    cmd = dec.update(1.0, 1.0, False, 0.0)
    assert cmd.left == pytest.approx(60.0)
    assert cmd.right == pytest.approx(60.0)


def test_dead_zone_clamps_small_targets():
    dec = make(dead_zone=10.0)
    cmd = dec.update(0.1, 0.0, False, 0.0)  # 6 < dead zone
    assert cmd.left == 0.0 and cmd.right == 0.0


def test_smoothing_is_exponential():
    dec = make(smoothing=0.5)
    first = dec.update(1.0, 1.0, False, 0.0)
    second = dec.update(1.0, 1.0, False, 33.0)
    assert first.left == pytest.approx(30.0)
    assert second.left == pytest.approx(45.0)


def test_inversion_per_side():
    dec = make(invert_left=True)
    cmd = dec.update(1.0, 1.0, False, 0.0)
    assert cmd.left == pytest.approx(-60.0)
    assert cmd.right == pytest.approx(60.0)


def test_escape_bypasses_smoothing():
    dec = make(smoothing=0.8)
    cmd = dec.update(0.1, 0.1, True, 0.0)
    assert cmd.left == pytest.approx(60.0)
    assert cmd.reason == "escape"
    assert dec.escapes == 1


def test_read_is_zero_before_any_update():
    dec = make()
    assert dec.read(0.0).stale is True


def test_read_goes_stale_after_timeout():
    dec = make()
    dec.update(1.0, 1.0, False, 1000.0)
    assert dec.read(1200.0).stale is False
    assert dec.read(1600.0).stale is True
    assert dec.read(1600.0).left == 0.0


def test_emergency_stop_latches_until_cleared():
    dec = make()
    dec.update(1.0, 1.0, False, 0.0)
    stop = dec.emergency_stop(10.0)
    assert stop.emergency_stop and stop.left == 0.0
    again = dec.update(1.0, 1.0, False, 20.0)
    assert again.emergency_stop is True and again.left == 0.0
    dec.clear_emergency()
    assert dec.update(1.0, 1.0, False, 30.0).left == pytest.approx(60.0)


def test_zero_now_does_not_latch():
    dec = make()
    dec.update(1.0, 1.0, False, 0.0)
    dec.zero_now(50.0)
    resumed = dec.update(1.0, 1.0, False, 60.0)
    assert resumed.left == pytest.approx(60.0)
    assert resumed.emergency_stop is False


def test_drives_outside_unit_range_rejected():
    dec = make()
    with pytest.raises(ValueError):
        dec.update(1.4, 0.0, False, 0.0)
