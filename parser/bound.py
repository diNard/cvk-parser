from . import Parser
from .address import AddressParser
from models.station_dirty import StationDirty
from models.bound.city import City
from models.bound.street import Street
from models.bound.number import Number
from pony.orm import db_session, select, commit
import re


class BoundParser(Parser):
    @db_session
    def _parse(self):
        self.station = self.param('station')
        if not self.station.processed:
            self.dirty = StationDirty.get(id = self.station.id)
            if self.dirty:
                self._parse_bounds()
                self.station.processed = True

    def _parse_bounds(self):
        bounds_text = self.dirty.bound
        if bounds_text[-1] != ';':
            bounds_text += ';'

        parents = {"city": None, "street": None}
        process_number = False
        last = 0

        for node in re.finditer(r' – |,|;|:', bounds_text):
            node_delimiter = bounds_text[node.start(): node.end()].strip()
            node_text = bounds_text[last:node.start()].strip()
            if len(node_text):
                bound = self._process_node(parents, node_text, process_number)
                if bound is not None:
                    active_type = bound.__class__.__name__.lower()

                    if active_type in ['city', 'street']:
                        parents[active_type] = bound
                        if active_type == 'city':
                            parents['street'] = None

                    if process_number and (active_type != 'number' \
                                            or node_delimiter == ';'):
                        process_number = False

                    if node_delimiter == ":":
                        if active_type == 'street':
                            process_number = True
                        else:
                            error = "Incorrect: type = %s, del = %s, id = %u, %u:%u" % \
                                (active_type, node_delimiter, self.station.id,\
                                node.start(), node.end()
                            )
                            print(error.encode('utf8'))
            last = node.end()

    def _process_node(self, parents, node_text, process_number, help_type = None):
        _type, name = AddressParser.get_type_and_name(node_text)

        bound = self._process_city_and_street(parents, _type, name)
        if bound is None:
            # "вул.Пушкіна/Лермонтова", for "Лермонтова" should be help type
            if help_type:
                bound = self._process_city_and_street(parents, help_type, name)
            elif process_number:
                bound = self._process_number(parents, node_text)

        if bound is None:
            bound = self._process_street(parents, "", node_text)

        commit()
        return bound

    def _process_city_and_street(self, parents, _type, name):
        bound = None
        if _type in AddressParser.CITY_TYPES:
            bound = self._process_city(_type, name)
        elif _type in AddressParser.STREET_TYPES:
            bound = self._process_street(parents, _type, name)
        return bound

    def _process_city(self, _type, name):
        city_id = AddressParser.get_city_id(name,
                                            self.station.district_id,
                                            self.station.region_id)
        if city_id:
            _type, name = "", ""

        return City(
            type = _type,
            name = name,
            locality_id = city_id,
            station_id = self.station.id
        )

    def _process_street(self, parents, _type, name):
        bound = None

        # check if "вул.Барановського/вул.Чкалова"
        if _type and ('/' in name):
            nodes = name.split('/')
            name = nodes[0].strip()
            if not AddressParser.represents_int(name):
                # we pass _type for "вул.Барановсього/Чкалова", then Чкалова
                # will be street type
                bound = self._process_node(parents, '/'.join(nodes[1:]), False, _type)

        city_id = None
        if parents['city']:
            city_id = parents['city'].id

        if name:
            _bound = Street(
                type = _type,
                name = name[:256],

                locality_id = self.station.city_id,
                station_id = self.station.id,
                city_id = city_id
            )
            if bound is None:
                bound = _bound
        return bound

    def _process_number(self, parents, node_text):
        # if prev item was'nt street
        if not parents['street']:
            return None

        items = node_text.split('–')
        start, end = items[0], ''
        if len(items) > 1:
            end = items[1]

        return Number(
            start = start[:8],
            end = end[:8],
            street_id = parents['street'].id
        )
