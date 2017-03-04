from pony.orm import *


class Number(db.Entity):
    id = PrimaryKey(int, auto=True)
    start = Required(str, 8)
    end = Optional(str, 8)
    street_id = Required(int, unsigned=True)

    type_name = "number"
