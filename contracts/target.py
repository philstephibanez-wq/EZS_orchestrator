from __future__ import annotations

from enum import Enum


class Target(str, Enum):
    DEV = "dev"
    PROD = "prod"
    LAB = "lab"
