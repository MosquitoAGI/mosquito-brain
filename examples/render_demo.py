"""Render the demo animation in the README from the real pipeline.

    python examples/render_demo.py assets/mock-demo.gif

Every pixel in the output comes from running the same encoder, backend and
decoder the tests use. The telemetry fed in is synthetic, so the stop rule stays
quiet; the animation is a picture of software output, not of a robot.
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fruitfly_brain.config import Config  # noqa: E402
from fruitfly_brain.controller import Bridge, NullTransport  # noqa: E402
from fruitfly_brain.main import MockCamera  # noqa: E402
from fruitfly_brain.protocol import Telemetry, encode_telemetry, parse_packet  # noqa: E402

BACKGROUND = "#0d1117"
INK = "#c9d1d9"
ACCENT = "#79cce8"
ACCENT2 = "#60dfb3"
WARN = "#f0a35e"


def collect(frames: int, backend: str, fps: int):
    cfg = Config().validate()
    cfg.brain.backend = backend
    cfg.camera.fps = fps

    camera = MockCamera(cfg.camera.width, cfg.camera.height)
    transport = NullTransport()
    bridge = Bridge(cfg, transport)
    rows = []
    for i in range(frames):
        transport.inbox.append(
            encode_telemetry(
                Telemetry(
                    sequence=i + 1,
                    gyro=(0.2 * (i % 10 - 5) / 5.0, 0.0, 0.1),
                    accel=(0.0, 0.0, 0.98),
                    left_speed=20.0,
                    right_speed=20.0,
                )
            )
        )
        frame = camera.read()
        result = bridge.tick(frame, i * (1000.0 / fps))
        rows.append((frame, result, parse_packet(result.payload)))
    return rows


def draw(rows, index: int, fig, axes):
    frames = rows[: index + 1]
    frame, result, command = rows[index]
    ax_frame, ax_signal, ax_motor = axes

    ax_frame.clear()
    ax_frame.imshow(frame, cmap="gray", vmin=0, vmax=255)
    width = frame.shape[1]
    ax_frame.axvline(width // 2, color=ACCENT, lw=0.8, alpha=0.7)
    ax_frame.set_xticks([])
    ax_frame.set_yticks([])
    ax_frame.set_title("synthetic camera (160x120 encoder input)", color=INK, fontsize=9, loc="left")

    sensory = np.array([r[1].sensory.vector() for r in frames])
    ax_signal.clear()
    ax_signal.set_facecolor(BACKGROUND)
    window = sensory[-90:]
    ax_signal.plot(window[:, 0], color=ACCENT, lw=1.4, label="left motion")
    ax_signal.plot(window[:, 1], color=ACCENT2, lw=1.4, label="right motion")
    ax_signal.plot(window[:, 2], color=WARN, lw=1.4, label="approach cue")
    ax_signal.set_ylim(-4.5, 4.5)
    ax_signal.set_xlim(0, 90)
    ax_signal.tick_params(colors=INK, labelsize=7)
    ax_signal.grid(alpha=0.15)
    legend = ax_signal.legend(loc="upper left", fontsize=7, framealpha=0.1, ncols=3)
    for text in legend.get_texts():
        text.set_color(INK)
    ax_signal.set_title("encoder output (last 90 frames)", color=INK, fontsize=9, loc="left")

    commands = [r[2] for r in frames]
    left = [c.left for c in commands][-120:]
    right = [c.right for c in commands][-120:]
    ax_motor.clear()
    ax_motor.set_facecolor(BACKGROUND)
    ax_motor.plot(left, color=ACCENT, lw=1.6, label="left command")
    ax_motor.plot(right, color=ACCENT2, lw=1.6, label="right command")
    ax_motor.axhline(0, color=INK, lw=0.6, alpha=0.4)
    ax_motor.set_ylim(-70, 70)
    ax_motor.set_xlim(0, 120)
    ax_motor.tick_params(colors=INK, labelsize=7)
    ax_motor.grid(alpha=0.15)
    legend = ax_motor.legend(loc="upper left", fontsize=7, framealpha=0.1, ncols=2)
    for text in legend.get_texts():
        text.set_color(INK)
    ax_motor.set_title(
        "decoded motor commands  |  escape=%s" % ("yes" if result.escape else "no"),
        color=INK,
        fontsize=9,
        loc="left",
    )

    fig.suptitle(
        "fruitfly-brain  |  frame %d  |  left %.1f right %.1f  |  sequence %d"
        % (index, commands[-1].left, commands[-1].right, commands[-1].sequence),
        color=INK,
        fontsize=10,
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", default="assets/mock-demo.gif")
    parser.add_argument("--frames", type=int, default=90)
    parser.add_argument("--backend", default="connectome")
    parser.add_argument("--fps", type=int, default=20)
    args = parser.parse_args(argv)

    rows = collect(args.frames, args.backend, 30)
    fig, axes = plt.subplots(3, 1, figsize=(7.2, 6.0), dpi=110)
    fig.patch.set_facecolor(BACKGROUND)
    fig.subplots_adjust(left=0.07, right=0.985, top=0.90, bottom=0.05, hspace=0.45)

    images = []
    for i in range(len(rows)):
        draw(rows, i, fig, axes)
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", facecolor=BACKGROUND)
        buffer.seek(0)
        images.append(Image.open(buffer).convert("RGB").copy())

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(out, save_all=True, append_images=images[1:], duration=1000 // args.fps, loop=0)
    still = out.with_suffix(".png")
    images[-1].save(still)
    print("wrote %s (%d frames) and %s" % (out, len(images), still))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
