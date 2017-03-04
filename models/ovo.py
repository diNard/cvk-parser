from pony.orm import *


class Ovo(db.Entity):
    id = PrimaryKey(int, unsigned=True)
    url = Required(str, 256)
    region_id = Required(int, index=True, unsigned=True)

    peoples_count = Optional(int, unsigned=True)
    stations_count = Optional(int, unsigned=True)

    post_address = Optional(LongStr)
    bounds_desc = Required(LongStr)
    center_desc = Required(str, 256)
    place = Optional(str, 256)
    phones = Optional(str, 256)
    faxes = Optional(str, 256)

    processed = Required(bool, default=False)
    processed_update = Required(bool, default=False)

    def get_stations_url(self):
        return self.url.replace("WP024", "WP029")
