import pandas as pd
import json
import mainwindow
from dateutil.parser import parse
from tfs import TFSAPI
from PyQt5 import QtWidgets
from PyQt5.QtCore import QDate, QDateTime
import PandasModel
import logic

class WTWindow(QtWidgets.QMainWindow, mainwindow.Ui_Dialog):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.btStart.pressed.connect(self.start_task)
        self.btExportToExcel.pressed.connect(self.start_export)
        start = QDate.currentDate().addDays(-QDate.currentDate().dayOfWeek() + 1)
        end = QDate.currentDate().addDays(7 - QDate.currentDate().dayOfWeek())
        self.dtFrom.setDate(start)
        self.dtTo.setDate(end)

    def start_task(self):
        """Start program"""
        with open('config.json') as config_file:
            configs = json.load(config_file)
            config_token = configs['token']
            client = TFSAPI(configs['server'],
                            project=configs['project'], pat=config_token)

        dateFrom = parse(self.dtFrom.dateTime().toString(),
                         ignoretz=True).strftime('%Y-%m-%d')
        dateTo = parse(self.dtTo.dateTime().toString(),
                       ignoretz=True).strftime('%Y-%m-%d')

        self.validateDate()
        data_fixed = logic.recieveDataForPeriod(client, dateFrom, dateTo)
        model = PandasModel.PandasModel(self.formatingDataFrame(data_fixed))
        self.tblData.setModel(model)
        self.tblData.setMinimumWidth(300)

    def start_export(self):
        """Export data to excel"""

    def validateDate(self):
        """Validate dateFrom dateTo"""
        return self.dtFrom.dateTime() <= self.dtFrom.dateTime()

    def btSave(self):
        """Save token to config file"""
        token = self.lToken.text()
        if self.validate_setting(token):
            with open("config.json", "r") as config_file:
                configs = json.load(config_file)
            configs['token'] = token

    def validate_setting(self, token):
        """Validates token"""
        if len(token) < 52:
            return False

        return True

    def formatingDataFrame(self, data_fixed):
        pd.options.display.float_format = "{:,.2f}".format
        df = pd.DataFrame(data_fixed, columns=[
            "id", "StartTime", "CompletedWork", "ChangedDate", "DisplayName"])

        df["Date"] = pd.to_datetime(df["ChangedDate"]).dt.date
        df["CompletedWork"] = df["CompletedWork"].astype(float)
        dfsum = df.groupby(["DisplayName"], as_index=False).sum()
        return dfsum[["DisplayName", "CompletedWork"]]
