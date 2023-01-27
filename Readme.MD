# Chat APP - Python3

Exemplo de projeto para estudo, de um servidor de CHAT, para que os usuários possam se conectar via TELNET.

OBS; O mesmo funciona bem para clientes vindo de sistemas que trabalham com encoding UTF-8 (Linux e etc).

Para clientes que se conectam com client Telnet à partir do MS Windows, o Windows por padrão, usa a codificação de caracteres "cp1252". Logo pode ocorrer uma experiência ruim e erros não esperados.

Como dito, é um exemplo para estudos, brincadeira/nostalgia.


**Alguns recursos já implementados:**

- Validação de Nickname até 20 caracteres;
- Valida se já existe um usuário conectado (session) com o Nickname informado, evitando uso de apelidos iguais;
- Envio e Recebimento de mensagens se apoiam em mensageria, nosso caso foi implementado o uso com AWS SQS, podendo rodar o LocalStack para testes locais;
- Armazenamento do Nickname + SessionID (UUID) gerado em um REDIS (aqui usando Docker para subir o REDIS).
- Quando usuário enviar uma mensagem, ela cai na FILA e é consumida e replicada para todos usuários (broadcast);
- Graças ao armazenamento da Session, quando você envia uma mensagem é exibido como "VOCÊ DISSE";
- A cada 5 minutos o APP envia mensagem para todos com os usuários conectados no CHAT;
- Sempre que um novo usuário entra ou sai, é exibido também para todos em destaque;


**Recursos a serem implementados no Futuro:**

- Para trabalhar em um ambiente distribuido com mais nós, pode ser interessante se apoiar em um sistema de mensageria melhor como RabbitMQ;
- Resolver questões de encoding para clientes by Windows;
- Suporte e integração com Discord e outros, utilizando Webhook;
- Suporte a cadastro/autenticação dos usuários em caso de persistir seu Apelido único;
- Implementação de comandos (ex: /list users), para que o usuário possa ter recursos adicionais ao CHAT;
- Implementar soluções de moderação para palavrões e recursos para futuros moderadores banir usuário por IP Origem. Hoje se a Session do usuário for invalidada/removida do Redis ele será desconectado já;
- Refletir Chat na WEB; Implementar uma versão WEB, que funciona no mesmo contexto, interagindo juntos seja usuários vindo da WEB ou via TERMINAL;
- Implementar possibilidade de Canais/Salas;


# Como cliente pode se conectar??


> telnet IP_ADDRESS_SERVER 8888

ou

> nc IP_ADDRESS_SERVER 8888


# Executando o APP local para testes:


# Primeiro vamos criar nosso environment

Vamos criar nosso ENV e instalar as LIBs que já estão anunciadas no `requirements.txt`.

```bash

python3 -m venv --prompt chat-python .venv

. .venv/bin/activate

pip install -r requirements.txt

```

Feito isso, podemos prosseguir com a criação dos nossos 2 recursos que utilizamos nessa POC/Projeto:

- redis;
- localstack;

# O que é LocalStack?

LocalStack é uma solução para simular um Stack Cloud Local totalmente funcional. Aonde você pode localmente testar chamadas de API para a Stack Local simulando vários serviços AWS como S3, API Gateway, CloudFront, Amplify e dentre vários.

Maiores informações sobre o LocalStack:

> https://docs.localstack.cloud/aws


# Instalando o Localstack e criando nossa Fila SQS:

Podemos utilizar o **localstack** local, o que já está disponível (instalado a lib). Ou podemos executar o mesmo à partir de um Container (Docker).


**01 - Executnado via Container/Docker:**

```bash

docker run -d -p4566:4566 localstack/localstack

```

**02 - Executando o LocalStack local:**

Para rodar local, lá em cima na criação do nosso Environment, já instalamos a LIB do LocalStack.

Senão fez o passo anterior, o faça:

```bash

python3 -m venv --prompt chat-python .venv

. .venv/bin/activate

pip install -r requirements.txt

```

Isso já vai resolver as dependências das bibliotecas para você.

Mas a título de informação, se quiser instalar manualmente o **Localstack** e o **awscli-local**, basta:

```bash

pip install localstack
pip install awscli-local

``` 


Em seguida, se optou por rodar o **Localstack** localmente (sem container), precisamos iniciar o **Localstack**:

```bash

localstack start

```

Finalizado isso, agora vamos criar nossos recursos que iremos utilizar abaixo!!


# Criando nossa Fila/SQS no Localstack:

Criando nossa Fila SQS:

> **Observação:** Entendemos que o Localstack já em execução, seja local ou Docker, escutando na porta 4566.


```bash

awslocal sqs create-queue --queue-name chat-queue

```

Criamos nossa fila com nome **chat-qeueu**!

Exemplo da URI/Endpoint para consumir a mesma:

- http://localhost:4566/000000000000/chat-queue


# Enviando uma mensagem para Fila SQS para testar:

Se quiser testar a fila (opcional), basta:

```bash

awslocal sqs send-message --queue-url http://localhost:4566/000000000000/chat-queue --message-body test

```


# Criando nosso serviço Redis com Docker:

Para o Redis, vamos utilizar um Container Docker.

```bash

docker run -d -p 6379:6379 redis


```

Pronto, isso é suficiente, temos nosso serviços **Redis** já escutando na porta 6379!


# Definindo as configuração/parametrizações do APP:

Precisamos definir/setar as configurações/parametrizações para rodar nosso APP.

Você podera fazer isso entro do arquivo/lib `libs/chat/chat.py`.

Se for recuperar esses valores de variáveis de ambiente (ENV), o que é recomendado/apropriado, descomentar as linhas abaixo no arquivo:

```python

###############################################################
###               Configurações do CHAT                     ###
###############################################################

envRedisEndpoint = os.getenv("REDIS_ENDPOINT")
envRedisPort = int(os.getenv("REDIS_PORT"))
queueSQSEndpoint = os.getenv("SQS_ENDPOINT")
envAwsAccessKeyId= os.getenv("AWS_ACCESS_KEY_ID")
envAwsSecretAccessKey = os.getenv("AWS_SECRET_ACCESS_KEY")
envAwsRegion = os.getenv("AWS_REGION")
chatName = os.getenv("CHAT_NAME")
chatVersion = os.getenv("CHAT_VERSION")

```


Se não for recuperar esses valores de variáveis de ambiente (ENV), pode definir diretamente no arquivo, descomentando as linhas abaixo:

> Aqui já está o exemplo em que deixo já apontando para o `Redis` local e o endpoint da `Fila SQS` também local!

```python

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

```

Pronto, já definida as configurações do APP, podemos então iniciar o mesmo!!


# Finalmente, iniciando nosso APP CHAT Python:

Agora com todos serviços e requisitos criados, vamos então iniciar nosso **APP - Chat Python**!!!

**Para executar o APP, basta rodar:**

> **Observação:** Isso se tiver definido o valor da `variável` **chatPortServer** no `app.py`.

```bash

# python3 app.py

```

Caso não tenha definido o valor da `variável` **chatPortServer** no `app.py`, mas já está pegando a mesma do ENV **CHAT_PORT_SERVER**, basta:

```bash

# export CHAT_PORT_SERVER=8888 && python3 app.py

```


# Opção de Iniciar nosso APP CHAT utilizando Container:

Adicionalmente, foi disponibilizado dois arquivos:

- **Dockerfile**
- **runAPP.sh**

Já com o que é preciso para buildar/construir sua imagem de Container para a aplicação.

> **Atençao:** Utilizando Container a biblioteca `termcolor` não funcionou bem, assim, toda experiência do usuário com cores no chat, fundo das mensagens e etc., não funcionou como esperado!

Se ainda sim, deseja executar a aplicação com Container para testar:

**Criando nossa imagem Docker:**

```bash

docker image build -t app-chat:1.0 .

```

**Executando nosso container/APP em seguida:**

```bash

docker container run -d -p 8888:8888 --env "CHAT_PORT_SERVER=8888" app-chat:1.0

```

Lembrando que, rodando dentro de um container, deverá se atentar as definições/configurações do CHAT, para apontar para os endpoints dos serviços corretos.

No caso de usar o `Redis` e `Localstack` com container também, não irá funcionar usar `localhost` como referência, neste caso aponte para o **endereço IP** de fato do seu PC/instâncias, ou use **Compose** ou **Swarm** para se apoiar em Service Discovery e usar o nome dos próprios Services.


Mas enfim, se for usar Docker para "empacotar" o APP CHAT, recomendo que tenha experiẽncia com Docker.

Senão, siga o passo anterior e rode o mesmo diretamente no seu ambiente após seguir todos os passos aqui descritos e terá sucesso!


=)