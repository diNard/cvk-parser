@db_session
def _parse(self):
    self.ovo = self.param('ovo')

    for tds in self.tr_tds(1, slice=1):
        id = int(tds[0].text())

        if Station.get(id = id):
            continue

        address_str = self._clear_html(cells[1].html())
        bound = cells[2].text()

        address = self.parse_address(address_str)
        bounds = self.parse_bound(bound, address)

        region_id, district_id  = self.save_address(id, address)
        self.save_dirty(id, address_str, bound)
        self.save_bounds(id, bounds, region_id, district_id, id)

        self.print_data(id, address, bounds)

    self.ovo.processed = True

def _clear_html(self, text):
    return text.replace('<td class="td2">', '').replace("</td>\n", '').replace('<br>', ',')

def parse_address(self, address):
    items = address.split(',')

    street_types = ['просп', 'бульв', 'пл', 'пров', 'вул', 'острів', "роз'їзд", 'будка', 'тупик', "майдан"]
    city_types = ['с', 'м', 'смт', 'с-ще']
    region_types = ["обл.", "р-н", "район", "область"]

    street, city = ["", ""], ["", ""]
    number, post_index = "", ""
    region, district = "", ""
    pos = [len(items)]

    for k, a in enumerate(items):
        add = self.get_type_and_name(a)

        if add[0] in street_types:
            street = add
            if len(items) > k + 1:
                _, number =  self.get_type_and_name(items[k + 1])
                if not self.has_numbers(number):
                    number = "" # items[k + 1]
            pos.append(k)
        elif add[0] in city_types:
            city = add
            pos.append(k)
        elif add[1] in region_types:
            if add[1] == region_types[0]:
                region = add[0].strip()
            else:
                district = add[0].strip()
            pos.append(k)

    if self.represents_int(items[-1].strip()) > 1000:
        post_index = items[-1].strip()

    return {
        "post_index": post_index,
        "region": region,
        "district": district,
        "city": city,
        "street": street,
        "number": number.strip(),
        "place": ",".join(items[0: min(pos)]),
        "comment": ""
    }

@db_session
def save_address(self, id, address):
    region = self._get_locality_set(1, address["region"])
    district = self._get_locality_set(2, address["district"])

    if not region[1] and self.ovo.region_id:
        region = region[0], self.ovo.region_id

    city_id = self._get_city_id(address["city"][1], district[1], region[1])
    if city_id is not None:
        address["city"] = "", ""

    Station(
        id = id,
        ovo_id = self.ovo.id,
        post_index = address["post_index"],

        region = region[0],
        region_id = region[1],

        district = district[0],
        district_id = district[1],

        city_type = address["city"][0],
        city_name = address["city"][1],
        city_id = city_id,

        street_type = address["street"][0],
        street_name = address["street"][1],
        number = address["number"],

        place = address["place"],
        comment = address["comment"]
    )
    return region[1], district[1]

@db_session
def save_dirty(self, id, address, bound):
    DirtyStation(
        id = id,
        address = address,
        bound = bound,
    )

def _get_locality_set(self, _type, name):
    locality_name = name
    locality_id = None
    if locality_name:
        locality = select(c for c in Locality if c.type == _type
                                    and c.name == self._format_city_name(name)).first()
        if locality:
            locality_id = locality.id
            locality_name = ""
    return locality_name, locality_id

def _format_city_name(self, name):
    return name.replace("’", "'")

def _get_city_id(self, city_name, district_id, region_id):
    city_id = None
    if city_name:
        city = select(p for p in Locality if p.name == self._format_city_name(city_name)
                                    and (
                                        (
                                            p.type > 2
                                            and (p.parent_id == district_id) or (p.parent_id == region_id)
                                        )
                                        or (p.type == 3)
                                    )
                      ).first()
        if city:
            city_id = city.id
    return city_id

def parse_bound(self, text, address):
    suffix = ""
    if text[-1] != ';':
        suffix = ';'

    # 0 - city, 1 - street, 2 - number
    level = 0
    last = 0

    changes = [
        {"–": 1},
        {":": 1, ";": -1},
        {";": -1}
    ]
    errors = [[":"], ["–"], ["–", ":"]]

    result = []
    link = result

    for node in re.finditer(r' – |,|;|:', text + suffix):
        node_text = text[node.start(): node.end()].strip()
        tp, name, error = [""] * 3

        if level in [0, 1]:
            tp, name = self.get_type_and_name(text[last:node.start()])
            children = []

            if tp in ['с', 'м', 'смт', 'с-ще']:
                if level == 1:
                    level, link = self.change_level(level, -1 * level, result)
            elif level == 0:
                # save all if single
                if text == text[last:node.start()]:
                    name = text

                address["comment"] = name

                tp, name = address["city"]
                children = [
                    [ address["street"][0], address["street"][1], [address["number"]] ]
                ]

            link.append([tp, name, children])
        else:
            tp = text[last:node.start()].strip()
            link.append(tp)

        if node_text in errors[level]:
            error = "Incorrect, %s, %s" % (level, node_text)

        #print("%s: %s %s %s" % (level, tp, name, error))

        if node_text in changes[level]:
            level, link = self.change_level(level, changes[level][node_text], result)

        last = node.end()
    return result


def save_bounds(self, id, bounds, region_id, district_id, station_id):
    for city in bounds:
        id, city_id = self._save_bound_city(city, region_id, district_id, station_id)
        for street in city[2]:
            bs_id = self._save_bound_street(street, id, city_id)
            for number in street[2]:
                self._save_bound_number(number, bs_id)

@db_session
def _save_bound_city(self, city, region_id, district_id, station_id):
    city_id = self._get_city_id(city[1], district_id, region_id)
    if city_id is not None:
        city[0] = ""
        city[1] = ""

    bc = BoundCity(
        type = city[0],
        name = city[1],
        city_id = city_id,
        station_id = station_id
    )
    commit()
    return bc.id, bc.city_id

@db_session
def _save_bound_street(self, street, bound_city_id, city_id):
    bs = BoundStreet(
        type = street[0][:16],
        name = street[1],
        city_id = city_id,
        bound_city_id = bound_city_id
    )
    commit()
    return bs.id

@db_session
def _save_bound_number(self, name, bound_street_id):
    items = name.split('–')
    start, end = items[0], items[0]
    if len(items) > 1:
        end = items[1]

    BoundNumber(
        start = start[:8],
        end = end[:8],
        bound_street_id = bound_street_id
    )

def change_level(self, level, diff, result):
    level += diff
    link = result
    for _ in range(0, level):
        link = link[-1][2]
    return level, link

def get_type_and_name(self, text):
    text = text.strip()
    tp, name = self._tp(text, ".")
    if tp is None:
        tp, name = self._tp(text, " ")
        if tp is None:
            tp, name = "", text
    return tp.strip(), name.strip()

def _tp(self, text, delimiter):
    items = text.split(delimiter)
    if len(items) > 1 and len(items[1]) > 0:
        tp = items[0]
        name = delimiter.join(items[1:])
        return tp, name
    return None, None

def print_data(self, id, address, bounds):
    print(id, "-----------------------------")
    print(address['post_index'], address["region"], address["district"])
    print(address['city'][0], address['city'][1])
    print(address['street'][0], address['street'][1], address['number'])
    print(address['place'])
    for city in bounds:
        print(city[0], city[1])
        for street in city[2]:
            numbers = ""
            if len(street[2]) > 0:
                numbers = " :: " + ", ".join(street[2])
            print(" ", street[0], street[1], numbers)

def represents_int(self, s):
    try:
        a = int(s)
        return a
    except ValueError:
        return False

def has_numbers(self, text):
    return any(char.isdigit() for char in text)


#db.generate_mapping()
