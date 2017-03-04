from pony.orm import *


class StationDirty(db.Entity):
    id = PrimaryKey(int, unsigned=True)
    address = Required(LongStr)
    bound = Required(LongStr)
