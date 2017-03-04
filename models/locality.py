from pony.orm import *


class Locality(db.Entity):
    id = PrimaryKey(int, auto=True, unsigned=True)
    name = Required(str, index=True)
    abbreviations = Optional(str, 4)
    parent_id = Optional(int, unsigned=True)
    number = Optional(int, unsigned=True)
    """
    1 - 'Область'
    2 - 'Район'
    3 - 'Місто обласного значення'
    4 - 'Місто'
    5 - 'Селище міского типу'
    6 - 'Село'
    """
    type = Required(int, size=8)

    table_type_values = {
        1: 'обл',
        2: 'р-н',
        3: 'м',
        4: 'м',
        5: 'смт',
        6: 'с',
    }

    REGION = 1
    DISTRICT = 2
    CITY_OF_REGION = 3
    CITY = 4
    URBAN_VILLAGE = 5
    VILLAGE = 6
