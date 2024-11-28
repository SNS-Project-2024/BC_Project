import sys
import socket
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QGraphicsScene, QVBoxLayout, QGraphicsView
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtCore import Qt

SERVER_IP = '127.0.0.1'
SERVER_PORT = 9000

class CustomGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setMouseTracking(True)
        self.pen = QPen(QColor(Qt.red), 10)  # 펜 설정
        self.last_point = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_point = self.mapToScene(event.pos())
            print(f"Mouse Pressed at: {self.last_point}")

    def mouseMoveEvent(self, event):
        if self.last_point:
            current_point = self.mapToScene(event.pos())
            print(f"Drawing line from {self.last_point} to {current_point}")
            self.scene().addLine(self.last_point.x(), self.last_point.y(),
                                 current_point.x(), current_point.y(), self.pen)
            self.last_point = current_point

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            print(f"Mouse Released at: {event.pos()}")
            self.last_point = None

class DrawingApp(QWidget):
    def __init__(self, client_socket):
        super().__init__()
        self.setWindowTitle("그림판")
        self.setGeometry(100, 100, 800, 600)

        self.client_socket = client_socket

        # 그래픽 설정
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 800, 600)
        self.view = CustomGraphicsView(self.scene, self)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.view)
        self.setLayout(self.layout)

        # 데이터 수신 스레드 시작
        self.recv_thread = threading.Thread(target=self.receive_data)
        self.recv_thread.daemon = True
        self.recv_thread.start()

    def receive_data(self):
        while True:
            try:
                data = self.client_socket.recv(1024).decode()
                if data.startswith("LINE:"):
                    _, x1, y1, x2, y2 = map(float, data.split(":")[1].split(","))
                    self.scene.addLine(x1, y1, x2, y2, self.view.pen)  # 받은 데이터를 화면에 그림
            except Exception as e:
                print(f"Error receiving data: {e}")
                break

def connect_to_server():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, SERVER_PORT))
    return client_socket

def main():
    client_socket = connect_to_server()
    app = QApplication(sys.argv)
    window = DrawingApp(client_socket)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
