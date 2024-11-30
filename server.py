import socket
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QVBoxLayout, QLineEdit, QPushButton, QFrame
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtCore import Qt

# 서버 설정
HOST = '0.0.0.0'
PORT = 9000

clients = []


class CustomGraphicsView(QGraphicsView):
    def __init__(self, scene, server_app, parent=None):
        super().__init__(scene, parent)
        self.setMouseTracking(True)
        self.pen = QPen(QColor(Qt.black), 5)
        self.last_point = None
        self.server_app = server_app

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_point = self.mapToScene(event.pos())

    def mouseMoveEvent(self, event):
        if self.last_point:
            current_point = self.mapToScene(event.pos())
            self.scene().addLine(self.last_point.x(), self.last_point.y(),
                                 current_point.x(), current_point.y(), self.pen)

            data = f"LINE:{self.last_point.x()},{self.last_point.y()},{current_point.x()},{current_point.y()}"
            self.server_app.broadcast(data.encode())
            self.last_point = current_point

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_point = None


class ServerDrawingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client_ids = {}
        self.setWindowTitle("서버 그림판")
        self.setGeometry(100, 100, 800, 600)

        self.answer = None  # 제시어 저장
        
        # 서버 소켓 설정
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(5)
        print("서버가 시작되었습니다.")

        # 클라이언트 연결 스레드 실행
        self.server_thread = threading.Thread(target=self.accept_clients)
        self.server_thread.daemon = True
        self.server_thread.start()

        # 그래픽 설정
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 800, 600)
        self.view = CustomGraphicsView(self.scene, self)

        # 제시어 입력 UI
        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("제시어를 입력하세요...")
        self.set_button = QPushButton("제시어 설정")
        self.set_button.clicked.connect(self.set_answer)

        # 중앙 프레임 설정 (QWidget 대체)
        central_frame = QFrame()
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(self.answer_input)
        layout.addWidget(self.set_button)
        central_frame.setLayout(layout)

        # QMainWindow의 중앙 위젯 설정
        self.setCentralWidget(central_frame)

        

    def set_answer(self):
        answer = self.answer_input.text().strip()
        if answer is not None:
            self.answer = answer
            print(f"제시어가 설정되었습니다: {self.answer}")
            self.answer_input.clear()
            for client in clients:
                try:
                    message = "SEVER:SET"
                    client.sendall(message.encode())
                except Exception as e:
                    print(f"클라이언트 전송 중 오류 {e}")
                    break

    def accept_clients(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"클라이언트 연결됨: {addr}")
            client_id = f"{addr[1]}"
            self.client_ids[client_socket] = client_id
            clients.append(client_socket)
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        client_id = self.client_ids[client_socket]
        while True:
            try:
                data = client_socket.recv(1024).decode()
                if not data:
                    break
                print(f"[{client_id}]로부터 데이터 수신: {data}")

                # 정답 검증
                if not self.answer:
                    client_socket.sendall("SERVER:ALREADY".encode())
                elif data == self.answer:
                    client_socket.sendall("RESULT:CORRECT".encode())
                    self.broadcast_to_others(client_socket, f"RESULT:ANSWER:{self.answer}")
                    self.reset_game()
                else:
                    client_socket.sendall("RESULT:WRONG".encode())
            except Exception as e:
                print(f"클라이언트 처리 중 오류: {e}")
                break
            
        client_socket.close()
        clients.remove(client_socket)
        del self.client_ids[client_socket]

    def broadcast(self, message):
        for client in clients:
            try:
                client.sendall(message)
            except Exception as e:
                print(f"클라이언트로 데이터 전송 중 오류: {e}")
                clients.remove(client)

    def broadcast_to_others(self, sender_socket, message):
        for client in clients:
            if client != sender_socket:
                try:
                    client.sendall(message.encode())
                except Exception as e:
                    print(f"브로드캐스트 오류: {e}")
                    clients.remove(client)

    def reset_game(self):
        print("게임이 초기화됩니다.")
        self.scene.clear()
        self.answer = None

    def closeEvent(self, event):
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
