from django.test import TestCase
from parameterized import parameterized
from rest_framework.reverse import reverse

from .models import Friendship, User
from .serializers import UserSerializer


class FriendshipTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        u1 = User.objects.create_user(username="Иван", password='123')
        u2 = User.objects.create_user(username="Василий", password='123')
        u3 = User.objects.create_user(username="Николай", password='123')
        u4 = User.objects.create_user(username="Екатерина", password='123')
        u5 = User.objects.create_user(username="Татьяна", password='123')

        Friendship.objects.create(friend1=u1, friend2=u2, status=0)
        Friendship.objects.create(friend1=u2, friend2=u1, status=0)
        Friendship.objects.create(friend1=u1, friend2=u4, status=-1)
        Friendship.objects.create(friend1=u4, friend2=u1, status=1)
        Friendship.objects.create(friend1=u1, friend2=u5, status=1)
        Friendship.objects.create(friend1=u5, friend2=u1, status=-1)

        Friendship.objects.create(friend1=u3, friend2=u2, status=0)
        Friendship.objects.create(friend1=u2, friend2=u3, status=0)
        Friendship.objects.create(friend1=u3, friend2=u4, status=0)
        Friendship.objects.create(friend1=u4, friend2=u3, status=0)
        Friendship.objects.create(friend1=u3, friend2=u5, status=0)
        Friendship.objects.create(friend1=u5, friend2=u3, status=0)

    @parameterized.expand([
        ({'username': 'Петр', 'password': '123'}, 201, '', 6),
        ({'username': 'Петр' * 150, 'password': '123'}, 400,
         '{"username":["Убедитесь, что это значение содержит не более 150 символов."]}', 5),
        ({'username': 'Петр\^/', 'password': '12^\/3'}, 400,
         '{"username":["Введите правильное имя пользователя. Оно может содержать только буквы, цифры и знаки @/./+/-/_."]}',
         5),
        ({}, 400, '{"username":["Обязательное поле."],"password":["Обязательное поле."]}', 5),
    ])
    def test_register(self, data, status, response_body, count):
        response = self.client.post(reverse('register'), data=data)
        self.assertEqual(response.status_code, status)
        if status == 201:
            self.assertEqual(User.objects.count(), count)
        else:
            self.assertEqual(response.content.decode('utf-8'), response_body)

    @parameterized.expand([
        (None, 403, 'Учетные Данные Не Были Предоставлены.'),
        (("Николай", '123'), 200, ''),
        (("Иван", '123'), 200, ''),
        (("Екатерина", '123'), 200, ''),
    ])
    def test_friends_list(self, login_pass, status, response_body):
        if login_pass:
            self.client.login(username=login_pass[0], password=login_pass[1])
        response = self.client.get(reverse('friends-list'))
        self.assertEqual(response.status_code, status)
        if not response_body:
            data = UserSerializer(User.objects.get(username=login_pass[0]).get_users_friends(), many=True).data
            self.assertEqual(response.data, data)
        else:
            self.assertEqual(response.data['detail'].title(), response_body)

    @parameterized.expand([
        (None, 1, 403, 'Учетные Данные Не Были Предоставлены.'),
        (("Иван", '123'), 2, 200, 'Вы друзья.'),
        (("Иван", '123'), 4, 200, 'Вы подали заявку на дружбу.'),
        (("Иван", '123'), 5, 200, 'Пользователь отправил Вам заявку в друзья.'),
        (("Екатерина", '123'), 2, 200, 'Вы еще не друзья.'),
        (("Екатерина", '123'), 4, 200, 'Это вы.'),
        (("Екатерина", '123'), 7, 404, 'Страница Не Найдена.'),
    ])
    def test_get_friendship_status(self, login_pass, pk, status, response_body):
        if login_pass:
            self.client.login(username=login_pass[0], password=login_pass[1])
        response = self.client.get(reverse('friends-detail', kwargs={'pk': pk}))
        self.assertEqual(response.status_code, status)
        if status == 200:
            self.assertEqual(response.data['friendship_status'], response_body)
        else:
            self.assertEqual(response.data['detail'].title(), response_body)

    @parameterized.expand([
        (None, {}, 403, 'Учетные Данные Не Были Предоставлены.', 12),
        (("Иван", '123'), {"friend2": 1}, 422, 'Нельзя Отправить Заявку Самому Себе.', 12),
        (("Иван", '123'), {"friend2": 2}, 208, {'friend2': 2, 'status': 0}, 12),
        (("Иван", '123'), {"friend2": 3}, 201, {'friend2': 3, 'status': -1}, 14),
        (("Иван", '123'), {"friend2": 4}, 208, {'friend2': 4, 'status': -1}, 12),
        (("Иван", '123'), {"friend2": 5}, 200, {'friend2': 5, 'status': 0}, 12),
        (("Иван", '123'), {"friend2": 15}, 400, 'Недопустимый Первичный Ключ "15" - Объект Не Существует.', 12),
        (("Иван", '123'), {"friend2": -15}, 400, 'Недопустимый Первичный Ключ "-15" - Объект Не Существует.', 12),
        (("Иван", '123'), {"friend2": ''}, 400, 'Это Поле Не Может Быть Пустым.', 12),
        (("Иван", '123'), {"friend2": 'None'}, 400,
         'Некорректный Тип. Ожидалось Значение Первичного Ключа, Получен Str.', 12),
        (("Иван", '123'), {}, 400, 'Обязательное Поле.', 12),
    ])
    def test_send_friendship(self, login_pass, data, status, response_body, count):
        if login_pass:
            self.client.login(username=login_pass[0], password=login_pass[1])
        response = self.client.post(reverse('friends-list'), data=data)
        self.assertEqual(response.status_code, status)
        if 200 <= status < 400:
            self.assertEqual(response.data['friend2'], response_body['friend2'])
            self.assertEqual(response.data['status'], response_body['status'])
        else:
            resp = response.data['detail'] if 'detail' in response.data else response.data['friend2'][0]
            self.assertEqual(resp.title(), response_body)
        self.assertEqual(Friendship.objects.count(), count)

    @parameterized.expand([
        (None, {}, 403, 'Учетные Данные Не Были Предоставлены.', 12),
        (("Иван", '123'), 1, 204, '', 12),
        (("Иван", '123'), 2, 204, '', 10),
        (("Иван", '123'), 3, 204, '', 12),
        (("Иван", '123'), 4, 204, '', 12),
        (("Иван", '123'), 5, 204, '', 12),
        (("Иван", '123'), 15, 404, 'Страница Не Найдена.', 12),
    ])
    def test_delete_friend(self, login_pass, pk, status, response_body, count):
        if login_pass:
            self.client.login(username=login_pass[0], password=login_pass[1])
        response = self.client.delete(reverse('friends-detail', kwargs={'pk': pk}))
        self.assertEqual(response.status_code, status)
        if status != 204:
            self.assertEqual(response.data['detail'].title(), response_body)
        self.assertEqual(Friendship.objects.count(), count)

    @parameterized.expand([
        (None, 1, 403, 'Учетные Данные Не Были Предоставлены.', 0),
        (("Иван", '123'), 1, 200, '', 1),
        (("Иван", '123'), -1, 200, '', 1),
        (("Иван", '123'), 0, 200, '', 1),
        (("Николай", '123'), 0, 200, '', 3),
        (("Николай", '123'), 1, 200, '', 0),
        (("Николай", '123'), 12, 400, 'Выберите Корректный Вариант. 12 Нет Среди Допустимых Значений.', 0),
        (("Николай", '123'), 'jj', 400, 'Выберите Корректный Вариант. Jj Нет Среди Допустимых Значений.', 0),
    ])
    def test_list_friend_requests(self, login_pass, filter_count, status, response_body, count):
        if login_pass:
            self.client.login(username=login_pass[0], password=login_pass[1])
        url = reverse('friendship-list') + '?status=%s' % filter_count
        response = self.client.get(url)
        self.assertEqual(response.status_code, status)
        if status == 200:
            self.assertEqual(len(response.data), count)
        else:
            resp = response.data['detail'] if 'detail' in response.data else response.data['status'][0]
            self.assertEqual(resp.title(), response_body)

    @parameterized.expand([
        (None, 1, 403, 'Учетные Данные Не Были Предоставлены.'),
        (("Иван", '123'), 1, 400, 'Попытка Доступа К Чужой Или Неактуальной Заявке.'),
        (("Иван", '123'), 5, 200, {'user': 5, 'status': 0}),
        (("Иван", '123'), 6, 400, 'Попытка Доступа К Чужой Или Неактуальной Заявке.'),
        (("Иван", '123'), 66, 404, 'Страница Не Найдена.'),
    ])
    def test_accept_friendship(self, login_pass, pk, status, response_body):
        if login_pass:
            self.client.login(username=login_pass[0], password=login_pass[1])
        response = self.client.get(reverse('friendship-detail', kwargs={'pk': pk}))
        self.assertEqual(response.status_code, status)
        if status == 200:
            self.assertEqual(response.data['friend2'], response_body['user'])
            self.assertEqual(response.data['status'], response_body['status'])
        else:
            self.assertEqual(response.data['detail'].title(), response_body)

    @parameterized.expand([
        (None, 1, 403, 'Учетные Данные Не Были Предоставлены.', 12),
        (("Иван", '123'), 1, 400, 'Попытка Доступа К Чужой Или Неактуальной Заявке.', 12),
        (("Иван", '123'), 5, 204, '', 10),
        (("Иван", '123'), 6, 400, 'Попытка Доступа К Чужой Или Неактуальной Заявке.', 12),
        (("Иван", '123'), 66, 404, 'Страница Не Найдена.', 12),
    ])
    def test_reject_friendship(self, login_pass, pk, status, response_body, count):
        if login_pass:
            self.client.login(username=login_pass[0], password=login_pass[1])
        response = self.client.delete(reverse('friendship-detail', kwargs={'pk': pk}))
        self.assertEqual(response.status_code, status)
        if status != 204:
            self.assertEqual(response.data['detail'].title(), response_body)
        self.assertEqual(Friendship.objects.count(), count)
