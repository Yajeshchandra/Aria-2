from __future__ import annotations

import ast
import threading
from collections import deque
from pathlib import Path
from typing import Any, Optional

import numpy as np

module_path = Path(__file__).with_name("watch_and_tell_aria_gen2.py")
tree = ast.parse(module_path.read_text(encoding="utf-8"))
node = next(
    item for item in tree.body
    if isinstance(item, ast.ClassDef) and item.name == "AudioRingBuffer"
)
namespace = {
    "np": np,
    "Any": Any,
    "Optional": Optional,
    "deque": deque,
    "threading": threading,
    "SAMPLE_RATE": 16_000,
}
exec(compile(ast.Module(body=[node], type_ignores=[]), str(module_path), "exec"), namespace)
AudioRingBuffer = namespace["AudioRingBuffer"]

cases = [
    (np.array([-17, 0, 19], dtype=np.int16), "signed-int16", [-17, 0, 19]),
    (np.array([65535, 0, 1], dtype=np.uint16), "unsigned-low16-uint16", [-1, 0, 1]),
    (np.array([-17, 0, 19], dtype=np.int64) << 16, "signed-q16-shift-int64", [-17, 0, 19]),
]
for raw, expected_name, expected_pcm in cases:
    pcm, name = AudioRingBuffer._to_pcm16(raw)
    assert name == expected_name, (name, expected_name)
    assert pcm.tolist() == expected_pcm, (pcm.tolist(), expected_pcm)

print("Audio conversion tests passed.")
