#!/usr/bin/env python3
"""Descarga (o reanuda) MOLA MEGDR 64 ppd y LOLA LDEM_64 desde el PDS."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from config import LOLA_IMG_URL, LOLA_LBL_URL, MOLA_BASE, MOLA_TILES, RAW_MARS, RAW_MOON


def curl(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1000:
        print(f"  existe {dest.name} ({dest.stat().st_size} B)")
        return
    tmp = dest.with_suffix(dest.suffix + ".part")
    cmd = [
        "curl", "-fL", "--retry", "8", "--retry-delay", "5",
        "--retry-all-errors", "-C", "-", "-o", str(tmp), url,
    ]
    print(f"  descargando {dest.name} <- {url}")
    subprocess.check_call(cmd)
    tmp.rename(dest)
    print(f"  ok {dest.name} ({dest.stat().st_size} B)")


def main() -> int:
    for name in MOLA_TILES:
        curl(f"{MOLA_BASE}/{name}.lbl", RAW_MARS / f"{name}.lbl")
        curl(f"{MOLA_BASE}/{name}.img", RAW_MARS / f"{name}.img")
    curl(LOLA_LBL_URL, RAW_MOON / "ldem_64.lbl")
    curl(LOLA_IMG_URL, RAW_MOON / "ldem_64.img")
    return 0


if __name__ == "__main__":
    sys.exit(main())
