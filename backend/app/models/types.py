from enum import Enum
from typing import TypeVar

from sqlalchemy import Enum as SAEnum

E = TypeVar("E", bound=Enum)


def str_enum(enum_cls: type[E], name: str) -> SAEnum:
    """VARCHAR + CHECK constraint instead of a native Postgres ENUM: this project's enums
    (etapa, origem, tipo, ...) are expected to grow (dois níveis de risco jurídico, novas
    fontes de leilão), and CHECK migrates with a plain ALTER TABLE while native ENUM requires
    ALTER TYPE outside a transaction on older Postgres versions."""
    return SAEnum(enum_cls, name=name, native_enum=False, values_callable=lambda obj: [e.value for e in obj])
