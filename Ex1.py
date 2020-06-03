import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtSql import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from mainWindow import Ui_MainWindow
from dateEnter import Ui_Form
from tester import testerWindow
from trader import traderWindow
from datetime import datetime
from DownloadingFromSite import ThreadReturnCurrencies, ThreadReturnTicker, ThreadReturnCompleteBalances, ThreadLoadQueue, ThreadReturnChartData, ThreadReturnOrderBook
import pyqtgraph as pg
import queue
import time
import numpy as np

INTERVAL = 0.2

class MainWindow(QMainWindow, Ui_MainWindow):
    # файл настроек
    settings = QSettings("./config.ini", QSettings.IniFormat)

    dateEnter = ""
    flagOnline = 0
    flagPrivate = 0
    # очередь задач
    q = {'High':queue.Queue(0), 'Normal':queue.Queue(10), 'Low':queue.Queue(10)}
    # результатоприемник
    res = ()

    qb_red = QBrush()
    qb_red.setColor(QColor(255, 212, 212))
    qb_red.setStyle(Qt.SolidPattern)
    qb_green = QBrush()
    qb_green.setColor(QColor(212, 255, 212))
    qb_green.setStyle(Qt.SolidPattern)
    qb_gold = QBrush()
    qb_gold.setColor(QColor(249, 166, 2))
    qb_gold.setStyle(Qt.SolidPattern)
    qb_white = QBrush()
    qb_white.setColor(QColor(255, 255, 255))
    qb_white.setStyle(Qt.SolidPattern)

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        #  подключаем базу SQLite
        self.db = QSqlDatabase.addDatabase("QSQLITE", 'maindb')

        # модель для отображения валютных пар
        self.model1 = QStandardItemModel()
        model1proxy = QSortFilterProxyModel()
        model1proxy.setSourceModel(self.model1)
        self.tableView1.setModel(model1proxy)
        self.model1.setColumnCount(7)
        self.model1.setHorizontalHeaderLabels(['Пара', ' посл. Бар', 'Цена', '% за 24 ч', 'Объем', 'Купить', 'Продать'])

        # модель для отображения баланса
        self.model2 = QStandardItemModel()
        self.model2.setColumnCount(4)
        self.model2.setHorizontalHeaderLabels(['Валюта', 'Свободно', 'В ордерах', 'Всего USD'])
        self.tableView2.setModel(self.model2)

        # модель для отображения открытых ордеров
        model3 = QStandardItemModel()
        model3.setColumnCount(4)
        model3.setHorizontalHeaderLabels(['Валюта', 'Свободно', 'В ордерах', 'USD'])
        self.tableView3.setModel(model3)

        # модель для отображения стакана цен
        self.modelAsks = QStandardItemModel()
        self.modelAsks.setColumnCount(2)
        self.modelBids = QStandardItemModel()
        self.modelBids.setColumnCount(2)

        # потоки для загрузки данных с сайта
        self.th_ThreadReturnCurrencies = ThreadReturnCurrencies(self)
        self.th_ThreadReturnCurrencies.finished.connect(self.finished_ThreadReturnCurrencies)
        self.th_ThreadReturnTicker = ThreadReturnTicker(self)
        self.th_ThreadReturnTicker.finished.connect(self.finished_ThreadReturnTicker)
        self.th_ThreadReturnCompleteBalances = ThreadReturnCompleteBalances(self)
        self.th_ThreadReturnCompleteBalances.finished.connect(self.finished_ThreadReturnCompleteBalances)
        self.th_ThreadReturnChartData = ThreadReturnChartData(self)
        self.th_ThreadReturnChartData.finished.connect(self.finished_ThreadReturnChartData)
        self.th_ThreadReturnOrderBook = ThreadReturnOrderBook(self)
        self.th_ThreadReturnOrderBook.finished.connect(self.finished_ThreadReturnOrderBook)
        self.thq = ThreadLoadQueue(self)
        self.thq.finished.connect(self.finished_thq)
        self.thq.queueProcessed.connect(self.queueProcessed_thq)

        # дмалог трейдер
        self.qw = QDialog(self)
        self.qw.finished.connect(self.traderDialogFinished)
        self.qw.setModal(True)
        tw = traderWindow()
        tw.setupUi(self.qw)
        tw.twAsks.setModel(self.modelAsks)
        tw.twAsks.setColumnWidth(1, 140)
        tw.twBids.setModel(self.modelBids)
        tw.twBids.setColumnWidth(1, 140)
        # показываем главное окно
        self.show()

    def __del__(self):
        if self.db.isOpen():
            self.db.close()

# ============================= threading ====================================
    @pyqtSlot()
    def finished_ThreadReturnCurrencies(self):
        if self.flagOnline == 1 and not self.qw.isVisible():
            self.th_ThreadReturnCurrencies.start()
    @pyqtSlot()
    def finished_ThreadReturnTicker(self):
        if self.flagOnline == 1 and not self.qw.isVisible():
            self.th_ThreadReturnTicker.start()
    @pyqtSlot()
    def finished_ThreadReturnCompleteBalances(self):
        if self.flagOnline == 1 and self.flagPrivate == 1 and not self.qw.isVisible():
            self.th_ThreadReturnCompleteBalances.start()
    @pyqtSlot()
    def finished_ThreadReturnChartData(self):
        if self.flagOnline == 1 and not self.qw.isVisible():
            self.th_ThreadReturnChartData.start()
    @pyqtSlot()
    def finished_ThreadReturnOrderBook(self):
        if self.flagOnline == 1 and self.qw.isVisible():
            self.th_ThreadReturnOrderBook.start()
    @pyqtSlot()
    def finished_thq(self):
        if self.flagOnline == 1:
            self.thq.start()
            self.thq.ak = self.ak
            self.thq.ask = self.ask

    def load_returnCurrencies_thq(self, currencies):
        q1 = QSqlQuery(self.db)
        q1.prepare("BEGIN TRANSACTION")
        q1.exec_()
        for currency in currencies:
            q1.prepare(
                'INSERT OR IGNORE INTO currency (name, fullname, humanType, currencyType) VALUES (:name, :fullname, :humanType, :currencyType)')
            q1.bindValue(":name", currency)
            q1.bindValue(":fullname", currencies[currency]['name'])
            q1.bindValue(":humanType", currencies[currency]['humanType'])
            q1.bindValue(":currencyType", currencies[currency]['currencyType'])
            q1.exec_()
            q1.prepare(
                'UPDATE currency SET txFee = :txFee, minConf = :minConf, disabled = :disabled, delisted = :delisted, frozen = :frozen WHERE name = :name')
            q1.bindValue(":name", currency)
            q1.bindValue(":txFee", currencies[currency]['txFee'])
            q1.bindValue(":minConf", currencies[currency]['minConf'])
            q1.bindValue(":disabled", currencies[currency]['disabled'])
            q1.bindValue(":delisted", currencies[currency]['delisted'])
            q1.bindValue(":frozen", currencies[currency]['frozen'])
            q1.exec_()
        q1.prepare("COMMIT")
        q1.exec_()

    def load_returnTicker_thq(self, ticker):
        def updatemodel1(iloc):
            self.model1.item(iloc, 2).setData(float(ticker[tick]['last']), Qt.DisplayRole)
            pchange = float(ticker[tick]['percentChange'])
            if pchange >= 0:
                self.model1.item(iloc, 3).setBackground(self.qb_green)
            else:
                self.model1.item(iloc, 3).setBackground(self.qb_red)
            self.model1.item(iloc, 3).setData(round(pchange * 100, 2), Qt.DisplayRole)
            self.model1.item(iloc, 4).setData(float(ticker[tick]['baseVolume']), Qt.DisplayRole)
            if self.flagPrivate == 1:
                c1c2 = tick.split("_")
                item = self.model2.findItems(c1c2[0], flags=Qt.MatchExactly, column=0)
                lastprice = float(ticker[tick]['last'])
                if lastprice == 0:
                    return
                if item:
                    self.model1.item(iloc, 5).setBackground(self.qb_green)
                    self.model1.item(iloc, 5).setFont(QFont("Times", 7))
                    ambase = self.model2.item(item[0].row(), 1).text()
                    amsec = str(round(float(ambase) / lastprice, 2))
                    self.model1.item(iloc, 5).setText(amsec + ' ' + c1c2[1] + ' за' + '\n' + ambase + ' ' + self.model2.item(item[0].row(), 0).text())
                else:
                    self.model1.item(iloc, 5).setBackground(self.qb_white)
                    self.model1.item(iloc, 5).setText('')
                item = self.model2.findItems(c1c2[1], flags=Qt.MatchExactly, column=0)
                if item:
                    self.model1.item(iloc, 6).setBackground(self.qb_green)
                    self.model1.item(iloc, 6).setFont(QFont("Times", 7))
                    amsec = self.model2.item(item[0].row(), 1).text()
                    ambase = str(round(float(amsec) * lastprice, 2))
                    self.model1.item(iloc, 6).setText(amsec + ' ' + self.model2.item(item[0].row(), 0).text() + ' за' + '\n' + ambase + ' ' + c1c2[0])
                else:
                    self.model1.item(iloc, 6).setBackground(self.qb_white)
                    self.model1.item(iloc, 6).setText('')
        for tick in ticker:
            item = self.model1.findItems(tick, flags=Qt.MatchExactly, column=0)
            if not item:
                print(tick)
                self.model1.appendRow(
                    [QStandardItem(tick), QStandardItem('0'), QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem(),
                     QStandardItem()])
                updatemodel1(self.model1.rowCount() - 1)
                q1 = QSqlQuery(self.db)
                q1.prepare('INSERT OR IGNORE INTO curpair (curname, lastchartime) VALUES (:curname, :date)')
                q1.bindValue(':curname', tick)
                q1.bindValue(':date', 0)
                q1.exec_()
            else:
                updatemodel1(item[0].row())

    def load_returnCompleteBalances_thq(self, balances):
        def updatemodel2(iloc):
            self.model2.item(iloc, 1).setText(balances[balance]['available'])
            self.model2.item(iloc, 2).setText(balances[balance]['onOrders'])
            if balance == 'USDT':
                self.model2.item(iloc, 3).setText(str(round(float(balances[balance]['available']), 2)))
            else:
                row = self.model1.findItems('USDT_' + balance)[0].row()
                m1 = float(balances[balance]['available'])
                m2 = float(self.model1.item(row, 2).text())
                self.model2.item(iloc, 3).setText(str(round(m1 * m2, 2)))
        for balance in balances:
            if float(balances[balance]['available']) == 0:
                continue
            item = self.model2.findItems(balance, flags=Qt.MatchExactly, column=0)
            if not item:
                self.model2.appendRow([QStandardItem(balance), QStandardItem(), QStandardItem(), QStandardItem()])
                updatemodel2(self.model2.rowCount() - 1)
            else:
                updatemodel2(item[0].row())

    def load_returnChartData_thq(self, curname, lastcharupdate, chartdata):
        q1 = QSqlQuery(self.db)
        q1.prepare("BEGIN TRANSACTION")
        q1.exec_()
        maxchardate = 0
        for chart in chartdata[:-1]:
            q1.prepare(
                "INSERT OR IGNORE INTO chardata7200 (curname, date, high, low, volume, quoteVolume) "
                "VALUES (:curname, :date, :high, :low, :volume, :quoteVolume)")
            q1.bindValue(":curname", curname)
            q1.bindValue(":date", int(chart['date']))
            q1.bindValue(":high", float(chart['high']))
            q1.bindValue(":low", float(chart['low']))
            q1.bindValue(":volume", float(chart['volume']))
            q1.bindValue(":quoteVolume", float(chart['quoteVolume']))
            q1.exec_()
            maxchardate = max(int(lastcharupdate), int(chart['date']))

        q1.prepare("UPDATE curpair SET lastchartime = :lastchartime WHERE curname = :curname")
        q1.bindValue(":lastchartime", str(maxchardate))
        q1.bindValue(":curname", curname)
        q1.exec_()
        item = self.model1.findItems(curname, flags=Qt.MatchExactly, column=0)[0]
        self.model1.item(item.row(), 1).setText(QDateTime.toString(QDateTime.fromSecsSinceEpoch(maxchardate, QTimeZone(0)), 'dd.MM.yyyy HH:mm'))
        q1.prepare("COMMIT")
        q1.exec_()

    def load_returnOrderBook(self, orderbook):
        self.modelAsks.removeRows(0, self.modelAsks.rowCount())
        self.modelBids.removeRows(0, self.modelBids.rowCount())

        for order in orderbook['asks']:
            self.modelAsks.appendRow([QStandardItem(order[0]), QStandardItem(str(order[1]))])
        for order in orderbook['bids']:
            self.modelBids.appendRow([QStandardItem(order[0]), QStandardItem(str(order[1]))])
        print(self.q['Normal'].qsize())
    @pyqtSlot()
    def queueProcessed_thq(self):
        command = self.res[0]['command']
        data = self.res[1]
        if command == 'returnCurrencies':
            self.load_returnCurrencies_thq(data)
        elif command == 'returnTicker':
            self.load_returnTicker_thq(data)
        elif command == 'returnCompleteBalances':
            self.load_returnCompleteBalances_thq(data)
        elif command == 'returnChartData':
            curname = self.res[0]['parameters']['currencyPair']
            lastcharupdate = self.res[0]['parameters']['start']
            self.load_returnChartData_thq(curname, lastcharupdate, data)
            self.updateTableView()
        elif command == 'returnOrderBook':
            self.load_returnOrderBook(data)

# =============== меню Файл ====================================================
    @pyqtSlot()
    def trig_menuopendb(self):
        fname = self.settings.value("dbpath", "")
        fname = QFileDialog.getOpenFileName(self, "Выберите файл базы", fname, "*.db file (*.db)")[0]
        if fname:
            self.db.setDatabaseName(fname)
            self.db.open()
            if not self.db.isOpen():
                msgBox = QMessageBox()
                msgBox.setText("Ошибка открытия файла базы данных")
                msgBox.exec()
                return
            if not self.db.tables():
                msgBox = QMessageBox()
                msgBox.setText("У файла базы данных неправильная структура")
                msgBox.exec()
                return
            self.settings.setValue("dbpath", fname)

            q1 = QSqlQuery(self.db)
            q1.prepare("SELECT value FROM parameters WHERE name='API_KEY'")
            q1.exec_()
            q1.next()
            self.ak = q1.value(0)
            q1.prepare("SELECT value FROM parameters WHERE name='API_SECRET'")
            q1.exec_()
            q1.next()
            self.ask = q1.value(0)
            #=======================================================
            fav = []
            q1.prepare('SELECT curname FROM curpairfav ORDER BY curname ASC')
            q1.exec_()
            while q1.next():
                fav.append(q1.value(0))

            cb1 = []
            q1.prepare('SELECT * FROM curpair ORDER BY curname ASC')
            q1.exec_()
            while q1.next():
                curs = q1.value(0).split('_')
                if not curs[0] in cb1:
                    cb1.append(curs[0])
                self.model1.appendRow([QStandardItem(q1.value(0)),
                                       QStandardItem(QDateTime.toString(QDateTime.fromSecsSinceEpoch(q1.value(1), QTimeZone(0)), 'dd.MM.yyyy HH:mm')),
                                       QStandardItem(),
                                       QStandardItem(),
                                       QStandardItem(),
                                       QStandardItem(),
                                       QStandardItem()])
                if q1.value(0) in fav:
                    self.model1.item(self.model1.rowCount() - 1, 0).setBackground(self.qb_gold)
                    self.model1.item(self.model1.rowCount() - 1, 0).setData('1', 3)
                else:
                    self.model1.item(self.model1.rowCount() - 1, 0).setData('0', 3)
            for cur in cb1:
                self.comboBox1.addItem(cur)
            self.comboBox1.addItem('избранное')
            self.comboBox1.addItem('все')
            self.comboBox1_currentIndexChanged()
            self.updateTableView()

    @pyqtSlot()
    def trig_menucreatedb(self):
        fname = self.settings.value("dbpath", "")
        fname = QFileDialog.getSaveFileName(self, "Выберите файл базы", fname, "db files (*.db)")[0]
        if fname:
            if not os.path.isfile(fname):
                self.db.setDatabaseName(fname)
                self.db.open()
                q1 = QSqlQuery()
                q1.prepare(
                    "CREATE TABLE 'chardata7200' ('idchardata' INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 'curname' TEXT NOT NULL, 'date' INTEGER NOT NULL,"
                    " 'high' REAL NOT NULL, 'low' REAL NOT NULL, 'volume' REAL NOT NULL, 'quoteVolume' REAL NOT NULL, 'uprank' INTEGER NOT NULL DEFAULT 0, 'downrank' INTEGER NOT NULL DEFAULT 0)")
                q1.exec_()
                q1.prepare(
                    "CREATE TABLE 'curpair' ('curname' TEXT NOT NULL UNIQUE, 'lastchartime' INTEGER NOT NULL DEFAULT 0, 'last'	REAL, PRIMARY KEY('curname'))")
                q1.exec_()
                q1.prepare(
                    "CREATE TABLE 'currency' ('name' TEXT NOT NULL UNIQUE, 'fullname' TEXT,	'humanType'	TEXT, 'currencyType' TEXT, 'txFee' REAL, 'minConf' REAL,"
                    " 'disabled' INTEGER, 'delisted' INTEGER, 'frozen' INTEGER,	PRIMARY KEY('name'))")
                q1.exec_()
                q1.prepare(
                    "CREATE TABLE 'fractkoef' ( 'idfractkoef' INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, 'intervals' INTEGER NOT NULL, 'idchardata'	INTEGER NOT NULL, 'a' REAL NOT NULL, 'b' REAL NOT NULL,	'sigma'	REAL NOT NULL)")
                q1.exec_()
                q1.prepare(
                    "CREATE TABLE 'parameters' ('name' TEXT NOT NULL UNIQUE, 'value' TEXT NOT NULL,	PRIMARY KEY('name'))")
                q1.exec_()
                q1.prepare(
                    "CREATE UNIQUE INDEX 'curdata7200' ON 'chardata7200' ('curname'	ASC, 'date'	ASC)")
                q1.exec_()
                self.updatetable()
                self.settings.setValue("dbpath", fname)

    @pyqtSlot()
    def trig_menuexit(self):
        sys.exit()

# =============== меню Операции ================================================
    @pyqtSlot()
    def trig_menuvalidation(self):
        if not self.db.isOpen():
            return

        model = QStandardItemModel()
        model.setColumnCount(7)
        model.setHorizontalHeaderLabels(['Пара', 'К-во баров', 'Мин. дата', 'Макс. дата', 'К-во 7200', 'К-во ФК', 'null data'])
        self.tableView3.setModel(model)


        q1 = QSqlQuery(self.db)
        q2 = QSqlQuery(self.db)
        q1.prepare("SELECT curname FROM curpair ORDER BY curname ASC")
        q1.exec_()
        while q1.next():
            curname = q1.value(0)
            q2.prepare("SELECT date, low, high FROM chardata7200 WHERE curname = :curname ORDER BY date ASC")
            q2.bindValue(":curname", curname)
            q2.exec_()
            list_bar = []
            dx_dict = {}
            flag_wrong = 0
            while q2.next():
                list_bar.append((q2.value(0), q2.value(1), q2.value(2)))

            count_bar = len(list_bar)
            if count_bar == 0:
                min_date = 0
                max_date = 0
            else:
                min_date = list_bar[0][0]
                max_date = list_bar[-1][0]
            for i, bar in enumerate(list_bar):
                if bar[1] <= 0 or bar[2] <= 0 or bar[2] < bar[1]:
                    flag_wrong = 1
                if i > 0:
                    dx = bar[0] - list_bar[i - 1][0]
                    if dx in dx_dict:
                        dx_dict[dx] = dx_dict[dx] + 1
                    else:
                        dx_dict[dx] = 1

            if 7200 in dx_dict:
                count_7200 = dx_dict[7200]
            else:
                count_7200 = 0

            textFKwrong = ''
            intervals = []
            q2.prepare("SELECT name FROM parameters WHERE name LIKE 'interval_'")
            q2.exec_()
            while q2.next():
                intervals.append(q2.value(0))
            for interval in intervals:
                q2.prepare(
                    "SELECT COUNT(chardata7200.idchardata) FROM chardata7200 INNER JOIN " + interval + " "
                    "ON chardata7200.idchardata = " + interval + ".idchardata "
                    "WHERE chardata7200.curname = :curname ORDER BY chardata7200.date ASC")
                q2.bindValue(":curname", curname)
                q2.exec_()
                q2.next()
                if q2.value(0) != count_bar:
                    textFKwrong = textFKwrong + str(q2.value(0))+","
            model.appendRow(
                [QStandardItem(curname),
                 QStandardItem(),
                 QStandardItem(),
                 QStandardItem(),
                 QStandardItem(),
                 QStandardItem(),
                 QStandardItem()])
            model.item(model.rowCount()-1, 1).setData(count_bar, Qt.DisplayRole)
            model.item(model.rowCount() - 1, 2).setData(min_date, Qt.DisplayRole)
            model.item(model.rowCount() - 1, 3).setData(max_date, Qt.DisplayRole)
            model.item(model.rowCount() - 1, 4).setData(count_7200, Qt.DisplayRole)
            if count_7200 == count_bar - 1:
                model.item(model.rowCount() - 1, 4).setBackground(self.qb_green)
            else:
                model.item(model.rowCount() - 1, 4).setBackground(self.qb_red)
            model.item(model.rowCount() - 1, 5).setText(textFKwrong)
            if not textFKwrong:
                model.item(model.rowCount() - 1, 5).setBackground(self.qb_green)
            else:
                model.item(model.rowCount() - 1, 5).setBackground(self.qb_red)
            if flag_wrong == 0:
                model.item(model.rowCount() - 1, 6).setBackground(self.qb_green)
            else:
                model.item(model.rowCount() - 1, 6).setBackground(self.qb_red)

    @pyqtSlot()
    def trig_calcfractals(self):
        def insidecalc(curname, rank):
            # выбираем последний рассчитаный фрактал порядка rank + 1
            qa.prepare("SELECT date FROM chardata7200 WHERE curname = :curname AND uprank = :rank ORDER BY date DESC LIMIT 1")
            qa.bindValue(":curname", curname)
            qa.bindValue(":rank", rank + 1)
            qa.exec_()
            if qa.next():
                lastDate = qa.value(0)
            else:
                lastDate = 0

            qa.prepare("SELECT idchardata, high FROM chardata7200 WHERE curname = :curname AND uprank = :rank AND date > :date ORDER BY date ASC")
            qa.bindValue(":curname", curname)
            qa.bindValue(":rank", rank)
            qa.bindValue(":date", lastDate)
            qa.exec_()
            qb.prepare("BEGIN TRANSACTION")
            qb.exec_()
            mas = []
            nup = 0
            while qa.next():
                mas.append([qa.value(0), qa.value(1)])
                n = qa.at()
                nup = n
                if n < 4:
                    continue
                if mas[n - 2][1] > mas[n - 4][1] and mas[n - 2][1] > mas[n - 3][1] and mas[n - 2][1] > mas[n - 1][1] and mas[n - 2][1] > mas[n][1]:
                    qb.prepare("UPDATE chardata7200 SET uprank = :rank WHERE idchardata = :idchardata")
                    qb.bindValue(":idchardata", mas[n-2][0])
                    qb.bindValue(":rank", rank + 1)
                    qb.exec_()
            qb.prepare("COMMIT")
            qb.exec_()

            # выбираем последний рассчитаный фрактал порядка rank + 1
            qa.prepare(
                "SELECT date FROM chardata7200 WHERE curname = :curname AND downrank = :rank ORDER BY date DESC LIMIT 1")
            qa.bindValue(":curname", curname)
            qa.bindValue(":rank", rank + 1)
            qa.exec_()
            if qa.next():
                lastDate = qa.value(0)
            else:
                lastDate = 0

            qa.prepare("SELECT idchardata, low FROM chardata7200 WHERE curname = :curname AND downrank = :rank AND date > :date ORDER BY date ASC")
            qa.bindValue(":curname", curname)
            qa.bindValue(":rank", rank)
            qa.bindValue(":date", lastDate)
            qa.exec_()
            qb.prepare("BEGIN TRANSACTION")
            qb.exec_()
            mas = []
            ndown = 0
            while qa.next():
                mas.append((qa.value(0), qa.value(1)))
                n = qa.at()
                ndown = n
                if n < 4:
                    continue
                if mas[n - 2][1] < mas[n - 4][1] and mas[n - 2][1] < mas[n - 3][1] and mas[n - 2][1] < mas[n - 1][1] and mas[n - 2][1] < mas[n][1]:
                    qb.prepare("UPDATE chardata7200 SET downrank = :rank WHERE idchardata = :idchardata")
                    qb.bindValue(":idchardata", mas[n - 2][0])
                    qb.bindValue(":rank", rank + 1)
                    qb.exec_()
            qb.prepare("COMMIT")
            qb.exec_()
            return (nup, ndown)

        if not self.db.isOpen():
            return
        q1 = QSqlQuery(self.db)
        qa = QSqlQuery(self.db)
        qb = QSqlQuery(self.db)
        q1.prepare("SELECT curname FROM curpair ORDER BY curname")
        q1.exec_()
        while q1.next():
            curname = q1.value(0)
            print(curname)
            r = 0
            (n_up, n_down) = insidecalc(curname, r)
            while (n_up >= 4 or n_down >= 4):
                r += 1
                (n_up, n_down) = insidecalc(curname, r)
                print('Ранг='+str(r)+' nup='+str(n_up)+' ndown='+str(n_down))

    @pyqtSlot()
    def trig_calcfractalkoef(self):
        def mnk(xlist, ylist):
            n = np.size(xlist)
            sx = np.sum(xlist)
            sy = np.sum(ylist)
            sxy = np.sum(np.multiply(xlist, ylist))
            sxx = np.sum(np.square(xlist))
            a = (n * sxy - sx * sy) / (n * sxx - sx * sx)
            b = (sy - a * sx) / n
            sigma = np.sum(np.square(np.subtract(ylist, a * xlist + b)))
            return (a, b, sigma)

        if not self.db.isOpen():
            return

        model = QStandardItemModel()
        model.setColumnCount(4)
        model.setHorizontalHeaderLabels(['Пара', 'К-во баров', 'К-во рассч. баров', 'Время'])
        self.tableView3.setModel(model)

        q1 = QSqlQuery(self.db)
        q2 = QSqlQuery(self.db)

        # cf.intervals = [1, 2, 4, 8]
        # listbars = [[0, 1, 5],
        #             [1, 2, 4],
        #             [2, 3, 7],
        #             [3, 5, 12],
        #             [4, 4, 10],
        #             [5, 4, 8],
        #             [6, 8, 10],
        #             [7, 2, 8]]
        # nplistbars = np.array(listbars)
        # nplistbars1 = nplistbars[:, [1, 2]]
        # cf.list_bar = nplistbars1
        # cf.start()
        # cf.wait()
        # return

        # подгружаем из базы интервалы
        intervals = {}
        q1.prepare("SELECT name, value FROM parameters WHERE name LIKE 'interval_'")
        q1.exec_()
        while q1.next():
            intervals.update({q1.value(0):list(map(int, q1.value(1).split(',')))})
        # выбираем все валютные пары
        q1.prepare("SELECT curname FROM curpair ORDER BY curname ASC")
        q1.exec_()
        # цикл по валютным парам
        while q1.next():
            timestart = time.time_ns()
            curname = q1.value(0)
            print(curname)
            # выбираем все бары
            q2.prepare("SELECT idchardata, low, high FROM chardata7200 WHERE curname = :curname ORDER BY date ASC")
            q2.bindValue(":curname", curname)
            q2.exec_()
            listbar = []
            while q2.next():
                listbar.append([q2.value(0), q2.value(1), q2.value(2)])
            count_bar = len(listbar)
            # если история баров полностью пустая
            if count_bar == 0:
                continue
            np_listbar = np.array(listbar)
            for interval in intervals:
                print(intervals[interval])
                cf_intervals = np.array(intervals[interval])

                # выбираем бары, которых нету в рассчтанных коэффициентах
                q2.prepare("SELECT chardata7200.idchardata FROM chardata7200 LEFT OUTER JOIN " + interval + " ON chardata7200.idchardata = " + interval + ".idchardata "
                    "WHERE chardata7200.curname = :curname AND " + interval + ".idchardata IS NULL ORDER BY chardata7200.date ASC")
                q2.bindValue(":curname", curname)
                q2.exec_()
                list_calckoef = []
                lastinterval = intervals[interval][-1]
                #for i, bar in enumerate(np_listbar):
                while q2.next():
                    i = np.argwhere(np_listbar == q2.value(0))[0, 0]
                    if i < lastinterval:
                        list_calckoef.append([np_listbar[i, 0], 0, 0, 0])
                        continue
                    list_bar = np_listbar[i-lastinterval:i, [1, 2]]

                    interval_log = np.log(cf_intervals)
                    vj = [np.sum(np.subtract(np.amax(np.reshape(list_bar[:, [1]], (interval, -1)), axis=1),
                                             np.amin(np.reshape(list_bar[:, [0]], (interval, -1)), axis=1))) for
                          interval in cf_intervals]
                    vj_log = np.log(vj)

                    (a, b, sigma) = mnk(interval_log, vj_log)

                    list_calckoef.append([np_listbar[i, 0], a, b, sigma])
                q2.prepare("BEGIN TRANSACTION")
                q2.exec_()
                for calckoef in list_calckoef:
                    q2.prepare("INSERT INTO " + interval + "(idchardata, a, b, sigma) VALUES (:idchardata, :a, :b, :sigma)")
                    q2.bindValue(":idchardata", int(calckoef[0]))
                    q2.bindValue(":a", float(calckoef[1]))
                    q2.bindValue(":b", float(calckoef[2]))
                    q2.bindValue(":sigma", float(calckoef[3]))
                    q2.exec_()
                q2.prepare("COMMIT")
                q2.exec_()

            fulltime = (time.time_ns() - timestart) / 1000000000
            model.appendRow(
                [QStandardItem(curname),
                 QStandardItem(),
                 QStandardItem(),
                 QStandardItem()])
            model.item(model.rowCount() - 1, 3).setData(fulltime, Qt.DisplayRole)
            model.item(model.rowCount() - 1, 1).setData(count_bar, Qt.DisplayRole)

# ===================================================================================
    @pyqtSlot()
    def push_the_button(self):
        if not self.db.isOpen():
            return
        qw = QDialog(self)
        qw.setWindowTitle('Тестер торговых стратегий')
        tw = testerWindow(self.db)
        tw.setupUi(qw)
        qw.show()
# ====== обработка кнопок онлайн, база, приват ===========================================================

    def updateButtons(self):
        if self.flagOnline == 1:
            self.toplabel1.setStyleSheet('background-color: rgb(212, 255, 212)')
            self.toplabel1.setText('online')
        else:
            self.toplabel1.setStyleSheet('background-color: rgb(255, 212, 212)')
            self.toplabel1.setText('offline')
        if self.db.isOpen():
            self.toplabel2.setStyleSheet('background-color: rgb(212, 255, 212)')
            self.toplabel2.setText('database connected')
        else:
            self.toplabel2.setStyleSheet('background-color: rgb(255, 212, 212)')
            self.toplabel2.setText('database disconnected')
        if self.flagPrivate == 1:
            self.toplabel3.setStyleSheet('background-color: rgb(212, 255, 212)')
            self.toplabel3.setText('private')
        else:
            self.toplabel3.setStyleSheet('background-color: rgb(255, 212, 212)')
            self.toplabel3.setText('public')

    @pyqtSlot()
    def mainwindow_toplabelsclicked(self):
        obj = self.sender()
        name = obj.objectName()
        # нажатие кнопки online-offline
        if name == 'toplabel1':
            if self.flagOnline == 0:
                if not self.db.isOpen():
                    return
                self.flagOnline = 1
                self.finished_ThreadReturnCurrencies()
                self.finished_ThreadReturnTicker()
                self.finished_ThreadReturnCompleteBalances()
                self.finished_ThreadReturnChartData()
                self.finished_thq()
            else:
                self.flagOnline = 0
                self.flagPrivate = 0
                # self.q['Normal'].clear()
        elif name == 'toplabel2':
            if not self.db.isOpen():
                self.trig_menuopendb()
            else:
                self.db.close()
                self.flagPrivate = 0
                self.flagOnline = 0
        elif name == 'toplabel3':
            if self.flagPrivate == 0:
                if not self.db.isOpen() or self.flagOnline == 0:
                    return
                self.flagPrivate = 1
                self.finished_ThreadReturnCompleteBalances()
            else:
                self.flagPrivate = 0
        self.updateButtons()

    @pyqtSlot()
    def comboBox1_currentIndexChanged(self):
        ct = self.comboBox1.currentText()
        self.tableView1.model().setFilterKeyColumn(0)
        if ct == 'избранное':
            self.tableView1.model().setFilterRole(3)
            self.tableView1.model().setFilterFixedString('1')
        elif ct == 'все':
            self.tableView1.model().setFilterRole(0)
            self.tableView1.model().setFilterRegExp(QRegExp("*"))
        else:
            self.tableView1.model().setFilterRole(0)
            self.tableView1.model().setFilterRegExp(ct+'_')

    # ============= действия по меню по правой кнопке на model1 =========

    def drawChartGraphics(self, cur):
        self.graphicsView.clear()
        plotImage = self.graphicsView.getPlotItem()

        mhigh = []
        mlow = []
        mup = []
        mdown = []
        q1 = QSqlQuery(self.db)
        q1.prepare("SELECT date, low, high, uprank, downrank FROM chardata7200 WHERE curname = :curname ORDER BY date ASC")
        q1.bindValue(":curname", cur)
        q1.exec_()
        while q1.next():
            mhigh.append([q1.value(0), q1.value(2)])
            mlow.append([q1.value(0), q1.value(1)])
            if q1.value(3) >= 2:
                mup.append([q1.value(0), q1.value(2)])
            if q1.value(4) >= 2:
                mdown.append([q1.value(0), q1.value(1)])

        self.graphicsView.plot([x[0] for x in mhigh], [x[1] for x in mhigh])
        barlow = pg.PlotDataItem([x[0] for x in mlow], [x[1] for x in mlow])
        plotImage.addItem(barlow)

        # barup = pg.ScatterPlotItem([x[0] for x in mup], [x[1] for x in mup])
        # barup.setSymbol('d')
        # barup.setBrush(QColor(192, 0, 0))
        # plotImage.addItem(barup)
        # bardown = pg.ScatterPlotItem([x[0] for x in mdown], [x[1] for x in mdown])
        # bardown.setSymbol('d')
        # bardown.setBrush(QColor(0, 192, 0))
        # plotImage.addItem(bardown)

        self.graphicsView.autoRange()

        plotImage.setMouseEnabled(True, False)
        viewBox = plotImage.getViewBox()
        viewBox.enableAutoRange(axis='y', enable=True)
        viewBox.setAutoVisible(False, True)
        plotImage.getAxis("bottom").showLabel(False)

    def saveForDeductor_Bar(self, cur):
        fpath = self.settings.value("dedpath", "")
        fname = cur + "_ded_bar.txt"
        filename = QFileDialog().getSaveFileName(self, "Файл для Deductor бары", fpath + "/" + fname, "txt files (*.txt)")[0]
        if filename:
            file = open(filename, "w")
            file.write("<DATE/TIME>;<HIGH>;<LOW>;<TICKVOL>;<VOL>\n")
            self.settings.setValue("dedpath", QFileDialog().directory().absolutePath())
            q1 = QSqlQuery(self.db)
            q1.prepare("SELECT date,high,low,volume,quoteVolume FROM chardata7200 WHERE curname = :curname ORDER BY date ASC")
            q1.bindValue(":curname", cur)
            q1.exec_()
            while q1.next():
                texttofile = datetime.utcfromtimestamp(q1.value(0)).__str__()+";"+q1.value(1).__str__()+";"+q1.value(2).__str__()+";"+q1.value(3).__str__()+";"+q1.value(4).__str__()+"\n"
                file.write(texttofile)
            file.close()

    def saveForDeductor_Fract(self, cur):
        fpath = self.settings.value("dedpath", "")
        fname = cur + "_ded_fract.txt"
        filename = QFileDialog().getSaveFileName(self, "Файл для Deductor фракталы", fpath + "/" + fname, "txt files (*.txt)")[0]
        if filename:
            file = open(filename, "w")
            file.write("<DATE/TIME>;<UPRANK>;<DOWNRANK>\n")
            self.settings.setValue("dedpath", QFileDialog().directory().absolutePath())
            q1 = QSqlQuery(self.db)
            q1.prepare("SELECT date, uprank, downrank FROM chardata7200 WHERE curname = :curname ORDER BY date ASC")
            q1.bindValue(":curname", cur)
            q1.exec_()
            while q1.next():
                texttofile = datetime.utcfromtimestamp(q1.value(0)).__str__()+";"+q1.value(1).__str__()+";"+q1.value(2).__str__()+"\n"
                file.write(texttofile)
            file.close()

    def saveForDeductor_FractKoef(self, cur):
        fpath = self.settings.value("dedpath", "")
        fname = cur + "_ded_fractkoef.txt"
        filename = QFileDialog().getSaveFileName(self, "Файл для Deductor фракт. коэф.", fpath + "/" + fname, "txt files (*.txt)")[0]
        if filename:
            file = open(filename, "w")
            file.write("<DATE/TIME>;<A>;<B>;<SIGMA>\n")
            self.settings.setValue("dedpath", QFileDialog().directory().absolutePath())
            q1 = QSqlQuery()
            q1.prepare("SELECT chardata.date, fractkoef.a, fractkoef.b, fractkoef.sigma FROM chardata INNER JOIN fractkoef ON chardata.idchardata = fractkoef.idchardata "
                       "WHERE chardata.curname = :curname AND fractkoef.intervals = 4 ORDER BY chardata.date ASC")
            q1.bindValue(":curname", cur)
            q1.exec_()
            while q1.next():
                texttofile = datetime.utcfromtimestamp(q1.value(0)).__str__()+";"+q1.value(1).__str__()+";"+q1.value(2).__str__()+";"+q1.value(3).__str__()+"\n"
                file.write(texttofile)
            file.close()

    def saveForForexMT5(self, cur):
        dialog = QDialog(self)
        lastDatedt = dialog.dateEnter = self.settings.value("mt5DateOfLastUnloading"+cur, "")
        dialog.accepted.connect(lambda: self.setupDateEnterValue(form.dateEdit.dateTime()))
        form = Ui_Form()
        form.setupUi(dialog)
        result = dialog.exec_()
        if result == 0:
            return
        fpath = self.settings.value("mt5path", "")
        fname = cur + "_mt5.txt"
        filename = QFileDialog().getSaveFileName(self, "Файл для MT5", fpath + "/" + fname, "txt files (*.txt)")[0]
        if filename:
            file = open(filename, "w")
            file.write("<DATE>;<TIME>;<OPEN>;<HIGH>;<LOW>;<CLOSE>;<TICKVOL>;<VOL>;<SPREAD>\n")
            self.settings.setValue("mt5path", QFileDialog().directory().absolutePath())
            q1 = QSqlQuery(self.db)
            q1.prepare("SELECT date,high,low,quoteVolume,volume FROM chardata7200 WHERE curname = :curname AND date >= :dateEnter ORDER BY date ASC")
            q1.bindValue(":curname", cur)
            QDateTime.setTimeZone(self.dateEnter, QTimeZone(0))
            q1.bindValue(":dateEnter", QDateTime.toSecsSinceEpoch(self.dateEnter))
            q1.exec_()
            while q1.next():
                datedt = datetime.utcfromtimestamp(q1.value(0))
                texttofile = datedt.strftime("%Y.%m.%d") + ";" + datedt.strftime("%H:%M:%S") + ";" + q1.value(1).__str__() + ";" + q1.value(1).__str__() + ";" + q1.value(2).__str__() + ";" + q1.value(2).__str__() + \
                             ";" + q1.value(3).__str__() + ";" + q1.value(4).__str__() + "\n"
                file.write(texttofile)
                lastDatedt = QDateTime.toString(QDateTime.fromSecsSinceEpoch(q1.value(0)), 'dd.MM.yyyy')

            file.close()
            self.settings.setValue("mt5DateOfLastUnloading"+cur, lastDatedt)

    @pyqtSlot()
    def setupDateEnterValue(self, dateEnter):
        self.dateEnter = dateEnter
# ==================================================================
    @pyqtSlot()
    def tableView1Clicked(self):
        index = self.tableView1.selectedIndexes()[0].siblingAtColumn(0)
        cur = self.tableView1.model().itemData(index)[Qt.DisplayRole]
        self.drawChartGraphics(cur)

    @pyqtSlot()
    def tableView1DoubleClicked(self):
        index = self.tableView1.selectedIndexes()[0].siblingAtColumn(0)
        cur = self.tableView1.model().itemData(index)[Qt.DisplayRole]

        self.qw.setWindowTitle('Торговля по паре: '+cur)
        self.modelAsks.setHorizontalHeaderLabels(['Цена', 'Продают, '+str.split(cur, '_')[1]])
        self.modelBids.setHorizontalHeaderLabels(['Цена', 'Покупают, '+str.split(cur, '_')[1]])
        self.qw.show()


        self.th_ThreadReturnOrderBook.cur = cur
        self.finished_ThreadReturnOrderBook()

    @pyqtSlot()
    def tv_customContextMenuRequested(self):
        indexes = self.tableView1.selectedIndexes()
        if len(indexes) == 0 or len(indexes) > 1:
            return
        menu = QMenu()
        menu.addAction(self.tr("Добавить в избранное")).triggered.connect(lambda: self.customContextMenuTriggered(1))
        menu.addAction(self.tr("Удалить из избранного")).triggered.connect(lambda: self.customContextMenuTriggered(2))

        menu1 = QMenu(self.tr("Выгрузить для Deductor"))
        menu1.addAction(self.tr("Бары")).triggered.connect(lambda: self.customContextMenuTriggered(31))
        menu1.addAction(self.tr("Фракталы")).triggered.connect(lambda: self.customContextMenuTriggered(32))
        menu1.addAction(self.tr("Фрактальные коэф.")).triggered.connect(lambda: self.customContextMenuTriggered(33))
        menu.addMenu(menu1)

        menu.addAction(self.tr("Выгрузить для Forex MT5")).triggered.connect(lambda: self.customContextMenuTriggered(4))
        menu.exec_(QCursor.pos())

    @pyqtSlot()
    def customContextMenuTriggered(self, itemNumber):
        index = self.tableView1.selectedIndexes()[0].siblingAtColumn(0)
        cur = self.tableView1.model().itemData(index)[Qt.DisplayRole]
        if itemNumber == 1:
            sourceIndex = self.tableView1.model().mapToSource(index)
            q1 = QSqlQuery(self.db)
            q1.prepare("INSERT OR IGNORE INTO curpairfav (curname) VALUES (:curname)")
            q1.bindValue(":curname", cur)
            q1.exec_()
            self.model1.item(sourceIndex.row(), 0).setBackground(self.qb_gold)
            self.model1.item(sourceIndex.row(), 0).setData('1', 3)
        elif itemNumber == 2:
            sourceIndex = self.tableView1.model().mapToSource(index)
            q1 = QSqlQuery(self.db)
            q1.prepare("DELETE FROM curpairfav WHERE curname=:curname")
            q1.bindValue(":curname", cur)
            q1.exec_()
            self.model1.item(sourceIndex.row(), 0).setBackground(self.qb_white)
            self.model1.item(sourceIndex.row(), 0).setData('0', 3)
        elif itemNumber == 31:
            self.saveForDeductor_Bar(cur)
        elif itemNumber == 32:
            self.saveForDeductor_Fract(cur)
        elif itemNumber == 33:
            self.saveForDeductor_FractKoef(cur)
        elif itemNumber == 4:
            self.saveForForexMT5(cur)

    @pyqtSlot()
    def traderDialogFinished(self):
        self.finished_ThreadReturnCurrencies()
        self.finished_ThreadReturnTicker()
        self.finished_ThreadReturnCompleteBalances()
        self.finished_ThreadReturnChartData()

# =================================================================
    def updateTableView(self):
        qi1 = self.model1.createIndex(0, 0)
        qi2 = self.model1.createIndex(self.model1.rowCount(),
                                                  self.model1.columnCount())
        self.tableView1.dataChanged(qi1, qi2)
        qi1 = self.tableView2.model().createIndex(0, 0)
        qi2 = self.tableView2.model().createIndex(self.tableView2.model().rowCount(),
                                                  self.tableView2.model().columnCount())
        self.tableView2.dataChanged(qi1, qi2)

app = QApplication([])
win = MainWindow()
sys.exit(app.exec_())





