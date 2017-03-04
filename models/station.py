from pony.orm import *


class Station(db.Entity):
    id = PrimaryKey(int, unsigned=True)
    ovo_id = Required(int, unsigned=True, index=True)
    post_index = Optional(str, 8)

    region = Optional(str, 64)
    region_id = Optional(int, unsigned=True, index=True)

    district = Optional(str, 64)
    district_id = Optional(int, unsigned=True)

    city_type = Optional(str, 8)
    city_name = Optional(str, 64)
    city_id = Optional(int, unsigned=True, index=True)

    street_name = Optional(str, 64, index=True)
    street_type = Optional(str, 16)
    number = Optional(str, 8, index=True)

    place = Optional(str, 256)

    processed = Required(bool, default=False)
    processed_address = Required(bool, default=False)
