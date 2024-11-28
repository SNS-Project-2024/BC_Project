import sys
import socket
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsEllipseItem
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtCore import Qt, QPointF

# 클라이언트 설정
SERVER_IP = '127.0.0.1'  # 서버 IP 주소
SERVER_PORT = 9000

class DrawingApp(QMainWindow):
    def __init__(self, socket_client):
        super().__init__()
        self.setWindowTitle("갈틱폰 - 그림판")
        self.setGeometry(100, 100, 800, 600)

        # 네트워크 설정
        self.client_socket = socket_client

        # 그래픽 설정
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene, self)
        self.setCentralWidget(self.view)

        self.pen = QPen(QColor(Qt.black), 3)
        self.last_point = None

        # 데이터 수신 스레드
        self.recv_thread = threading.Thread(target=self.receive_data)
        self.recv_thread.daemon = True
        self.recv_thread.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_point = self.view.mapToScene(event.pos())

    def mouseMoveEvent(self, event):
        if self.last_point:
            current_point = self.view.mapToScene(event.pos())
            line = self.scene.addLine(self.last_point.x(), self.last_point.y(), 
                                      current_point.x(), current_point.y(), self.pen)
            self.last_point = current_point

            # 네트워크로 그림 데이터 전송
            data = f"LINE:{self.last_point.x()},{self.last_point.y()},{current_point.x()},{current_point.y()}"
            self.client_socket.sendall(data.encode())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_point = None

    def receive_data(self):
        while True:
            try:
                data = self.client_socket.recv(1024).decode()
                if data.startswith("LINE:"):
                    _, x1, y1, x2, y2 = map(float, data.split(":")[1].split(","))
                    self.scene.addLine(x1, y1, x2, y2, self.pen)
            except ConnectionResetError:
                break


def connect_to_server():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, SERVER_PORT))
    return client_socket

def main():
    app = QApplication(sys.argv)
    socket_client = connect_to_server()
    window = DrawingApp(socket_client)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
