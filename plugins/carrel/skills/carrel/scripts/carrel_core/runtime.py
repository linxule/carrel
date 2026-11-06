from __future__ import annotations

from .cli import build_parser
from .core import CarrelError, emit_error


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except CarrelError as error:
        return emit_error(error)
