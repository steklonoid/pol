import time
from PyQt6.QtCore import *
from privatPolonix import Poloniex

class ThreadReturnCurrencies(QThread):
    def __init__(self, f):
        QThread.__init__(self)
        self.f = f

    def run(self):
        self.f.q['Normal'].put({'command':'returnCurrencies', 'parameters':{}}, True)
        time.sleep(300)


class ThreadReturnTicker(QThread):
    def __init__(self, f):
        QThread.__init__(self)
        self.f = f

    def run(self):
        self.f.q['Normal'].put({'command':'returnTicker','parameters':{}}, True)
        time.sleep(2)

class ThreadReturnChartData(QThread):
    def __init__(self, f):
        QThread.__init__(self)
        self.f = f

    def run(self):
        for i in self.f.tickers.keys():
            item = self.f.model1.findItems(i, flags=Qt.MatchExactly, column=0)
            if item:
                tick = item[0].text()
                lt = QDateTime.fromString(self.f.model1.item(item[0].row(), 1).text(), 'dd.MM.yyyy HH:mm')
                QDateTime.setTimeZone(lt, QTimeZone(0))
                lastcharupdate = str(QDateTime.toSecsSinceEpoch(lt))
                self.f.q['Normal'].put({'command': 'returnChartData',
                                        'parameters': {'currencyPair': tick, 'start': lastcharupdate,
                                                       'period': '7200', 'resolution': 'auto'}}, True)
        time.sleep(1.5)

class ThreadLoadQueue(QThread):
    queueProcessed = pyqtSignal()
    def __init__(self, f):
        QThread.__init__(self)
        self.f = f

    def run(self):
        elq = ''
        mypolo = Poloniex(self.f.ak, self.f.ask)
        if not self.f.q['High'].empty():
            elq = self.f.q['High'].get(True)
        elif not self.f.q['Normal'].empty():
            elq = self.f.q['Normal'].get(True)
        elif not self.f.q['Low'].empty():
            elq = self.f.q['Low'].get(True)

        if elq:
            streval = 'mypolo.' + elq['command']+'('
            flfirst = True
            for k in elq['parameters'].keys():
                if not flfirst:
                    streval += ','
                else:
                    flfirst = False
                streval += k + '=' + "'" + elq['parameters'][k] + "'"
            streval += ')'
            print(streval)
            res = eval(streval)
            self.f.res = (elq, res)
            self.queueProcessed.emit()