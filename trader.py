from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from DownloadingFromSite import ThreadReturnOrderBook, ThreadReturnCompleteBalances
class traderWindow(object):
    def setupUi(self, Form):
        Form.resize(800, 600)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        #Form.setStyleSheet('background-color: rgb(32, 48, 64)')

        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")

        self.l1 = QLabel()
        self.l1.setObjectName("l1")
        self.gridLayout.addWidget(self.l1, 0, 0, 1, 6)
        self.l1.setText('Здесь будет крутой текст')

        self.twAsks = QTableView()
        self.twAsks.setObjectName("tw1")
        #self.twAsks.setStyleSheet('background-color: rgb(48, 32, 64)')
        self.gridLayout.addWidget(self.twAsks, 1, 0, 1, 2)


        self.twBids = QTableView()
        self.twBids.setObjectName("tw2")
        #self.twBids.setStyleSheet('background-color: rgb(48, 64, 32)')
        self.gridLayout.addWidget(self.twBids, 1, 4, 1, 2)

        self.b1 = QPushButton()
        self.b1.setObjectName("b1")
        self.gridLayout.addWidget(self.b1, 2, 0, 1, 1)

        self.b2 = QPushButton()
        self.b2.setObjectName("b2")
        self.gridLayout.addWidget(self.b2, 2, 1, 1, 1)


