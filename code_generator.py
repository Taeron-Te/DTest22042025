from typing import Any, Tuple
import ast
from dto.Operands import Operand, OperandType


class Code_generator:
    code_was_gendered = 0
    generated_file_names = []

    def __init__(self):
        pass


    def __call__(self, *args, **kwargs):
        self.primitive_generate(input("Text"), input("q"), input("o"), input("f"))

    def _add(self, fn):
        Code_generator.code_was_gendered += 1
        Code_generator.generated_file_names.append(fn)

    def get_generated_files(self):
        print(self.generated_file_names)
        for j, i in enumerate(self.generated_file_names):
            print(j, i)
        return self.generated_file_names

    def get_file_by_name(self, t):
        tmp = []
        for i in self.generated_file_names:
            if i == t:
                print(i)
                tmp.append(i)
        return tmp

    def primitive_generate(self, txt, q, o, f='', linka='', linkb='' ):
        filename = f
        if filename == 'LAST' and Code_generator.generated_file_names != []:
            filename = Code_generator.generated_file_names.pop()
        if filename == '':
            filename = 'f' + str(self.__hash__())
        generated = ""
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

    def match_generate(self, txt, q: list,  lincs: list[str], deflinc: str, f=''):
        filename = f
        if filename == '':
            filename = 'm' + str(self.__hash__())
        generated = ''
        if not isinstance(q, list):
            print("IS NOT LIST", q)
            self.primitive_generate(txt, q, "==", filename)
        if deflinc == '':
            deflinc = "#"
        for i in q:
            pass
        else:
            generated = f'''
def {filename}():
    print("{txt}")
    b = input("{q}")
    match b.split():
'''
            for i,j in q, lincs:
                generated += f'''
                
        case ["{i}"]:
            {j}()
            print("{i}")'''

            generated += f'''
        case _:
            {deflinc}()
            print("default")'''

        with open(f"generated/{filename}.py", 'w', encoding='utf-8') as file:
            file.write(generated)

        self._add(f'generated/{filename}.py')
        print(filename)
        return filename

    def generate_fuzzy_system_file(self,
            filename: str,
            system_name: str,
            antecedents: dict,
            consequents: dict,
            rule_definitions: list
    ) -> None:
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
            "",
            f"def evaluate_{system_name}({', '.join(antecedents.keys())}):",
            "    \"\"\"",
            "    Экспертная система на нечёткой логике",
            "    \"\"\"",
            # Определение лингвистических переменных
        ]
        # Создаём Antecedent
        for var, spec in antecedents.items():
            start, end, step = spec['range']
            lines.append(f"    {var} = ctrl.Antecedent(np.arange({start}, {end}+1, {step}), '{var}')")
            for term, (mf, params) in spec['terms'].items():
                lines.append(f"    {var}['{term}'] = fuzz.{mf}({var}.universe, {params})")
        # Создаём Consequent
        for var, spec in consequents.items():
            start, end, step = spec['range']
            lines.append(f"    {var} = ctrl.Consequent(np.arange({start}, {end}+1, {step}), '{var}')")
            for term, (mf, params) in spec['terms'].items():
                lines.append(f"    {var}['{term}'] = fuzz.{mf}({var}.universe, {params})")
        # Правила
        lines.append("    rules = []")
        for rd in rule_definitions:
            cond_terms = rd['if']
            logic = rd['logic']
            cond_expr = f" {'& ' if logic == 'and' else ' | '}".join([
                f"{var}['{term}']" for var, term in cond_terms
            ])
            out_var, out_term = rd['then']
            lines.append(f"    rules.append(ctrl.Rule({cond_expr}, {out_var}['{out_term}']))")
        # Сборка и инференс
        lines += [
            "    system = ctrl.ControlSystem(rules)",
            "    sim = ctrl.ControlSystemSimulation(system)",
        ]
        # Ввод данных
        for var in antecedents.keys():
            lines.append(f"    sim.input['{var}'] = {var}")
        lines += [
            "    sim.compute()",
            "    # Получение результата",
            f"    result = sim.output",
            f"    return result",
        ]
        # Запись в файл
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

    def starter(self, filename:str, linka:str):
        f = filename
        if f == '':
            f = "starter" + str(self.__hash__())



