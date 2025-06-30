# Тестовое задание для Ростелеком

Микросервисная система из двух сервисов и воркера для обработки задач через RabbitMQ.

Два сервиса: 

1. Service A на FastAPI с задержкой 60с как в ТЗ.    Запуск через main.py

2. Service B асинхронный на FastAPI как в ТЗ.   Запуск через main.py

3. Script - воркер для получения задачи через rabbitmq, отправления запроса в синхронный сервис Service_A. Ожидания ответа, и отправления результата в rabbitMQ.   Запустить worker_task.py.






Запуск для проверки

1. В файле config.ini изменить настройки rabbitMQ

[RABBITMQ]
user = guest
password = guest
host = localhost
port = 	5672


2. Service A - Service_A/main.py - на порту 8001

3. Service B - Service_B/main.py - на порту 8002

4. script - script/worker_task.py 

если service_A запускаете на другом порту, в worker_task.py измените ссылку на верный порт 

API_BASE_URL = "http://localhost:8001"  # URL FastAPI Server_A





📌 Особенности реализации
1. Service A имитирует задержку 60 секунд перед ответом

2. Service B работает асинхронно

3. Воркер автоматически обрабатывает задачи из очереди

4. Конфигурация через единый config.ini

🔄 Workflow системы
1. Пользователь делает запрос в Service B

3. Service B ставит задачу в RabbitMQ

4. Воркер забирает задачу, делает запрос в Service A

5. После получения ответа от Service A, результат отправляется обратно через RabbitMQ

6. После запроса в Service B пользователь может мониторить статус задачи
 
