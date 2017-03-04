from . import Parser
from models.region import Region
from models.locality import Locality
from pony.orm import db_session, select


class RegionParser(Parser):
    CVK_HTTP_PREFIX = 'http://www.cvk.gov.ua/pls/vnd2014/'

    """
    http://www.cvk.gov.ua/pls/vnd2014/wp030?PT001F01=910

    Second table

    <tr>
    <td width="40%" align="center" class=td1>Назва регіону України</td>
    <td width="15%" align="center" class=td1>Номери округів</td>
    <td width="15%" align="center" class=td1>Кількість округів</td>
    <td width="15%" align="center" class=td1>Орієнтовна кількість виборців</td>
    <td width="15%" align="center" class=td1>Кількість виборчих дільниць</td>

    From second row

    <tr>
    <td class=td2><a class=a1 HREF="WP023?PT001F01=910&PID100=5">
        Вінницька область</A></td>
    <td align="center" class=td3>11-18</td>
    <td align="center" class=td2>8</td>
    <td align="center" class=td3>1274948</td>
    <td align="center" class=td2>1660</td>

    """

    @db_session
    def _parse(self):
        for tds in self.tr_tds(1, from_index=1):
            a__name = tds[0].select('.//a')[0]
            name = a__name.text().replace(" область", "").replace("м.", "")

            # if names is eq and type is region or city of region value
            region = select(c for c in Locality if c.name == name and (c.type == 1 or c.type == 3)).first()
            if region and not Region.get(id = region.id):
                Region(
                    id = region.id,
                    url = self.CVK_HTTP_PREFIX + a__name.attr('href'),
                    ovos_count = int(tds[2].text()),
                    peoples_count = int(tds[3].text()),
                    stations_count = int(tds[4].text())
                )
