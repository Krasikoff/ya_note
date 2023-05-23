#При попытке перейти на страницу списка заметок, страницу успешного добавления записи, 
#страницу добавления заметки, отдельной заметки, редактирования или удаления 
#заметки анонимный пользователь перенаправляется на страницу логина.

from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

# Импортируем класс комментария.
from notes.models import  Note

# Получаем модель пользователя.
User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Создаём двух пользователей с разными именами:
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        # От имени одного пользователя создаём заметку:
        cls.note = Note.objects.create(
            title='Заголовок1',
            text='Текст1',
            slug='slug1',
            author=cls.author,
            )        

##Главная страница доступна анонимному пользователю.
##Страницы регистрации пользователей, входа в учётную запись и выхода из неё доступны всем пользователям.
    def test_pages_availability(self):
        urls = (
            ('notes:home', None),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

#Страницы отдельной заметки, удаления и редактирования заметки доступны
#только автору заметки. Если на эти страницы попытается зайти другой пользователь —
# вернётся ошибка 404.
    def test_availability_for_note_edit_and_delete(self):
        urls = (
            ('notes:detail'),
            ('notes:edit'),
            ('notes:delete'),
        )

        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            # Логиним пользователя в клиенте:
            self.client.force_login(user)
            # Для каждой пары "пользователь - ожидаемый ответ"
            # перебираем имена тестируемых страниц:
            for name in urls:  
                with self.subTest(user=user, name=name):   
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

#Аутентифицированному пользователю доступна страница со списком заметок notes/, 
#страница успешного добавления заметки done/, страница добавления новой заметки add/.
    def test_availability_for_add_success_list_note(self):
        urls = (
            ('notes:list'),
            ('notes:success'),
            ('notes:add'),
        )

        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.OK),
        )
        for user, status in users_statuses:
            # Логиним пользователя в клиенте:
            self.client.force_login(user)
            # Для каждой пары "пользователь - ожидаемый ответ"
            # перебираем имена тестируемых страниц:
            for name in urls:  
                with self.subTest(user=user, name=name):   
                    url = reverse(name, args=None,)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

#При попытке перейти на страницу списка заметок, страницу успешного добавления записи, 
#страницу добавления заметки, отдельной заметки, редактирования или удаления 
#заметки анонимный пользователь перенаправляется на страницу логина.
    def test_redirect_for_anonymous_client(self):
        urls = (
            ('notes:list',None),
            ('notes:success',None),
            ('notes:delete',(self.note.slug,)),
            ('notes:add',None),
            ('notes:detail',(self.note.slug,)),
            ('notes:edit', (self.note.slug,) ),
        )
        # Сохраняем адрес страницы логина:
        login_url = reverse('users:login')
        # В цикле перебираем имена страниц, с которых ожидаем редирект:
        for name, args in urls:
            with self.subTest(name=name):
                # Получаем адрес страницы редактирования или удаления комментария:
                url = reverse(name, args=args)
                # Получаем ожидаемый адрес страницы логина, 
                # на который будет перенаправлен пользователь.
                # Учитываем, что в адресе будет параметр next, в котором передаётся
                # адрес страницы, с которой пользователь был переадресован.
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                # Проверяем, что редирект приведёт именно на указанную ссылку.
                self.assertRedirects(response, redirect_url)
