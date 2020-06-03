# модуль главного окна
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from pyqtgraph import PlotWidget, AxisItem
from datetime import datetime
class AxisItemStringDate(AxisItem):
    def __init__(self, *args, **kwargs):
        AxisItem.__init__(self, *args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        ret = []
        if not values:
            return []

        if spacing >= 31622400:  # 366 days
            fmt = "%Y"

        elif spacing >= 2678400:  # 31 days
            fmt = "%Y/%m"

        elif spacing >= 86400:  # = 1 day
            fmt = "%d.%m"

        elif spacing >= 3600:  # 1 h
            fmt = "%d.%m-%Hh"

        elif spacing >= 60:  # 1 m
            fmt = "%H:%M"

        elif spacing >= 1:  # 1s
            fmt = "%H:%M:%S"

        else:
            # less than 2s (show microseconds)
            # fmt = '%S.%f"'
            fmt = '[+%fms]'  # explicitly relative to last second

        for x in values:
            try:
                t = datetime.fromtimestamp(x)
                ret.append(t.strftime(fmt))
            except ValueError:  # Windows can't handle dates before 1970
                ret.append('')

        return ret

    def attachToPlotItem(self, plotItem):
        self.setParentItem(plotItem)
        viewBox = plotItem.getViewBox()
        self.linkToView(viewBox)
        self._oldAxis = plotItem.axes[self.orientation]['item']
        self._oldAxis.hide()
        plotItem.axes[self.orientation]['item'] = self
        pos = plotItem.axes[self.orientation]['pos']
        plotItem.layout.addItem(self, *pos)
        self.setZValue(-1000)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1400, 900)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")

        self.toplabel1 = QPushButton(self.centralwidget)
        self.toplabel1.setText('offline')
        self.toplabel1.setStyleSheet('background-color: rgb(255, 212, 212)')
        self.toplabel1.setObjectName('toplabel1')
        self.toplabel1.clicked.connect(self.mainwindow_toplabelsclicked)
        self.gridLayout.addWidget(self.toplabel1, 0, 0, 1, 1)

        self.toplabel2 = QPushButton(self.centralwidget)
        self.toplabel2.setText('БД не подключена')
        self.toplabel2.setStyleSheet('background-color: rgb(255, 212, 212)')
        self.toplabel2.setObjectName('toplabel2')
        self.toplabel2.clicked.connect(self.mainwindow_toplabelsclicked)
        self.gridLayout.addWidget(self.toplabel2, 0, 1, 1, 1)

        self.toplabel3 = QPushButton(self.centralwidget)
        self.toplabel3.setText('public')
        self.toplabel3.setStyleSheet('background-color: rgb(255, 212, 212)')
        self.toplabel3.setObjectName('toplabel3')
        self.toplabel3.clicked.connect(self.mainwindow_toplabelsclicked)
        self.gridLayout.addWidget(self.toplabel3, 0, 2, 1, 1)

        self.splitter = QSplitter(Qt.Horizontal)
        self.gridLayout.addWidget(self.splitter, 1, 0, 1, 3)
        self.splitterleft = QSplitter(Qt.Vertical)
        self.splitter.addWidget(self.splitterleft)
        self.splitterright = QSplitter(Qt.Vertical)
        self.splitter.addWidget(self.splitterright)
        self.splitter.setSizes([1, 1])

        self.graphicsView = PlotWidget(self.splitterleft)
        self.graphicsView.setObjectName("graphicsView")
        self.plotItem = self.graphicsView.getPlotItem()
        self.plotItem.getViewBox().setMenuEnabled(False)
        self.plotItem.setTitle("График")
        axx = AxisItemStringDate(orientation='bottom')
        axx.attachToPlotItem(self.plotItem)
        self.splitterleft.addWidget(self.graphicsView)

        self.hspacerwidget = QWidget(self.splitterleft)
        self.hspacerwidget.setObjectName('hspacerwidget')
        self.hspacerwidget.setMaximumHeight(25)
        self.hspacer = QHBoxLayout(self.hspacerwidget)
        self.hspacer.setContentsMargins(0, 0, 0, 0)
        self.hspacer.setObjectName('hspacer')

        self.comboBox1 = QComboBox()
        #self.comboBox.setGeometry(QtCore.QRect(160, 30, 211, 22))
        self.comboBox1.setObjectName("comboBox1")
        self.comboBox1.currentIndexChanged.connect(self.comboBox1_currentIndexChanged)
        self.hspacer.addWidget(self.comboBox1)

        self.hspb2 = QPushButton()
        self.hspb2.setObjectName('hspb2')
        self.hspb2.setText('')
        self.hspacer.addWidget(self.hspb2)
        self.hspb3 = QPushButton()
        self.hspb3.setObjectName('hspb3')
        self.hspb3.setText('')
        
        self.hspacer.addWidget(self.hspb3)
        self.hspb4 = QPushButton()
        self.hspb4.setObjectName('hspb4')
        self.hspb4.setText('')
        self.hspacer.addWidget(self.hspb4)

        self.tableView1 = QTableView(self.centralwidget)
        self.tableView1.setObjectName("tableView1")
        self.tableView1.resizeColumnsToContents()
        self.tableView1.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableView1.setSortingEnabled(True)
        self.tableView1.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableView1.customContextMenuRequested.connect(self.tv_customContextMenuRequested)
        self.tableView1.doubleClicked.connect(self.tableView1DoubleClicked)
        self.tableView1.clicked.connect(self.tableView1Clicked)
        self.splitterleft.addWidget(self.tableView1)
        self.splitterleft.setSizes([5, 1, 5])

        self.tableView2 = QTableView(self.centralwidget)
        self.tableView2.setObjectName("tableView2")
        self.tableView2.resizeColumnsToContents()
        self.tableView2.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableView2.setSortingEnabled(True)
        self.tableView2.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.splitterright.addWidget(self.tableView2)

        self.tableView3 = QTableView(self.centralwidget)
        self.tableView3.setObjectName("tableView3")
        self.tableView3.resizeColumnsToContents()
        self.tableView3.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableView3.setSortingEnabled(True)
        self.tableView3.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.splitterright.addWidget(self.tableView3)
        self.splitterright.setSizes([1, 1])

        self.downloadingCurrency = QLabel(self.centralwidget)
        self.downloadingCurrency.setFrameShape(QFrame.Box)
        self.gridLayout.addWidget(self.downloadingCurrency, 2, 0, 1, 1)
        self.FUpdateButton = QPushButton(self.centralwidget)
        self.FUpdateButton.setObjectName("FUpdateButton")

        self.gridLayout.addWidget(self.FUpdateButton, 2, 1, 1, 1)
        self.FCalculateButton = QPushButton(self.centralwidget)
        self.FCalculateButton.setObjectName("FCalculateButton")
        self.FCalculateButton.clicked.connect(self.push_the_button)
        self.gridLayout.addWidget(self.FCalculateButton, 2, 2, 1, 1)


        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setGeometry(QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menubar")

        self.filemenu = self.menubar.addMenu("Файл")
        self.menuopendb = QAction("Открыть базу", self)
        self.menucreatedb = QAction("Создать новую базу", self)
        self.menuexit = QAction("Выход", self)
        self.menuopendb.triggered.connect(self.trig_menuopendb)
        self.menucreatedb.triggered.connect(self.trig_menucreatedb)
        self.menuexit.triggered.connect(self.trig_menuexit)
        self.filemenu.addAction(self.menuopendb)
        self.filemenu.addAction(self.menucreatedb)
        self.filemenu.addAction(self.menuexit)

        self.operationmenu = self.menubar.addMenu("Операции")
        self.menuvalidation = QAction("Валидация данных", self)
        self.operationmenu.addAction(self.menuvalidation)
        self.menuvalidation.triggered.connect(self.trig_menuvalidation)

        self.menucalcfractals = QAction("Рассчитать фракталы", self)
        self.operationmenu.addAction(self.menucalcfractals)
        self.menucalcfractals.triggered.connect(self.trig_calcfractals)
        self.menucalcfractalkoef = QAction("Рассчитать фракт. коэф.", self)
        self.operationmenu.addAction(self.menucalcfractalkoef)
        self.menucalcfractalkoef.triggered.connect(self.trig_calcfractalkoef)


        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Pol Charts"))
        self.FCalculateButton.setText(_translate("MainWindow", "Кнопка"))
        self.FUpdateButton.setText(_translate("MainWindow", "Обновить таблицу"))

