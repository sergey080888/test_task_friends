# **Описание**
Сервис может:
-	зарегистрировать нового пользователя
-	отправить одному пользователю заявку в друзья другому
-	принять/отклонить пользователю заявку в друзья от другого пользователя
-	посмотреть пользователю список своих исходящих и входящих заявок в друзья
-	посмотреть пользователю список своих друзей
-	получить пользователю статус дружбы с каким-то другим пользователем (нет ничего / есть исходящая заявка / есть входящая заявка / уже друзья)
-	удалить пользователю другого пользователя из своих друзей
-	если пользователь1 отправляет заявку в друзья пользователю2, а пользователь2 отправляет заявку пользователю1, то они автоматом становятся друзьями, их заявки автоматом принимаются

Также:
-	описан REST интерфейс сервиса с помощью OpenAPI
-	написан на Django сервис по этой спецификации
-	описана краткая документация с примерами запуска сервиса и вызова его API
+ unit-тесты
+ Dockerfile для упаковки в контейнер
# Описание REST интерфейса

Более подробное описание системы и ее работы представлено в файле Документация.pdf.

![image](https://user-images.githubusercontent.com/63101721/236899935-c16b3366-62ef-4a21-9fc8-ea5374e42aff.png)