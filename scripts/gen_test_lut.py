"""Generate a test .cube LUT (4x4x4, warm tint) for LUTPass verification."""

import sys
from pathlib import Path

SIZE = 33
out_path = Path(__file__).parent.parent / "test_lut.cube"

lines = [
    "# splice test LUT - warm push (+5% red, -10% blue)",
    f"LUT_3D_SIZE {SIZE}",
    "LUT_3D_INPUT_RANGE 0.0 1.0",
    "",
]

# .cube ordering: R fastest, B slowest
for b in range(SIZE):
    for g in range(SIZE):
        for r in range(SIZE):
            ri = r / (SIZE - 1)
            gi = g / (SIZE - 1)
            bi = b / (SIZE - 1)
            # warm push: +5% red, -10% blue, green unchanged, all clamped
            ro = min(ri + 0.05, 1.0)
            go = gi
            bo = max(bi - 0.10, 0.0)
            lines.append(f"{ro:.6f} {go:.6f} {bo:.6f}")

out_path.write_text("\n".join(lines) + "\n")
print(f"Written {SIZE**3} entries → {out_path}")
