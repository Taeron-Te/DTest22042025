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
                                    vibration_level=0)
    print(f"Индекс здоровья: {result['health_index']:.1f}")
    print(f"Категория: {result['health_category']}")