from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtSql import *
BUY = 0
SELL = 1

class curBar():
    def __init__(self, date, high, low):
        self.date = date
        self.high = high
        self.low = low

class tester():
    def __init__(self,
                 balance,       # {currency1:ammount1,...,currencyN:ammountN}                       - текущий баланс
                 listbars,      # [[curBar1, balance1],...,[curBarN, balanceN]]                         - список баров
                 listorders,    # {date1:[{'type':BUY/SELL, 'currency':currency, 'percent':percent}..{'type':BUY/SELL, 'currency':currency, 'percent':percent}]} - список приказов на покупку/продажу
                 ):
        self.balance = balance
        self.listbars = listbars
        self.listorders = listorders
        self.calculate()

    def calculate(self):
        for cb in self.listbars:    # проходим по списку баров
            v = self.listorders.get(cb[0].date) # ищем в словаре приказов по ключу-дате
            if v:   # если нашли
                for order in v: # проходим по списку приказов за эту дату
                    curs = order['currency'].split('_')
                    cur1 = curs[0]  #   первая валюта
                    cur2 = curs[1]  #   вторая валюта
                    cur1ammount = self.balance.get(cur1)    # сумма первой валюты на балансе
                    if not cur1ammount:
                        cur1ammount = 0                     # если валюты не найдено, то = 0
                    cur2ammount = self.balance.get(cur2)    # сумма второй валюты на балансе
                    if not cur2ammount:
                        cur2ammount = 0                     # если валюты не найдено, то = 0
                    if order['type'] == BUY:
                        cur1trade = cur1ammount * order['percent'] / 100
                        #cur2trade = cur1trade / cb[0].high                      # худший случай
                        #cur2trade = cur1trade / ((cb[0].high + cb[0].low) / 2)  # средний случай
                        cur2trade = cur1trade / cb[0].low                       # лучший случай
                        self.balance.update({cur1: cur1ammount - cur1trade, cur2: cur2ammount + cur2trade})
                    elif order['type'] == SELL:
                        cur2trade = cur2ammount * order['percent'] / 100
                        #cur1trade = cur2trade * cb[0].low                      # худший случай
                        #cur1trade = cur2trade * ((cb[0].high + cb[0].low) / 2)  # средний случай
                        cur1trade = cur2trade * cb[0].high                       # лучший случай
                        self.balance.update({cur1: cur1ammount + cur1trade, cur2: cur2ammount - cur2trade})
            cb[1] = self.balance

class testerWindow(object):
    def __init__(self, db):
        self.db = db

    def setupUi(self, Form):
        Form.resize(640, 480)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        Form.setMinimumSize(QSize(640, 480))
        Form.setMaximumSize(QSize(640, 480))

        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        #Form.setStyleSheet('background-color: rgb(128, 176, 215)')

        self.dateEdit = QDateEdit(Form)
        self.dateEdit.setSizePolicy(sizePolicy)
        font = QFont()
        font.setFamily("Tahoma")
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        self.dateEdit.setFont(font)
        self.dateEdit.setAlignment(Qt.AlignCenter)
        self.dateEdit.setCalendarPopup(True)
        self.gridLayout.addWidget(self.dateEdit, 0, 0, 1, 1)
        self.dateEdit.setObjectName("dateEdit")

        self.pushButton = QPushButton(Form)
        self.gridLayout.addWidget(self.pushButton, 1, 0, 1, 1)
        self.pushButton.setObjectName("pushButton")
        self.pushButton.setText('П У С К !!!')
        self.pushButton.clicked.connect(lambda : self.pushButton_clicked())

        self.textEdit = QTextEdit()
        self.gridLayout.addWidget(self.textEdit, 2, 0, 1, 1)
        self.textEdit.setObjectName("textEdit")


    def pushButton_clicked(self):
        q1 = QSqlQuery(self.db)
        q2 = QSqlQuery(self.db)
        q1.prepare("SELECT curname FROM curpair WHERE curname LIKE 'USDT_%' ORDER BY curname")
        q1.exec_()
        rang = {}
        rangkeys = []
        self.textEdit.clear()
        while q1.next():
            curpair = q1.value(0)  #curname
            curs = curpair.split('_')
            percent = 50            # процент от остатка, которым торгуем (процентом)
            balance = {curs[0]: 1000, curs[1]: 0}   # начальный балланс - 1000 единиц первой валюты
            listbars = []
            listorders = {}
            q2.prepare("SELECT date, high, low, uprank, downrank FROM chardata7200 WHERE curname = :curname AND date >= :date ORDER BY date ASC")
            q2.bindValue(":curname", curpair)
            date1 = self.dateEdit.dateTime()
            QDateTime.setTimeZone(date1, QTimeZone(0))
            q2.bindValue(":date", QDateTime.toSecsSinceEpoch(date1))
            q2.exec_()
            while q2.next():
                cb = curBar(q2.value(0), q2.value(1), q2.value(2)) # date, high, low
                listbars.append([cb, {}])

                # if random.random() < 0.1:
                #     listorders.update({q2.value(0): [{'type': BUY, 'currency': curpair, 'percent': percent}]})
                # if random.random() > 0.9:
                #     listorders.update({q2.value(0): [{'type': SELL, 'currency': curpair, 'percent': percent}]})
                if q2.value(4) >= 1 and q2.value(3) == 0: # downrank >=  & uprank == 0
                    listorders.update({q2.value(0):[{'type':BUY, 'currency':curpair, 'percent':percent}]})
                elif q2.value(3) >= 1 and q2.value(4) == 0: # uprank >=  & downrank == 0
                    listorders.update({q2.value(0): [{'type': SELL, 'currency': curpair, 'percent': percent}]})
                lasthigh = q2.value(1)
                lastlow = q2.value(2)
            tst = tester(balance, listbars, listorders)

            fullbalance = tst.balance['USDT'] + tst.balance[curs[1]] * (lasthigh + lastlow) / 2
            rang.update({fullbalance: curpair})
            rangkeys.append(fullbalance)

        rangkeys.sort()
        for i in rangkeys:
            self.textEdit.append(str(rang[i])+' : '+str(i))




