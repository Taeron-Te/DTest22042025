import code_generator
from code_generator import Code_generator
from dto.Operands import Operand, OperandType


if __name__ == '__main__':
    c = Code_generator()
    while True:
        match input("").split():
            case["Примитив"]:
                c.primitive_generate(input("text"), input("answer"),input("operand"), input("filename"), input("linka"), input("linkb"))
            case["Match"]:
                lincs = []
                a = []
                while True:
                    tmp = input("Введите вопросы по порядку, отправьте пустую строку, чтобы закончить... ")
                    if tmp == "":
                        break
                    a.append(tmp)
                while True:
                    tmp = input("Введите ссылки по порядку вопросов, Количество ссылок должно совпадать с количеством вопросов отправьте пустую строку, чтобы закончить... ")
                    if tmp == "":
                        break
                    lincs.append(tmp)
                c.match_generate(input("text"), a, lincs, input("default link"), input("filename"))
            case["FL"]:

                c.generate_fuzzy_system_file(input("filename"), input("system_name"))

            case["get_all"]:
                c.get_generated_files()
            case ["end"]:
                break
