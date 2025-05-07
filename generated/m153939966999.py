
def m153939966999():
    print("Вам нравится еда в ресторане?")
    b = input("['Да', 'Нет']")
    match b.split():

                
        case ["Да"]:
            print("Да")
                
        case ["Нет"]:
            print("Нет")
        case _:
            print("default")