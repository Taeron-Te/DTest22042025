import json
from code_generator import Code_generator

def reader(filename:str):
    block_from_file: dict
    connection_from_file: dict
    with open(f"{filename}", "r", encoding="utf-8") as file:
        tmp = json.load(file)
        block_from_file = tmp['blocks']
        connection_from_file = tmp['connections']

    block_connections={}
    for i in block_from_file:
        block_connections[i['id']] = []
        for j in connection_from_file:
            if i['id'] == j['from']:
                block_connections[i['id']].append(j['to'])

    creater(block_from_file, block_connections)

def creater(bff:dict, bc:dict):
    c = Code_generator()
    # li : list
    for i in bff:
        # if i['type'] == 'Match' or i['type'] == 'Fuzzy':
        #     li = bc[i['id']]
        #     li.reverse()
        # pass
        match i['type']:
            case 'Starter':
                c.starter_generate(i['id'], bc[i['id']][0] ) #i['question']
            case 'Ender':
                c.ender_generate(i['id'], i['verdict'])
            case 'Binares':
                c.primitive_generate(i['condition'],i['id'], bc[i['id']][1], bc[i['id']][0])
            case 'Match':
                c.match_generate(i['question'], i['choices'], bc[i['id']], i['id'])
            case 'Fuzzy':
                c.fuzzy_generate(i['id'], i['question'],
                                 i['fuzzy_config']['antecedents'],
                                 i['fuzzy_config']['consequent'],
                                 i['fuzzy_config']['rule_definitions'],
                                 bc[i['id']])
            case _:
                print("def")