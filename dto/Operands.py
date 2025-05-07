from enum import Enum

from dataclasses import dataclass


class OperandType(str, Enum):
    MUCH = '>'
    LESS = '<'
    EQL = '=='
    MUCH_OR_EQL = '>='
    LESS_OR_EQL = '<='
    NOT_EQL = '!='


@dataclass
class Operand:
    operand: OperandType
