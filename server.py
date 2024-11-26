import socket
import threading

# 서버 설정
HOST = '0.0.0.0'  # 모든 IP에서 연결 허용
PORT = 9000

clients = []

def handle_client(client_socket):
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            # 브로드캐스트
            broadcast(data, client_socket)
        except ConnectionResetError:
            break
    client_socket.close()
    clients.remove(client_socket)

def broadcast(message, sender_socket):
    for client in clients:
        if client != sender_socket:
            client.sendall(message)

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print("서버가 시작되었습니다.")

    while True:
        client_socket, addr = server.accept()
        print(f"연결됨: {addr}")
        clients.append(client_socket)
        threading.Thread(target=handle_client, args=(client_socket,)).start()

if __name__ == "__main__":
    main()
