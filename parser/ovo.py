from . import Parser
from models.ovo import Ovo
from pony.orm import db_session, select


class OvoParser(Parser):
    CVK_HTTP_PREFIX = 'http://www.cvk.gov.ua/pls/vnd2014/'

    """
    http://www.cvk.gov.ua/pls/vnd2014/WP023?PT001F01=910&PID100=18

    Second table

    <tr>
    <td width="10%" align="center" class=td1>ОВО</td>
    <td width="10%" align="center" class=td1>Орієнтовна<br>
        кількість<br>виборців</td>
    <td width="10%" align="center" class=td1>Кількість<br>
        виборчих<br>дільниць</td>
    <td width="70%" align="center" class=td1>Опис меж</td>

    From second row

    <tr>
    <td align="center" class=td3>
        <A class=a1 HREF="WP024?PT001F01=910&PID100=18&PF7331=62">ОВО №62</A>
        </td>
    <td align="center" class=td2>171843</td>
    <td align="center" class=td3>105</td>
    <td  class=td2>Центр: місто Житомир<br>ОВО включає: частина Богунського
        району (виборчі дільниці № 181338 –181372, 181382 – 181386, 181388,
        181389, 181399 – 181403), Корольовський район  міста Житомира</td>

    """

    @db_session
    def _parse(self):
        self.region = self.param('region')

        for tds in self.tr_tds(1, from_index=1):
            a__number = tds[0].select('.//a')[0]
            id = int(a__number.text().replace("ОВО №", ""))

            if not Ovo.get(id = id):
                Ovo(
                    id = id,
                    url = self.CVK_HTTP_PREFIX + a__number.attr('href'),
                    region_id = self.region.id,

                    peoples_count = int(tds[1].text()),
                    stations_count = int(tds[2].text()),

                    bounds_desc = "-",
                    center_desc = "-"
                )

        self.region.processed = True
