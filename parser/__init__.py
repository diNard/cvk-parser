from grab import Grab


class Parser:
    def __init__(self, url, **kwargs):
        self.g = Grab()
        self.url = url
        self._params = kwargs

    def parse(self):
        if self.url is not None:
            self.g.go(self.url)
            self._tables = self.g.doc.select('//table[@class="t2"]')
        self._parse()

    def tr_tds(self, index, **params):
        from_index = params.get('from_index', 0)
        trs = self.table(index).select('.//tr')[from_index:]
        for tr in trs:
            yield tr.select('.//td')

    def table(self, index):
        return self._tables[index]

    def param(self, name):
        obj = self._params[name]
        if obj:
            return obj
        else:
            raise ValueError("Init method missing 1 required keyword argument: '%s'" % name)
