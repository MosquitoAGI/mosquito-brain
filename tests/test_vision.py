import numpy as np
import pytest

from fruitfly_brain.config import VisionConfig
from fruitfly_brain.vision import Encoder


def make_encoder(**kw):
    return Encoder(VisionConfig(**kw))


def blob_frame(width, height, cx, cy, radius=10):
    frame = np.zeros((height, width), dtype=np.uint8)
    yy, xx = np.ogrid[:height, :width]
    frame[(xx - cx) ** 2 + (yy - cy) ** 2 <= radius**2] = 255
    return frame


def test_first_frame_is_neutral():
    enc = make_encoder()
    sensory = enc.encode(blob_frame(160, 120, 50, 60))
    assert sensory.left == 0.0 and sensory.right == 0.0
    assert 0.0 <= sensory.luminance <= 1.0


def test_motion_in_left_half_reported_as_left():
    enc = make_encoder(blur=0)
    enc.encode(blob_frame(160, 120, 20, 60))
    sensory = enc.encode(blob_frame(160, 120, 60, 60))
    assert sensory.left > sensory.right
    assert sensory.left > 0.01


def test_motion_in_right_half_reported_as_right():
    enc = make_encoder(blur=0)
    enc.encode(blob_frame(160, 120, 100, 60))
    sensory = enc.encode(blob_frame(160, 120, 140, 60))
    assert sensory.right > sensory.left


def test_growing_blob_reads_as_expansion():
    enc = make_encoder(blur=0, looming_gain=4.0)
    enc.encode(blob_frame(160, 120, 80, 60, radius=12))
    sensory = enc.encode(blob_frame(160, 120, 80, 60, radius=26))
    assert sensory.expansion > 0.0


def test_static_scene_is_quiet():
    enc = make_encoder(blur=0)
    frame = blob_frame(160, 120, 80, 60)
    enc.encode(frame)
    sensory = enc.encode(frame)
    assert abs(sensory.left) < 1e-6
    assert abs(sensory.right) < 1e-6
    assert abs(sensory.expansion) < 1e-6


def test_values_are_clipped():
    enc = make_encoder(gain=1e6, blur=0)
    enc.encode(np.zeros((120, 160), dtype=np.uint8))
    sensory = enc.encode(np.full((120, 160), 255, dtype=np.uint8))
    assert abs(sensory.left) <= 8.0 and abs(sensory.expansion) <= 8.0


def test_unsupported_shape_raises():
    enc = make_encoder()
    with pytest.raises(ValueError):
        enc.encode(np.zeros((4, 4, 7), dtype=np.uint8))


def test_reset_clears_history():
    enc = make_encoder()
    enc.encode(blob_frame(160, 120, 20, 60))
    enc.reset()
    sensory = enc.encode(blob_frame(160, 120, 140, 60))
    assert sensory.left == 0.0 and sensory.right == 0.0
