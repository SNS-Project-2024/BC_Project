import sys
import socket
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QVBoxLayout, QLineEdit, QPushButton, QWidget
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtCore import Qt, pyqtSignal


class CustomGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setMouseTracking(True)
        self.pen = QPen(QColor(Qt.black), 5)

    def add_line(self, x1, y1, x2, y2):
        #서버로 받은 그림 그리기
        print(f"add_line 호출됨: ({x1}, {y1}) -> ({x2}, {y2})")
        self.scene().addLine(x1, y1, x2, y2, self.pen)
        self.scene().update()
        self.viewport().update()


class ClientDrawingApp(QMainWindow):
    draw_signal = pyqtSignal(float, float, float, float)

    def __init__(self, client_socket):
        super().__init__()
        self.setWindowTitle("클라이언트 그림판 (수신 전용)")
        self.setGeometry(100, 100, 800, 600)

        # 네트워크 설정
        self.client_socket = client_socket

        # 그래픽 설정
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 800, 600)  # 서버와 동일한 범위
        self.view = CustomGraphicsView(self.scene, self)
        self.setCentralWidget(self.view)
        
        # 텍스트 입력 UI
        self.message_input = QLineEdit(self)
        self.message_input.setPlaceholderText("메시지를 입력하세요...")
        self.send_button = QPushButton("전송", self)
        self.send_button.clicked.connect(self.send_message)
        
        # 레이아웃 설정
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(self.message_input)
        layout.addWidget(self.send_button)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # 시그널-슬롯 연결
        self.draw_signal.connect(self.view.add_line)

        # 데이터 수신 스레드 시작
        self.recv_thread = threading.Thread(target=self.receive_data)
        self.recv_thread.daemon = True
        self.recv_thread.start()
        
    def send_message(self):
        message = self.message_input.text().strip()
        if message:
            try:
                self.client_socket.sendall(f"MSG:{message}".encode())
                print(f"서버로 메시지 전송: {message}")
                self.message_input.clear()
            except Exception as e:
                print(f"메시지 전송 중 오류: {e}")

    def receive_data(self):
        buffer = ""  # 남은 데이터를 저장할 버퍼
        while True:
            try:
                data = self.client_socket.recv(1024).decode()
                if not data:  # 연결 종료
                    print("서버로부터 연결이 종료되었습니다.")
                    break
                buffer += data

                while "LINE:" in buffer:
                    start_idx = buffer.find("LINE:")
                    end_idx = buffer.find("LINE:", start_idx + 1)
                    if end_idx == -1:  # 다음 메시지를 기다림
                        break
                    line = buffer[start_idx:end_idx].strip()
                    buffer = buffer[end_idx:]

                    if line.startswith("LINE:"):
                        _, coords = line.split(":")
                        x1, y1, x2, y2 = map(float, coords.split(","))
                        self.draw_signal.emit(x1, y1, x2, y2)  # UI 갱신 요청
            except ConnectionResetError:
                print("서버 연결이 끊어졌습니다.")
                break
            except Exception as e:
                print(f"데이터 처리 중 오류: {e}")
                break

    def closeEvent(self, event):
        #창 닫으면 연결 종료
        try:
            self.client_socket.close()
            print("클라이언트가 서버와의 연결을 종료했습니다.")
        except Exception as e:
            print(f"클라이언트 종료 중 오류: {e}")
        event.accept()


def connect_to_server():
    #서버 연결
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect(("127.0.0.1", 9000))  # 서버 IP와 PORT
        print("서버에 연결되었습니다.")
        return client_socket
    except ConnectionRefusedError:
        print("서버 연결 실패: 서버가 실행 중인지 확인하세요.")
        sys.exit(1)


def main():
    app = QApplication(sys.argv)
    client_socket = connect_to_server()
    window = ClientDrawingApp(client_socket)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
