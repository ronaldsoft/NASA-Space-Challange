#!/usr/bin/env python3
"""Pipeline completo: descarga, procesamiento y documentación."""

from __future__ import annotations

import sys

import download_earth
import download_planetary
import process
import write_docs


def main() -> int:
    download_planetary.main()
    rc = download_earth.main()
    if rc != 0:
        print("aviso: algunas teselas terrestres fallaron; se continúa con lo descargado")
    process.main()
    write_docs.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
