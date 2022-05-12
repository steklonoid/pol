from PyQt6.QtCore import QSize, Qt,  pyqtSlot
from PyQt6.QtWidgets import QPushButton, QGridLayout, QLabel, QLineEdit, QTextEdit, QSizePolicy, QHBoxLayout, QWidget
from PyQt6.QtSql import QSqlQuery

import numpy as np
#   import tensorflow as tf
from tensorflow import keras
from keras import layers, activations, optimizers, losses


class NeyroWindow(object):
    def __init__(self, db, cur):
        self.db = db
        self.cur = cur

    def setup_ui(self, form):
        form.resize(640, 480)
        size_policy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(form.sizePolicy().hasHeightForWidth())
        form.setSizePolicy(size_policy)
        form.setMinimumSize(QSize(640, 480))
        form.setMaximumSize(QSize(640, 480))

        self.gridLayout = QGridLayout(form)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        #   Form.setStyleSheet('background-color: rgb(128, 176, 215)')

        self.labelTop = QLabel(self.cur)
        self.labelTop.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.gridLayout.addWidget(self.labelTop, 0, 0, 1, 1)

        self.whbox1 = QWidget()
        self.hbox1 = QHBoxLayout(self.whbox1)
        self.labelWindowSize = QLabel("Размер окна")
        self.hbox1.addWidget(self.labelWindowSize)
        self.lineEdit_numberEnters = QLineEdit()
        self.lineEdit_numberEnters.setText('20')
        self.hbox1.addWidget(self.lineEdit_numberEnters)
        self.labelpredictSize = QLabel("К-во предсказываемых")
        self.hbox1.addWidget(self.labelpredictSize)
        self.lineEdit_predictSize = QLineEdit()
        self.lineEdit_predictSize.setText('1')
        self.hbox1.addWidget(self.lineEdit_predictSize)
        self.labelEpoch = QLabel("Эпох")
        self.hbox1.addWidget(self.labelEpoch)
        self.lineEdit_Epoch = QLineEdit()
        self.lineEdit_Epoch.setText('10')
        self.hbox1.addWidget(self.lineEdit_Epoch)
        self.gridLayout.addWidget(self.whbox1, 1, 0, 1, 1)

        self.textEdit = QTextEdit()
        self.gridLayout.addWidget(self.textEdit, 2, 0, 1, 1)
        self.textEdit.setObjectName("textEdit")

        self.pushButton = QPushButton(form)
        self.gridLayout.addWidget(self.pushButton, 3, 0, 1, 1)
        self.pushButton.setObjectName("pushButton")
        self.pushButton.setText('П У С К !!!')
        self.pushButton.clicked.connect(lambda: self.pushbutton_clicked())

    @pyqtSlot()
    def pushbutton_clicked(self):
        # создаем запрос
        q1 = QSqlQuery(self.db)
        q1.prepare(
            "SELECT date,high,low FROM chardata7200 WHERE curname = :curname ORDER BY date ASC")
        q1.bindValue(":curname", self.cur)
        q1.exec_()
        listdata = []
        while q1.next():
            listdata.append([q1.value(0), q1.value(1), q1.value(2)])  # формируем спи

        #   listdata = [[i, (i+5)*2, i+4] for i in range(1, 31)]

        listlnhigh = {}
        listlnlow = {}
        for i in range(1, len(listdata)):
            listlnhigh[listdata[i][0]] = np.log(listdata[i][1] / listdata[i - 1][1])
            listlnlow[listdata[i][0]] = np.log(listdata[i][1] / listdata[i - 1][1])

        shift = int(self.lineEdit_numberEnters.text())
        predict = int(self.lineEdit_predictSize.text())
        epoch = int(self.lineEdit_Epoch.text())
        xdata = []
        ydata = []
        for i in range(1, len(listdata) - shift - predict + 1):
            xdataline = []
            for j in range(0, shift):
                xdataline.append(listlnhigh[listdata[i+j][0]])
            xdata.append(xdataline)
            ydataline = []
            for j in range(0, predict):
                ydataline.append(listlnhigh[listdata[i+shift+j][0]])
            ydata.append(ydataline)
        npxdata = np.array(xdata, dtype=np.float32)
        npydata = np.array(ydata, dtype=np.float32)

        inputs = layers.Input(shape=(shift,))
        dense1 = layers.Dense(shift * 2, activation=activations.sigmoid)(inputs)
        dense2 = layers.Dense(shift, activation=activations.sigmoid)(dense1)
        dense3 = layers.Dense(shift // 2, activation=activations.sigmoid)(dense2)
        outputs = layers.Dense(predict, activation=activations.tanh)(dense3)
        model = keras.Model(inputs=inputs, outputs=outputs, name="neyro_model")
        model.summary()
        model.compile(optimizer=optimizers.RMSprop(), loss=losses.MeanSquaredError())
        model.fit(x=npxdata, y=npydata, epochs=epoch, verbose=1, batch_size=64)

        print("====")
        print(npydata[-1:, :])
        print("----")
        print(model.predict(npxdata[-1:, :]))
        model.save("model_"+self.cur+"_epoch"+str(epoch)+"_shift"+str(shift)+"_predict"+str(predict)+".h5",
                   overwrite=True, include_optimizer=True)