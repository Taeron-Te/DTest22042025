
class Code_generator:
    __code_was_gendered = 0
    __generated_file_names = []


    # Добавление нового элемента в общий пул
    def __add(self, fn):
        Code_generator.__code_was_gendered += 1
        Code_generator.__generated_file_names.append(fn)
    # Получаем элементы из общего пула

    def get_generated_files(self):
        print(self.__generated_file_names)
        for j, i in enumerate(self.__generated_file_names):
            print(j, i)
        return self.__generated_file_names

    # Получаем все файлы содержащие t в названии
    def get_file_by_name(self, t):
        tmp = []
        for i in self.__generated_file_names:
            if i == t:
                print(i)
                tmp.append(i)
        return tmp

    # Бинарный блок
    def primitive_generate(self, txt, f='', linka='', linkb='' ):
        filename = f
        if filename == 'LAST' and Code_generator.__generated_file_names != []:
            filename = Code_generator.__generated_file_names.pop()
        if filename == '':
            filename = 'b' + str(self.__hash__())
        generated = ''
        if linka == '':
            linka = "#"
            print("Пропущено значение linka")
        else:
            generated += f'''
from {linka} import {linka}
'''
        if linkb == '':
            linkb = "#"
            print("Пропущено значение linkb")
        else:
            generated += f'''
from {linkb} import {linkb}
'''

        generated += f'''
def {filename}():
    print("{txt}")
    b = input()
    if "Да" == b:
        {linka}()
        return True
    else:
        {linkb}() 
        return False       
'''
        with open(f"generated/{filename}.py", 'w', encoding='utf-8') as file:
            file.write(generated)

        self.__add(filename)
        print(filename)
        return filename
    # Не бинарный блок выбора
    def match_generate(self, txt, q: list, lincs: list[str], f=''):
        # Генерация имени
        filename = f
        if filename == '':
            filename = 'm' + str(self.__hash__())
        generated = ''
        if len(lincs) > 0:
            for i in lincs:
                generated += f"""
from {i} import {i}
"""
        # Тело функции
        generated += f'''
def {filename}():
    print("{txt}")
    b = input("{q}")
    match b.split():
'''
        # Генерация кейсов
        for i in q:
            generated += f'''               
        case ["{i}"]:
        '''
            try:
                generated += f'''
            {lincs[q.index(i)]}()
            '''
            except:
                generated += f'''
            #()'''
                print("Пропущено значение ссылки")
            generated += f'''
            print("{i}")
            '''
        generated += f'''
        case _:
            {filename}()
            print("default")'''
        # Запись файла
        with open(f"generated/{filename}.py", 'w', encoding='utf-8') as file:
            file.write(generated)

        self.__add(f'generated/{filename}.py')
        print(filename)
        return filename

    # Fuzzy Logic
    def fuzzy_generate(self,
            f: str, question: str, antecedents: dict,
            consequents: dict, rule_definitions: list, links: list
    ):
        filename = f
        if filename == '':
            filename = 'fl' + str(self.__hash__())

        # Заголовок файла
        lines = [
            "import numpy as np",
            "import skfuzzy as fuzz",
            "from skfuzzy import control as ctrl",
            ""]
        for i in links:
            lines += [f"from {i} import {i}"]

        lines += [f"def {filename}():",
                  f"    print('{question}')",


                  
                  ""
                  # Определение лингвистических переменных
                  ]
        for i in antecedents.keys():
            lines += [f"    {i} = float(input('Введите значение {i}'))"]

        # Создаём Antecedent
        for var, spec in antecedents.items():
            start, end, step = spec['range']
            lines.append(f"    {var}X = ctrl.Antecedent(np.arange({start}, {end}+1, {step}), '{var}')")
            for term, (mf, params) in spec['terms'].items():
                lines.append(f"    {var}X['{term}'] = fuzz.{mf}({var}X.universe, {params})")
        # Создаём Consequent
        out_var = list(consequents.keys())[0]
        for var, spec in consequents.items():
            start, end, step = spec['range']
            lines.append(f"    {var}X = ctrl.Consequent(np.arange({start}, {end}+1, {step}), '{var}')")
            for term, (mf, params) in spec['terms'].items():
                lines.append(f"    {var}X['{term}'] = fuzz.{mf}({var}X.universe, {params})")
        # Правила
        lines.append("    rules = []")
        for rd in rule_definitions:
            cond_terms = rd['if']
            logic = rd['logic']
            cond_expr = f" {'& ' if logic == 'AND' else ' | '}".join([
                f"{var}X['{term}']" for var, term in cond_terms
            ])
            out_t = rd['then'][1]
            lines.append(f"    rules.append(ctrl.Rule({cond_expr}, {out_var}X['{out_t}']))")
        # Сборка и инференс
        lines += ["    ",
            "    system = ctrl.ControlSystem(rules)",
            "    sim = ctrl.ControlSystemSimulation(system)",
        ]
        # Вывод данных
        for var in antecedents.keys():
            lines.append(f"    sim.input['{var}'] = {var}")
        lines += [
            "    sim.compute()",
            "    # Получение результата",
            f"    # Дефаззификация для выходной переменной '{out_var}'",
            f"    {out_var}_index = float(sim.output['{out_var}'])",
            f"    memberships = {{",
            f"        label: float(fuzz.interp_membership(",
            f"            {out_var}X.universe, {out_var}X[label].mf, {out_var}_index",
            f"        ))",
            f"        for label in {out_var}X.terms.keys()",
            f"    }}",
            f"    {out_var}_category = max(memberships, key=memberships.get)"]
        tmpint = 0
        for _, spec in consequents.items():
            for i,_ in spec['terms'].items():

                try:
                    lines += [f"    ",
                              f"    if {out_var}_category == '{i}':",
                              f"        {links[tmpint]}()"]

                except Exception as e:
                    print(e)
                    break
                tmpint += 1
        lines += [

            "    return {" ,
            f"        '{out_var}_index': {out_var}_index,",
            f"        '{out_var}_category': {out_var}_category",
            "    }"
        ]
        # Запись в файл
        with open(f"generated/{filename}.py", 'w', encoding='utf-8') as file:
            file.write("\n".join(lines))

        self.__add(f'generated/{filename}.py')
        print(filename)
        return filename

    def starter_generate(self, f:str, linka:str):
        filename = f
        if filename == '':
            filename = "s" + str(self.__hash__())
        generated = ''
        generated +=f'''
from {linka} import {linka}
if __name__ == '__main__':
    print("Starting...")
    {linka}()'''
        with open(f"generated/{filename}.py", 'w', encoding='utf-8') as file:
            file.write(generated)

        self.__add(filename)
        print(filename)
        return filename

    def ender_generate(self, f:str, output:str):
        filename = f
        if filename == '':
            filename = "e" + str(self.__hash__())
        generated = ''
        generated +=f'''
def {filename}():
    print("{output}")
    return "Result" + "{output}"'''
        with open(f"generated/{filename}.py", 'w', encoding='utf-8') as file:
            file.write(generated)

        self.__add(filename)
        print(filename)
        return filename








