import sys
import socket
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QVBoxLayout, QLineEdit, QPushButton, QWidget, QLabel
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
        self.setWindowTitle("클라이언트 그림판")
        self.setGeometry(100, 100, 800, 600)

        self.client_socket = client_socket

        # UI 설정
        self.result_label = QLabel("", self)
        self.answer_input = QLineEdit(self)
        self.answer_input.setPlaceholderText("정답을 입력하세요...")
        self.send_button = QPushButton("정답 전송", self)
        self.send_button.clicked.connect(self.send_answer)

        # 그래픽 설정
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 800, 500)
        self.view = CustomGraphicsView(self.scene, self)
        
        # 시그널-슬롯 연결
        self.draw_signal.connect(self.view.add_line)

        # 레이아웃 설정
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(self.result_label)
        layout.addWidget(self.answer_input)
        layout.addWidget(self.send_button)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # 데이터 수신 스레드 시작
        self.recv_thread = threading.Thread(target=self.receive_data)
        self.recv_thread.daemon = True
        self.recv_thread.start()

    def send_answer(self):
        answer = self.answer_input.text().strip()
        if answer:
            self.client_socket.sendall(answer.encode())
            self.answer_input.clear()

    def receive_data(self):
        buffer = "" 
        while True:
            try:
                data = self.client_socket.recv(1024).decode()
                if not data:
                    break
                
                print(data)
                

                if data.startswith("LINE:"):
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

                elif data.startswith("RESULT:CORRECT"):
                    self.result_label.setText("정답입니다!")
                    self.scene.clear()
                elif data.startswith("RESULT:WRONG"):
                    self.result_label.setText("틀렸습니다!")
                elif data.startswith("RESULT:ANSWER:"):
                    correct_answer = data.split(":")[2]
                    self.result_label.setText(f"정답은 {correct_answer}입니다!")
                    self.scene.clear()
                elif data.startswith("SERVER:ALREADY"):
                    self.result_label.setText("제시어가 아직 설정되지 않았습니다.")
                elif data.startswith("SEVER:SET"):
                    self.result_label.setText("제시어가 설정되었습니다.")
                    
            except Exception as e:
                print(f"데이터 처리 중 오류: {e}")
                break



def connect_to_server():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(("127.0.0.1", 9000))
    return client_socket


def main():
    app = QApplication([])
    client_socket = connect_to_server()
    window = ClientDrawingApp(client_socket)
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()