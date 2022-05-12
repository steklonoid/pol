# модуль главного окна
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from datetime import datetime

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1400, 900)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        MainWindow.setCentralWidget(self.centralwidget)

        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.gridLayout.addWidget(self.splitter, 0, 0, 1, 1)
        self.splitterleft = QSplitter(Qt.Orientation.Vertical)
        self.splitter.addWidget(self.splitterleft)
        self.splitterright = QSplitter(Qt.Orientation.Vertical)
        self.splitter.addWidget(self.splitterright)
        self.splitter.setSizes([2, 1])

        self.hspacerwidget = QWidget(self.splitterleft)
        self.hspacerwidget.setObjectName('hspacerwidget')
        self.hspacerwidget.setMaximumHeight(25)
        self.hspacer = QHBoxLayout(self.hspacerwidget)
        self.hspacer.setContentsMargins(0, 0, 0, 0)
        self.hspacer.setObjectName('hspacer')

        self.toplabel1 = QPushButton()
        self.toplabel1.setText('offline')
        self.toplabel1.setStyleSheet('background-color: rgb(255, 212, 212)')
        self.toplabel1.setObjectName('toplabel1')
        self.toplabel1.clicked.connect(self.mainwindow_toplabelsclicked)
        self.hspacer.addWidget(self.toplabel1)

        self.toplabel2 = QPushButton()
        self.toplabel2.setText('БД не подключена')
        self.toplabel2.setStyleSheet('background-color: rgb(255, 212, 212)')
        self.toplabel2.setObjectName('toplabel2')
        self.toplabel2.clicked.connect(self.mainwindow_toplabelsclicked)
        self.hspacer.addWidget(self.toplabel2)

        self.comboBox1 = QComboBox()
        self.comboBox1.setObjectName("comboBox1")
        self.comboBox1.setMaximumHeight(20)
        self.comboBox1.currentIndexChanged.connect(self.comboBox1_currentIndexChanged)
        self.splitterleft.addWidget(self.comboBox1)

        self.tableView1 = QTableView(self.splitterleft)
        self.tableView1.setObjectName("tableView1")
        self.tableView1.resizeColumnsToContents()
        self.tableView1.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tableView1.setSortingEnabled(True)
        self.tableView1.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableView1.customContextMenuRequested.connect(self.tv_customContextMenuRequested)

        self.tableView2 = QTableView(self.centralwidget)
        self.tableView2.setObjectName("tableView2")
        self.tableView2.resizeColumnsToContents()
        self.tableView2.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tableView2.setSortingEnabled(True)
        self.tableView2.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.splitterright.addWidget(self.tableView2)

        self.menubar = QMenuBar(MainWindow)
        self.menubar.setGeometry(QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)

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

        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Pol Charts"))

