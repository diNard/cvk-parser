class CityCorrector:
    CORRECTIONS = {
        10043	: lambda x: x.replace("Берегове", "м.Берегове"),
        10243	: lambda x: x.replace("Добролюбовка", "с.Добролюбовка"),
        260285	: lambda x: x + ',с.Голинь',
        320852	: lambda x: x.replace("Довгалівське", "с.Довгалівське"),
        461607	: lambda x: x + ',с.Бердихів',
        531171	: lambda x: x + ',м.Полтава',
        631690	: lambda x: x + ',м.Харків',
        631691	: lambda x: x + ',м.Харків',
        680623	: lambda x: x.replace("вул.Криворудка", "с.Криворудка"),
        711102	: lambda x: x.replace("смт Катеринопіль", "смт Катеринопіль,")
    }

    def __init__(self, parser):
        self._parser = parser

    def correct(self, address, id):
        # prevent error "12 м. Київ", where missing comma
        for city_type in self._parser.CITY_TYPES:
            address = address.replace(" %s." % city_type, ", %s." %city_type)

        if id in self.CORRECTIONS:
            address = self.CORRECTIONS[id](address)
        return address
