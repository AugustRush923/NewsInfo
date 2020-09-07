import ast


def db_index_class(index):
    if index == 0:
        return "first"
    elif index == 1:
        return "second"
    elif index == 2:
        return "third"
    else:
        return ""


def to_dict(tup):
    str_tup = tup.__str__()
    new_str = str_tup.replace("(", "{").replace(")", "}").replace(",", ":")
    dic = ast.literal_eval(new_str)
    return dic
