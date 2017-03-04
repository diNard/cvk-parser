from . import Parser
from models.station import Station
from models.station_dirty import StationDirty
from pony.orm import db_session, select


class StationParser(Parser):
    """
    http://www.cvk.gov.ua/pls/vnd2014/WP029?PT001F01=910&PID100=18&pf7331=64

    Second table

    <tr>
    <td width="10%" align="center" class=td1>№  дільниці</td>
    <td width="30%" align="center" class=td1>Місцезнаходження та адреса
        приміщення для голосування</td>
    <td width="50%" align="center" class=td1>Опис меж</td>

    From second row

    <tr>
    <td align="center" class=td3><b>180363</b></td>
    <td  class=td2>сільрада, фойє<br>вул.Козака, 1, с.Берестовець, Коростенський
        р-н, Житомирська обл., 11532</td>
    <td  class=td2>с.Берестовець</td>

    """

    @db_session
    def _parse(self):
        self.ovo = self.param('ovo')

        for tds in self.tr_tds(1, from_index=1):
            id = int(tds[0].text())

            if not Station.get(id = id):
                StationDirty(
                    id = id,
                    address = StationParser.clear_html(tds[1].html()),
                    bound = tds[2].text(),
                )

                Station(
                    id = id,
                    ovo_id = self.ovo.id
                )

        self.ovo.processed = True

    @classmethod
    def clear_html(cls, text):
        return text.replace('<td class="td2">', '').replace("</td>\n", '').replace('<br>', ',')
