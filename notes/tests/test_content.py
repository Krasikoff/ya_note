from http import HTTPStatus

import pdb

from django.conf import settings
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
            title='Заголовок2',
            text='Текст2',
            slug='slug_2',
            author=cls.author,
            )        

        cls.note = Note.objects.create(
            title='Заголовок3',
            text='Текст3',
            slug='slug_3',
            author=cls.reader,
            )        
        cls.list_url= reverse('notes:list', )
        cls.detail_url = reverse('notes:detail', args=(cls.note.slug,))
        cls.add_url = reverse('notes:add', )
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))        
        print(cls.detail_url)


#отдельная заметка передаётся на страницу со списком заметок в 
#списке object_list в словаре context;
#в список заметок одного пользователя не попадают заметки другого пользователя;
    def test_notes_count(self):
        users_statuses = (
            (self.author, 1),
            (self.reader, 1),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            with self.subTest(user=user,):
                response = self.client.get(self.list_url)
                object_list = response.context['object_list']
                news_count = len(object_list)
                self.assertEqual(news_count, status) 
#        pdb.set_trace()
#на страницы создания и редактирования заметки передаются формы.
    def test_authorized_client_has_form(self):
        urls = (
            self.edit_url,
            self.add_url
        )
        # Авторизуем клиент при помощи ранее созданного пользователя.
        self.client.force_login(self.reader)
        for url in urls:
            with self.subTest(url = url):
                response = self.client.get(url)
                self.assertIn('form', response.context)  
