import socket
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QVBoxLayout
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtCore import Qt

# 서버 설정
HOST = '0.0.0.0'
PORT = 9000

clients = []



class CustomGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setMouseTracking(True)
        self.pen = QPen(QColor(Qt.black), 5)
        self.last_point = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_point = self.mapToScene(event.pos())

    def mouseMoveEvent(self, event):
        if self.last_point:
            current_point = self.mapToScene(event.pos())
            self.scene().addLine(self.last_point.x(), self.last_point.y(),
                                 current_point.x(), current_point.y(), self.pen)


            data = f"LINE:{self.last_point.x()},{self.last_point.y()},{current_point.x()},{current_point.y()}"
            self.parent().broadcast(data.encode())
            self.last_point = current_point

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_point = None


class ServerDrawingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("서버 그림판")
        self.setGeometry(100, 100, 800, 600)

        # 그래픽 설정
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 800, 600)

        self.view = CustomGraphicsView(self.scene, self)
        self.setCentralWidget(self.view)

        # 서버 소켓 설정
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(5)
        print("서버가 시작되었습니다.")

        # 클라이언트 연결 스레드 실행
        self.server_thread = threading.Thread(target=self.accept_clients)
        self.server_thread.daemon = True
        self.server_thread.start()

    def accept_clients(self):

        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"클라이언트 연결됨: {addr}")
            clients.append(client_socket)
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        #클라이언트 데이터
        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                print(f"클라이언트로부터 데이터 수신: {data.decode()}")
            except Exception as e:
                print(f"클라이언트 처리 중 오류: {e}")
                break
        client_socket.close()
        clients.remove(client_socket)

    def broadcast(self, message):
        #클라이언트에게 데이터 전송
        for client in clients:
            try:
                print(f"브로드캐스트 데이터: {message.decode()}")  # 디버깅용 로그 추가
                client.sendall(message)
            except Exception as e:
                print(f"클라이언트로 데이터 전송 중 오류: {e}")
                clients.remove(client)

    def closeEvent(self, event):
        #서버 종료
        self.server_socket.close()
        print("서버가 종료되었습니다.")
        super().closeEvent(event)


def main():
    app = QApplication([])
    window = ServerDrawingApp()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
