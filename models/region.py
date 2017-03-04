from pony.orm import *


class Region(db.Entity):
    id = PrimaryKey(int, unsigned=True) # same as locality_id
    url = Required(str, 256)

    ovos_count = Optional(int, unsigned=True)
    peoples_count = Optional(int, unsigned=True)
    stations_count = Optional(int, unsigned=True)

    processed = Required(bool, default=False)
