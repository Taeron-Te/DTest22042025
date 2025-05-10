from typing import Dict

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


def evaluate_engine_health(oil_pressure: float,
                           coolant_temp: float,
                           vibration_level: float) -> dict:

    # 1. Определяем лингвистические входные переменные
    oil = ctrl.Antecedent(np.arange(0, 101, 1), 'oil_pressure')
    temp = ctrl.Antecedent(np.arange(60, 121, 1), 'coolant_temp')
    vib = ctrl.Antecedent(np.arange(0, 11, 1), 'vibration_level')

    # 2. Определяем лингвистическую выходную переменную
    health = ctrl.Consequent(np.arange(0, 101, 1), 'engine_health')

    # 3. Определяем функции принадлежности для каждой переменной

    # Давление масла: низкое / нормальное / высокое
    oil['low'] = fuzz.trapmf(oil.universe, [0, 0, 30, 50])
    oil['normal'] = fuzz.trimf(oil.universe, [40, 60, 80])
    oil['high'] = fuzz.trapmf(oil.universe, [70, 90, 100, 100])

    # Температура ОЖ: низкая / нормальная / высокая
    temp['low'] = fuzz.trapmf(temp.universe, [60, 60, 70, 80])
    temp['normal'] = fuzz.trimf(temp.universe, [75, 90, 105])
    temp['high'] = fuzz.trapmf(temp.universe, [100, 110, 120, 120])

    # Уровень вибраций: низкий / средний / высокий
    vib['low'] = fuzz.trimf(vib.universe, [0, 2, 4])
    vib['medium'] = fuzz.trimf(vib.universe, [3, 5, 7])
    vib['high'] = fuzz.trimf(vib.universe, [6, 8, 10])

    # Состояние двигателя: критическое / предупреждение / нормальное
    health['Critical'] = fuzz.trimf(health.universe, [0, 0, 50])
    health['Warning'] = fuzz.trimf(health.universe, [30, 50, 70])
    health['Good'] = fuzz.trimf(health.universe, [50, 100, 100])

    # 4. Формулируем правила экспертной системы

    rules = [
        # Критические сочетания
        ctrl.Rule(oil['low'] | temp['high'] | vib['high'], health['Critical']),
        # Предупреждающие сочетания
        ctrl.Rule(oil['normal'] & temp['high'], health['Warning']),
        ctrl.Rule(oil['low'] & temp['normal'], health['Warning']),
        ctrl.Rule(vib['medium'] & temp['normal'], health['Warning']),
        # Хорошие сочетания
        ctrl.Rule(oil['normal'] & temp['normal'] & vib['low'], health['Good']),
        ctrl.Rule(oil['high'] & temp['normal'] & vib['low'], health['Good']),
    ]

    # 5. Собираем систему и создаём симулятор
    engine_ctrl = ctrl.ControlSystem(rules)
    engine_sim = ctrl.ControlSystemSimulation(engine_ctrl)

    # 6. Передаём конкретные значения и выполняем инференс
    engine_sim.input['oil_pressure'] = oil_pressure
    engine_sim.input['coolant_temp'] = coolant_temp
    engine_sim.input['vibration_level'] = vibration_level
    engine_sim.compute()

    # 7. Получаем результат
    health_index = float(engine_sim.output['engine_health'])
    # Определяем категорию по наибольшему значению степени принадлежности
    memberships = {
        label: float(fuzz.interp_membership(health.universe,
                                            health[label].mf,
                                            health_index))
        for label in health.terms.keys()
    }
    health_category = max(memberships, key=memberships.get)

    return {
        'health_index': health_index,
        'health_category': health_category
    }


# Пример использования:
if __name__ == "__main__":
    result = evaluate_engine_health(oil_pressure=60,
                                    coolant_temp=90,
                                    vibration_level=1)
    print(f"Индекс здоровья: {result['health_index']:.1f}")
    print(f"Категория: {result['health_category']}")

def a_random_three_pos_fl(name, inplings: Dict, mfs , rules):

    gendata = {
        'x': [0, 101, 1],
        'y': [60, 121, 1],
        'z': [0, 11, 1]
               }
    gendata = inplings
    alpha = ctrl.Antecedent(np.arange(gendata['x'][0], gendata['x'][1], gendata['x'][2]), 'alpha_mode') # abstract: ctrl.Antecedent(np.arange({x1}, {x2}, {x3}), '{x_name}')
    beta = ctrl.Antecedent(np.arange(gendata['y'][0], gendata['y'][1], gendata['y'][2]), 'beta_mode') # abstract: ctrl.Antecedent(np.arange({y1}, {y2}, {y3}), '{y_name}')
    gamma = ctrl.Antecedent(np.arange(gendata['z'][0], gendata['z'][1], gendata['z'][2]), 'gamma_mode') # abstract: ctrl.Antecedent(np.arange({z1}, {z2}, {z3}), '{z_name}')

    out = ctrl.Antecedent(np.arange(0, 101, 1), 'output_mode')

    localmfs = {
        'x':
            {
            'low': [0, 0, 30, 50],
            'normal': [40, 60, 60, 80],
            'high': [70, 90, 100, 100]
             },
        'y':
            {
                'low': [60, 60, 70, 80],
                'normal': [75, 90, 90, 105],
                'high': [100, 110, 120, 120]
            },
        'z':
            {
                'low': [0,2,2,4],
                'normal': [3,5,5,7],
                'high': [6,8,8,10]
            }
    }

    alpha['low'] = fuzz.trapmf(alpha.universe, localmfs['x']['low']) # трапецеидальная функция принадлежности ... Тримф - треугольная abcd - начало подъема, начало плато, конец плато, конец спада
    alpha['normal'] = fuzz.trapmf(alpha.universe, localmfs['x']['normal'])
    alpha['high'] = fuzz.trapmf(alpha.universe, localmfs['x']['high'])

    beta['low'] = fuzz.trapmf(beta.universe, localmfs['y']['low'])
    beta['normal'] = fuzz.trapmf(beta.universe, localmfs['y']['normal'])
    beta['high'] = fuzz.trapmf(beta.universe, localmfs['y']['high'])

    gamma['low'] = fuzz.trapmf(gamma.universe, localmfs['y']['low'])
    gamma['normal'] = fuzz.trapmf(gamma.universe, localmfs['y']['normal'])
    gamma['high'] = fuzz.trapmf(gamma.universe, localmfs['y']['high'])

    out['first'] = fuzz.trapmf(out.universe, [0,0,0,50])
    out['second'] = fuzz.trapmf(out.universe, [30, 50, 50, 70])
    out['third'] = fuzz.trapmf(out.universe, [50, 100, 100, 100])

    ruledict = {
        'alpha': ["alpha['low']", "alpha['normal']", "alpha['high']"],
        'beta': ["beta['low']","beta['normal']","beta['high']"],
        'gamma': ["gamma['low']", "gamma['normal']", "gamma['high']"],
        'answer': ["out['first']", "out['second']", "out['third']"]
        
    }
    rules = exec(f"""
        [
        ctrl.Rule({ruledict['alpha'][0]} or {ruledict['beta'][2]} or {ruledict['gamma'][2]}, {ruledict['answer'][0]} ),
        
        ctrl.Rule( {ruledict['alpha'][1]}  &  {ruledict['beta'][2]} ,  {ruledict['answer'][1]} ),
        ctrl.Rule( {ruledict['alpha'][0]}  &  {ruledict['beta'][1]} ,  {ruledict['answer'][1]} ),
        ctrl.Rule( {ruledict['gamma'][1]}  &  {ruledict['beta'][1]} , {ruledict['answer'][1]} ),
        
        ctrl.Rule( {ruledict['alpha'][1]}  &  {ruledict['beta'][1]}  &  {ruledict['gamma'][0]} ,  {ruledict['answer'][2]} )
        ctrl.Rule( {ruledict['alpha'][2]}  &  {ruledict['beta'][1]}  &  {ruledict['gamma'][0]} ,
                   {ruledict['answer'][2]} )

    ]
    """)

