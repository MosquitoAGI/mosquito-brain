"""The eye.

One frame in, a small fixed-width sensory vector out. The encoder does not try
to recognise anything: it reports how much motion sits in the left and right
half of the field, how fast the covered area of the field is growing, and the
mean luminance. Everything downstream is built on those numbers.

A note on the looming channel: the first implementation used the radial
component of the optical flow (mean of ``v . r/|r|``), which is the textbook
way to detect approach. On synthetic blobs Farneback returns the *wrong sign*
at a growth boundary — measured on a disc growing 12 px -> 26 px the radial
mean reads negative, i.e. "receding" — and its divergence is numerically zero
at this resolution. The frame-to-frame change in covered area has the correct
sign on the same input, survives compression noise and costs nothing extra, so
that is what this module reports. See ``docs/VALIDATION.md`` for the numbers.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import VisionConfig

try:  # pragma: no cover - exercised in CI by installing the extra
    import cv2
except Exception:  # pragma: no cover
    cv2 = None


@dataclass
class SensoryFrame:
    """Sensory reading for one frame."""

    left: float
    right: float
    expansion: float
    luminance: float

    def vector(self) -> np.ndarray:
        return np.array([self.left, self.right, self.expansion, self.luminance], dtype=np.float64)


def _to_gray(frame: np.ndarray) -> np.ndarray:
    if frame.ndim == 2:
        gray = frame
    elif frame.ndim == 3 and frame.shape[2] in (3, 4):
        # OpenCV convention (BGR); a mean over the first three channels is close
        # enough here and keeps the numpy-only path free of colour constants.
        gray = frame[:, :, :3].mean(axis=2)
    else:
        raise ValueError("unsupported frame shape: %r" % (frame.shape,))
    return np.asarray(gray, dtype=np.float32)


class Encoder:
    """Motion encoder.

    ``encode`` keeps only the previous frame: call ``reset`` between sessions.
    """

    def __init__(self, cfg: VisionConfig | None = None):
        self.cfg = cfg or VisionConfig()
        self.cfg.validate()
        self._prev: np.ndarray | None = None
        self._prev_coverage = 0.0
        self.frames = 0

    def reset(self) -> None:
        self._prev = None
        self._prev_coverage = 0.0
        self.frames = 0

    # ------------------------------------------------------------------ frames
    def _prepare(self, frame: np.ndarray) -> np.ndarray:
        gray = _to_gray(frame)
        target = (self.cfg.width, self.cfg.height)
        if gray.shape[::-1] != target:
            if cv2 is not None:
                gray = cv2.resize(gray, target, interpolation=cv2.INTER_AREA)
            else:
                rows = np.linspace(0, gray.shape[0] - 1, target[1]).astype(int)
                cols = np.linspace(0, gray.shape[1] - 1, target[0]).astype(int)
                gray = gray[np.ix_(rows, cols)]
        if self.cfg.blur >= 3:
            k = self.cfg.blur
            if cv2 is not None:
                gray = cv2.GaussianBlur(gray, (k, k), 0)
            else:
                pad = k // 2
                padded = np.pad(gray, pad, mode="edge")
                acc = np.zeros_like(gray)
                for dy in range(k):
                    for dx in range(k):
                        acc += padded[dy : dy + gray.shape[0], dx : dx + gray.shape[1]]
                gray = acc / float(k * k)
        return gray

    def _coverage(self, gray: np.ndarray) -> float:
        """Fraction of the field below/above the midpoint of its own range."""
        lo, hi = float(gray.min()), float(gray.max())
        if hi - lo < 8.0:  # flat frame, nothing to cover
            return 0.0
        return float((gray > (lo + 0.5 * (hi - lo))).mean())

    def _flow(self, prev: np.ndarray, cur: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        if cv2 is not None:
            flow = cv2.calcOpticalFlowFarneback(prev, cur, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            return flow[..., 0], flow[..., 1]
        # numpy-only fallback: horizontal / vertical gradients of the frame
        # difference. Coarser than Farneback, good enough for a moving blob and
        # keeps the package importable without OpenCV.
        diff = cur - prev
        dx = np.zeros_like(prev)
        dy = np.zeros_like(prev)
        dx[:, 1:] = diff[:, 1:]
        dy[1:, :] = diff[1:, :]
        return dx, dy

    # ------------------------------------------------------------------ encode
    def encode(self, frame: np.ndarray) -> SensoryFrame:
        gray = self._prepare(frame)
        coverage = self._coverage(gray)
        if self._prev is None:
            self._prev = gray
            self._prev_coverage = coverage
            self.frames += 1
            return SensoryFrame(0.0, 0.0, 0.0, float(gray.mean()) / 255.0)

        u, v = self._flow(self._prev, gray)
        mag = np.sqrt(u * u + v * v)
        half = self.cfg.width // 2
        left = float(mag[:, :half].mean()) * self.cfg.gain
        right = float(mag[:, half:].mean()) * self.cfg.gain
        expansion = (coverage - self._prev_coverage) * self.cfg.looming_gain

        self._prev = gray
        self._prev_coverage = coverage
        self.frames += 1

        clip = lambda x: float(np.clip(x, -8.0, 8.0))  # noqa: E731
        return SensoryFrame(
            left=clip(left),
            right=clip(right),
            expansion=clip(expansion),
            luminance=float(gray.mean()) / 255.0,
        )
