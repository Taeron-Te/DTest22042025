import code_generator
from code_generator import Code_generator


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
                antecedents = {
                    'oil_pressure': {'range': [0, 100, 1], 'terms': {
                        'low': ('trapmf', [0, 0, 30, 50]),
                        'normal': ('trapmf', [40, 60, 60, 80]),
                        'high': ('trapmf', [70, 90, 100, 100])
                    }},
                    'coolant_temp': {'range': [60, 120, 1], 'terms': {
                        'low': ('trapmf', [60, 60, 70, 80]),
                        'normal': ('trapmf', [75, 90, 90, 105]),
                        'high': ('trapmf', [100, 110, 120, 120])
                    }},
                    'vibration_level': {'range': [0, 10, 1], 'terms': {
                        'low': ('trapmf', [0, 2, 2, 4]),
                        'medium': ('trapmf', [3, 5, 5, 7]),
                        'high': ('trapmf', [6, 8, 8, 10])
                    }}
                }
                consequents = {
                    'engine_health': {
                        'range': [0, 100, 1],
                        'terms': {
                            'Critical': ('trapmf', [0, 0, 0, 50]),
                            'Warning': ('trapmf', [30, 50, 50, 70]),
                            'Good': ('trapmf', [50, 100, 100, 100])
                    }}
                }
                rule_definitions = [
                    {'if': [('oil_pressure', 'low'), ('coolant_temp', 'high'), ('vibration_level', 'high')],
                     'logic': 'or', 'then': ('engine_health', 'Critical')},
                    {'if': [('oil_pressure', 'normal'), ('coolant_temp', 'high')], 'logic': 'and',
                     'then': ('engine_health', 'Warning')},
                    {'if': [('oil_pressure', 'low'), ('coolant_temp', 'normal')], 'logic': 'and',
                     'then': ('engine_health', 'Warning')},
                    {'if': [('vibration_level', 'medium'), ('coolant_temp', 'normal')], 'logic': 'and',
                     'then': ('engine_health', 'Warning')},
                    {'if': [('oil_pressure', 'normal'), ('coolant_temp', 'normal'), ('vibration_level', 'low')],
                     'logic': 'and', 'then': ('engine_health', 'Good')},
                    {'if': [('oil_pressure', 'high'), ('coolant_temp', 'normal'), ('vibration_level', 'low')],
                     'logic': 'and', 'then': ('engine_health', 'Good')}
                ]
                lincs = [] #"lincA", "lincB", "lincC"
                while True:
                    tmp = input('Введите ссылки по порядку вопросов, Количество ссылок должно совпадать с количеством вопросов отправьте пустую строку, чтобы закончить... Пример "lincA", "lincB", "lincC"')
                    if tmp == "":
                        break
                    lincs.append(tmp)
                c.generate_fuzzy_system_file(input("filename"), antecedents, consequents, rule_definitions, lincs)

            case["get_all"]:
                c.get_generated_files()
            case ["end"]:
                break
