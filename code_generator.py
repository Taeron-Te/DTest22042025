from typing import Any, Tuple
import ast



class Code_generator:
    code_was_gendered = 0
    generated_file_names = []

    def __init__(self):
        pass

    # Добавление нового элемента в общий пул
    def _add(self, fn):
        Code_generator.code_was_gendered += 1
        Code_generator.generated_file_names.append(fn)
    # Получаем элементы из общего пула

    def get_generated_files(self):
        print(self.generated_file_names)
        for j, i in enumerate(self.generated_file_names):
            print(j, i)
        return self.generated_file_names

    # Получаем все файлы содержащие t в названии
    def get_file_by_name(self, t):
        tmp = []
        for i in self.generated_file_names:
            if i == t:
                print(i)
                tmp.append(i)
        return tmp

    # Бинарный блок
    def primitive_generate(self, txt, q, o, f='', linka='', linkb='' ):
        filename = f
        if filename == 'LAST' and Code_generator.generated_file_names != []:
            filename = Code_generator.generated_file_names.pop()
        if filename == '':
            filename = 'f' + str(self.__hash__())
        generated = ''
        if linka == '':
            linka = "#"
        else:
            generated += f'''
from generated.{linka} import {linka}
'''
        if linkb == '':
            linkb = "#"
        else:
            generated += f'''
from generated.{linkb} import {linkb}
'''

        generated += f'''
def {filename}():
    print("{txt}")
    b = input()
    if "{q}" {o} b:
        {linka}()
        return True
    else:
        {linkb}() 
        return False       
'''
        with open(f"generated/{filename}.py", 'w', encoding='utf-8') as file:
            file.write(generated)

        self._add(filename)
        print(filename)
        return filename
    # Не бинарный блок выбора
    def match_generate(self, txt, q: list,  lincs: list[str], deflinc: str, f=''):
        # Генерация имени
        filename = f
        if filename == '':
            filename = 'm' + str(self.__hash__())
        generated = ''
        # Защита от дурака
        if not isinstance(q, list):
            print("IS NOT LIST", q)
            self.primitive_generate(txt, q, "==", filename)
        # Замена отсутствующей дефолт ссылки (
        if deflinc == '':
            deflinc = "#"
        else:
            generated += f"""
from {deflinc} import {deflinc}"""
        # Импорт ссылок
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
            generated += f'''
            print("{i}")
            '''

            generated += f'''
        case _:
            {deflinc}()
            print("default")'''
        # Запись файла
        with open(f"generated/{filename}.py", 'w', encoding='utf-8') as file:
            file.write(generated)

        self._add(f'generated/{filename}.py')
        print(filename)
        return filename

    # Нечеткая логика мать ее
    def generate_fuzzy_system_file(self,
            filename: str,
            antecedents: dict,
            consequents: dict,
            rule_definitions: list,
            links: list
    ):
        f = filename
        if f == '':
            f = 'fl' + str(self.__hash__())
          # - filename: путь к выходному .py файлу
          # - system_name: имя системы (будет использовано в имени функции)
          # - antecedents: словарь входных переменных вида:
          #       {
          #         'var_name': {
          #             'range': [start, end, step],
          #             'terms': {
          #                 'term_name': ['trimf' | 'trapmf', params_list],
          #                 ...
          #             }
          #         },
          #         ...
          #       }
          # - consequents: аналогично antecedents для выходных переменных
          # - rule_definitions: список определений правил вида:
          #       [
          #         {
          #           'if': [('var', 'term'), ...],
          #           'logic': 'and' | 'or',
          #           'then': ('out_var', 'out_term')
          #         },
          #         ...
          #       ]
        # Заголовок файла
        lines = [
            "import numpy as np",
            "import skfuzzy as fuzz",
            "from skfuzzy import control as ctrl",
            ""]
        for i in links:
            lines += [f"from {i} import {i}"]
        lines += [f"def evaluate_{filename}Z({':float, '.join(antecedents.keys())}):",
            "    \"\"\"",
            "    Экспертная система на нечёткой логике",
            "    \"\"\"",
            # Определение лингвистических переменных
        ]
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
            cond_expr = f" {'& ' if logic == 'and' else ' | '}".join([
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
        for _, spec in consequents.items():
            for i,_ in spec['terms'].items():
                tmpint = 0
                try:
                    lines += [f"    ",
                              f"    if {out_var}_categoty == {i}:",
                              f"        {links[tmpint]}()"]
                except Exception as e:
                    print(e)
                    break
        lines += [

            "    return {" ,
            f"        '{out_var}_index': {out_var}_index,",
            f"        '{out_var}_category': {out_var}_category",
            "    }"
        ]
        # Запись в файл
        with open(f"generated/{f}.py", 'w', encoding='utf-8') as file:
            file.write("\n".join(lines))

    def starter(self, filename:str, linka:str):
        f = filename
        if f == '':
            f = "starter" + str(self.__hash__())





