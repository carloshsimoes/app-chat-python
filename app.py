#!/usr/bin/python3

import socket
import threading
import os
from libs import chat

chatPortServer = int(os.getenv("CHAT_PORT_SERVER"))
#chatPortServer = 8888

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', chatPortServer))
    server.listen(50)
    
    print(f'Serviço escutando na porta TCP: {chatPortServer}\n')

    receiveThread = threading.Thread(target=chat.receiveNewConnection, args=(server,))
    receiveThread.start()

    displayThread = threading.Thread(target=chat.displayOnlineUsers)
    displayThread.start()

    getMessagesThread = threading.Thread(target=chat.getMessages)
    getMessagesThread.start()

       

if __name__ == "__main__":
    main()
