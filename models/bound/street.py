from pony.orm import *


class Street(db.Entity):
    id = PrimaryKey(int, auto=True)
    type = Optional(str, 16)
    name = Required(str, 256, index=True)
    locality_id = Optional(int, unsigned=True)
    station_id = Required(int, unsigned=True)
    city_id = Optional(int, unsigned=True)

    type_name = "street"
