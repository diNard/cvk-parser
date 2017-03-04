from . import Parser
from models.station_dirty import StationDirty
from models.ovo import Ovo
from models.locality import Locality
from pony.orm import db_session, select
from .corrector.district import DistrictCorrector
from .corrector.city import CityCorrector
from .corrector.street import StreetCorrector
import re


class AddressParser(Parser):
    STREET_TYPES = ['вул', 'пров', 'в/ч', "в'їзд", "проїзд", 'заїзд', "роз'їзд",
                    'пл', 'шосе', 'просп', 'узв', 'км', 'кв-л', 'майдан', 'туп',
                    'спуск', 'набережна', 'присілок', 'будка', 'мкр-н', 'бульв',
                    'завулок', 'урочище', 'лінія', 'алея', 'ж/м', 'острів',
                    'бухта']
    CITY_TYPES = ['с', 'м', 'смт', 'с-ще', 'х']
    REGION_TYPES = ['обл.', 'область']
    DISTRICT_TYPES = ['р-н', 'район']

    @db_session
    def _parse(self):
        self.station = self.param('station')
        if not self.station.processed_address:
            self.dirty = StationDirty.get(id = self.station.id)
            self.ovo = Ovo.get(id = self.station.ovo_id)
            if self.dirty and self.ovo:
                self._parse_address()
                self._save_address()
                self.station.processed_address = True

    def _parse_address(self):
        """
        селищний будинок культури №1, хол,вул.Жовтнева, 62, смт Покровське,
        Покровський р-н, Дніпропетровська обл., 53600

        => [
            "селищний будинок культури №1",
            "хол",
            "вул.Жовтнева",
            "62",
            "смт Покровське",
            "Покровський р-н",
            "Дніпропетровська обл.",
            "53600"
        ]
        """
        address_nodes = CityCorrector(self).correct(
                            self.dirty.address, self.station.id).split(',')

        place_max_node_index = len(address_nodes)

        # if True then check if we can grab node to station.number
        need_check_number = False

        for i, address_node in enumerate(address_nodes):
            address_node = address_node.strip()
            # "вул.Жовтнева" => ("вул", "Жовтнева")
            # or "Жовтнева вул." => ("вул", "Жовтнева")
            _type, name = AddressParser.get_type_and_name(address_node)

            if need_check_number:
                need_check_number = False
                # contains > 40% digits
                if AddressParser.is_number(name):
                    self.station.number = name
                    place_max_node_index = min(place_max_node_index, i)
                    continue

            # contains 100% digits
            if AddressParser.represents_int(address_node) > 1000:
                self.station.post_index = address_node

            elif _type in self.STREET_TYPES:
                self.station.street_type = _type
                self.station.street_name = name
                need_check_number = True
                place_max_node_index = min(place_max_node_index, i)

            elif _type in self.CITY_TYPES:
                self.station.city_type = _type
                self.station.city_name = name
                place_max_node_index = min(place_max_node_index, i)

            elif name in self.REGION_TYPES:
                self.station.region = _type
                place_max_node_index = min(place_max_node_index, i)

            elif name in self.DISTRICT_TYPES:
                self.station.district = _type
                place_max_node_index = min(place_max_node_index, i)

        self.station.place = ",".join(address_nodes[0: place_max_node_index])

    def _save_address(self):
        # Save region
        name, id = AddressParser.get_name_and_id(Locality.REGION,
                                                 self.station.region)
        if not id and self.ovo.region_id:
            name, id = "", self.ovo.region_id
        self.station.region = name
        self.station.region_id = id

        # Save distcirt
        # filter by region: may be few districts with eq names
        # print("A:",self.station.district)
        name, id = AddressParser.get_name_and_id(Locality.DISTRICT,
                                        self.station.district,
                                        self.station.region_id)
        if id is None:
            name = DistrictCorrector.correct(name)
            if name != self.station.district:
                name, id = AddressParser.get_name_and_id(Locality.DISTRICT,
                                                    name,
                                                    self.station.region_id)
        self.station.district = name
        self.station.district_id = id

        # Save city
        self.station.city_id = AddressParser.get_city_id(self.station.city_name,
                                         self.station.region_id,
                                         self.station.district_id)
        if self.station.city_id is not None:
            self.station.city_type = ""
            self.station.city_name = ""

    @classmethod
    def get_type_and_name(cls, address_node):
        address_node = StreetCorrector.correct_full_str(address_node)

        _type, name = "", address_node
        # split by " " and "."
        nodes = re.split('\.| ', address_node)
        if len(nodes) > 1:
            _p_type = nodes[0].strip()
            _type = cls._get_type(_p_type)
            # "<type>.Київ"
            name = address_node[len(nodes[0]) + 1:]

            if not((_type in cls.STREET_TYPES) or (_type in cls.CITY_TYPES)):
                # check if type after name, example "Полтавки бульв."
                name_with_type = cls._get_type(name)
                if _type and (name_with_type in cls.STREET_TYPES \
                                or name_with_type in cls.CITY_TYPES):
                    _type, name = name_with_type, _p_type
        return _type, name

    @classmethod
    def _get_type(cls, _type):
        _type = _type.lower()
        return StreetCorrector.correct_type(_type)

    @classmethod
    def get_city_id(cls, city_name, region_id, district_id):
        city_id = None
        pids = (id for id in (region_id, district_id) if id)

        if city_name:
            city = select(p for p in Locality
                                    if p.name.upper() == cls.filter_name(city_name)
                                    and p.type > Locality.DISTRICT
                                    and (
                                        (p.parent_id in pids)
                                        or (p.type == Locality.CITY_OF_REGION)
                                    )).first()
            if city:
                city_id = city.id
            elif district_id is None:
                # if district id missed
                district_id = cls.find_district_id_in_region_by_city_name(
                    region_id, city_name
                )
                if district_id:
                    city_id = cls.get_city_id(city_name, region_id, district_id)

        return city_id

    @classmethod
    def find_district_id_in_region_by_city_name(cls, region_id, city_name):
        district_id = None

        # get possible district ids
        parent_ids_for_cities_that_name = select(p.parent_id for p in Locality
                                if p.name.upper() == cls.filter_name(city_name)
                                and p.type > Locality.DISTRICT)
        # get districts with ids and this region as parent
        district = select(p for p in Locality
                                    if p.id in parent_ids_for_cities_that_name
                                    and p.parent_id == region_id).first()
        if district:
            district_id = district.id
        return district_id

    @classmethod
    def get_name_and_id(cls, _type, name, parent_id = None):
        id = None
        if name:
            # print("B:", name)
            localities = list(select(c for c in Locality if c.type == _type
                                        and c.name.upper() == cls.filter_name(name)))

            if _type == Locality.DISTRICT:
                # print(name, len(localities))
                pass

            if parent_id:
                localities = [l for l in localities if l.parent_id == parent_id]
            if len(localities):
                name, id = "", localities[0].id
        return name, id

    @classmethod
    def filter_name(cls, name):
        return name.replace("’", "'").upper()

    @classmethod
    def is_number(cls, string):
        count = sum(1 for char in string if char.isdigit())
        return count > 0.4 * len(string)

    @classmethod
    def represents_int(cls, string):
        try:
            num = int(string)
            return num
        except ValueError:
            return False
