import threading
import boto3
from boto3.dynamodb.conditions import Key
import redis
import os
import random
import string
import termcolor
import time
import uuid


###############################################################
###               Configurações do CHAT                     ###
###############################################################

# envRedisEndpoint = os.getenv("REDIS_ENDPOINT")
# envRedisPort = int(os.getenv("REDIS_PORT"))
# queueSQSEndpoint = os.getenv("SQS_ENDPOINT")
# envAwsAccessKeyId= os.getenv("AWS_ACCESS_KEY_ID")
# envAwsSecretAccessKey = os.getenv("AWS_SECRET_ACCESS_KEY")
# envAwsRegion = os.getenv("AWS_REGION")
# chatName = os.getenv("CHAT_NAME")
# chatVersion = os.getenv("CHAT_VERSION")



###############################################################
###       Configurações do CHAT para USO LOCAL em DEV       ###
###############################################################

envRedisEndpoint = "localhost"
envRedisPort = 6379
envAwsRegion = "us-east-1"
queueSQSEndpoint = "http://localhost:4566/000000000000/chat-queue"
envAwsAccessKeyId= "test" # <== Uso somente com LocalStack (local)
envAwsSecretAccessKey = "test" # <== Uso somente com LocalStack (local)
chatName = "Barba Roots"
chatVersion = "v1.0"



redisClient = redis.StrictRedis(host=envRedisEndpoint,
                           port=envRedisPort,
                           #ssl=True) # <== Se Redis AWS, usando TLS/SSL
                           db=0)



sqsQueue = boto3.client('sqs',
                    region_name=envAwsRegion,
                    aws_access_key_id=envAwsAccessKeyId, #<== Uso somente com LocalStack (local)
                    aws_secret_access_key=envAwsSecretAccessKey, #<== Uso somente com LocalStack (local)
                    endpoint_url = 'http://localhost.localstack.cloud:4566') #<== Uso somente com LocalStack (local)



clients = []


class SessionClient:
    def __init__(self, client, nickname, sessionid, ipaddress):
        self.__client = client
        self.__nickname = nickname
        self.__sessionid = sessionid
        self.__ipaddress = ipaddress

    def getClient(self):
        return self.__client

    def getNickname(self):
        return self.__nickname

    def getSessionId(self):
        return self.__sessionid

    def getIpAddress(self):
        return self.__ipaddress



def showBanner(client):
    message = f"""

------------------------------------------------
Bem-vindo ao CHAT {chatName}
Versão do sistema: {chatVersion}

Nostalgia... brincadeira... isso aqui é para
testes e brincar.

>> Usuários Conectados neste Servidor: {len(clients) + 1}
------------------------------------------------

"""
    color = randomColor()
    client.send(termcolor.colored(f'{message}', color, attrs=["bold"]).encode('utf-8'))



def randomNickname():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=5))



def randomColor():
    listColorOptions = ('red', 'green', 'yellow', 'blue', 'magenta', 'cyan')
    return random.choice(listColorOptions)



def sendBroadcastMsg(message, sessionId = ""):
    for userClientObject in clients:

        client = userClientObject.getClient()
        nickname = userClientObject.getNickname()
        userSessionId = userClientObject.getSessionId()

        try:
            if str(userSessionId).strip() != sessionId.strip():
                client.send(message.encode('utf-8'))
            else:
                _message = message.replace(nickname, 'VOCÊ DISSE')
                client.send(_message.encode('utf-8'))

        except Exception as e:
            print(f"Exception: {e}")
            client.close()
            clients.remove(userClientObject)



def handle(newClient):

    while True:

        client = newClient.getClient()
        nickname = newClient.getNickname()
        sessionId = newClient.getSessionId()

        try:
            message = client.recv(1024).decode('utf-8', errors='ignore')

            if not redisClient.get(nickname):
                raise Exception(f"Nickname {nickname} | Session invalidada ou ausente!\n")

            if message is not None and message.strip() != "":
                #sqsQueue.send_message(QueueUrl=queueSQSEndpoint, MessageBody=f'\n>>> {nickname}: {message} | {sessionId}', MessageGroupId=str(int(time.time()))) # Somente para FIFO
                sqsQueue.send_message(QueueUrl=queueSQSEndpoint, MessageBody=f'\n>>> {nickname}: {message} | {sessionId}')


        except Exception as e:
            print(f"Exception: {e}")

            client.close()
            clients.remove(newClient)
            redisClient.delete(nickname)

            sendBroadcastMsg(termcolor.colored(f'{nickname} saiu do chat!', 'white', 'on_red', attrs=["bold"]))
            sendBroadcastMsg('\n\n ')
            sendBroadcastMsg('> ')

            print(f'[-] Nickname: {nickname} | Session: {sessionId}')

            break



def receiveNewConnection(server):
    while True:

        client, address = server.accept()

        print(f'Conectado com {str(address)}')
        showBanner(client)

        client.send('Informe seu APELIDO: '.encode('utf-8'))

        try:
            nickname = client.recv(1024).decode('utf-8', errors='ignore').upper().strip().replace(' ', '')

            if len(nickname) >= 20:
                client.send("Seu APELIDO deve ter até 20 caracteres.. =(".encode('utf-8'))
                client.close()
                continue

            if redisClient.get(nickname) or nickname == "":
                client.send("Apelido já existente ou inválido, escolha outro".encode('utf-8'))
                client.close()
                continue


        except UnicodeDecodeError:
            nickname = randomNickname()
            client.send(f"Seu apelido é {nickname}".encode('utf-8'))



        newClient = SessionClient(client,
                                  nickname,
                                  str(uuid.uuid4()),
                                  address
        )

        clients.append(newClient)
        redisClient.set(nickname, newClient.getSessionId())

        print(f'[+] Nickname: {nickname} | Session: {newClient.getSessionId()}')
        client.send(f'Bem-vindo {nickname}!\n'.encode('utf-8'))

        sendBroadcastMsg(termcolor.colored(f'{nickname} entrou no chat!', 'white', 'on_green', attrs=["bold"]))
        sendBroadcastMsg('\n\n ')
        sendBroadcastMsg('> ')

        clientThread = threading.Thread(target=handle, args=(newClient,))
        clientThread.start()



def displayOnlineUsers():
    while True:
        time.sleep(300)

        nicknames = []

        for client in clients:
            nicknames.append(client.getNickname())

        message = f"""

------------------------------------------------
> Usuários Online neste Servidor:
------------------------------------------------
{'#####'.join(nicknames)}
------------------------------------------------

""".replace("#####", "\n")

        color = randomColor()
        sendBroadcastMsg(termcolor.colored(f"{message}", color, attrs=["bold"]))
        sendBroadcastMsg('\n\n ')
        sendBroadcastMsg('> ')



def getMessages():
    while True:

        time.sleep(1)

        messages = sqsQueue.receive_message(QueueUrl=queueSQSEndpoint, MaxNumberOfMessages=10)

        if 'Messages' in messages:

            for message in messages['Messages']:

                color = randomColor()

                if len(message['Body'].split('|')) > 1:
                    messageBody, sessionId = message['Body'].split('|')
                    sendBroadcastMsg(termcolor.colored(f"{messageBody}", color, "on_white", attrs=["bold"]), sessionId)
                else:
                    messageBody = message['Body'].split('|')[0]
                    sendBroadcastMsg(termcolor.colored(f"{messageBody}", color, "on_white", attrs=["bold"]))

                sqsQueue.delete_message(QueueUrl=queueSQSEndpoint, ReceiptHandle=message['ReceiptHandle'])

                sendBroadcastMsg('\n\n ')
                sendBroadcastMsg('> ')

