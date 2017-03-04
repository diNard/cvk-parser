from . import Parser
from pony.orm import db_session


class OvoUpdateParser(Parser):

    """
    http://www.cvk.gov.ua/pls/vnd2014/WP024?PT001F01=910&PID100=18&PF7331=64

    First table
    From first row

    <tr>
    <td width="50%" class=td10>Центр</td>
    <td width="50%" class=td2>місто Коростень</td>
    <tr>
    <td class=td10>Опис меж</td>
    <td class=td2>місто Коростень, Коростенський, Олевський райони</td>
    <tr>
    <td class=td10>Поштова адреса ОВК</td>
    <td class=td2>11500, м. Коростень, вул. Грушевського, 3</td>
    <tr>
    <td class=td10>Контактні телефони</td>
    <td class=td2>(04142) 96-0-92, 96-0-97, 96-0-94</td>
    <tr>
    <td  class=td10>Кількість виборчих дільниць</td>
    <td  class=td2><b>306</b></td>
    <tr>
    <td  class=td10>Орієнтовна кількість виборців</td>
    <td  class=td2><b>     164 049</b></td>

    """

    @db_session
    def _parse(self):
        self.ovo = self.param('ovo')
        if not self.ovo.processed_update:
            for tds in self.tr_tds(0):
                label = tds[0].text()
                value = tds[1].text()

                if label == "Центр":
                    self.ovo.center_desc = value
                elif label == "Опис меж":
                    self.ovo.bounds_desc = value
                elif label == "Поштова адреса ОВК":
                    self.ovo.post_address = value
                elif label == "Місцезнаходження ОВК":
                    self.ovo.place = value
                elif label == "Контактні телефони":
                    self.ovo.phones = value
                elif label == "Факси":
                    self.ovo.faxes = value

            self.ovo.processed_update = True
