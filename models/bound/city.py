from pony.orm import *


class City(db.Entity):
    id = PrimaryKey(int, auto=True)
    type = Optional(str, 8)
    name = Optional(str, 64)
    locality_id = Optional(int, unsigned=True)
    station_id = Required(int, unsigned=True)

    type_name = "city"
