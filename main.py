from code_generator import Code_generator
from dto.Operands import Operand, OperandType


if __name__ == '__main__':
    c = Code_generator("Вам нравится еда в ресторане?", ["Да", "Нет"], o='==')
    c.match_generate()
    c()




