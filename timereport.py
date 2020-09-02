import WTWindow
from PyQt5 import QtWidgets

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setQuitOnLastWindowClosed(False)
    window = WTWindow.WTWindow()
    window.show()
    app.exec_()

    # df1.to_excel("output.xlsx")
    # print(dfsum)
