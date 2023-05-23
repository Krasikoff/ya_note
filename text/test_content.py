# news/tests/test_routes.py
from http import HTTPStatus
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone


# Импортируем класс комментария.
from news.models import Comment, News

# Получаем модель пользователя.
User = get_user_model()



class TestRoutes(TestCase):

    HOME_URL = reverse('news:home')

    @classmethod
    def setUpTestData(cls):
        today = datetime.today()
        News.objects.bulk_create(
            News(title=f'Новость {index}', 
                 text='Просто текст.',
                 date=today - timedelta(days=index),
                 )
            for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
        ) 


    def test_news_count(self):
        # Загружаем главную страницу.
        response = self.client.get(self.HOME_URL)
        # Код ответа не проверяем, его уже проверили в тестах маршрутов.
        # Получаем список объектов из словаря контекста.
        object_list = response.context['object_list']
        # Определяем длину списка.
        news_count = len(object_list)
        # Проверяем, что на странице именно 10 новостей.
        self.assertEqual(news_count, settings.NEWS_COUNT_ON_HOME_PAGE) 


    def test_news_order(self):
        response = self.client.get(self.HOME_URL)
        object_list = response.context['object_list']
        # Получаем дату первой новости.
        first_news_date = object_list[0].date
        # Получаем список всех дат новостей на странице.
        all_dates = [news.date for news in object_list]
        # Проверяем, что у первой новости - самое большое значение даты.
        self.assertEqual(first_news_date, max(all_dates)) 

class TestDetailPage(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.news = News.objects.create(
            title='Тестовая новость', text='Просто текст.'
        )
        # Сохраняем в переменную адрес страницы с новостью:
        cls.detail_url = reverse('news:detail', args=(cls.news.id,))
        cls.author = User.objects.create(username='Комментатор')
        # Запоминаем текущее время:
        now = timezone.now()
        # Создаём комментарии в цикле.
        for index in range(2):
            # Создаём объект и записываем его в переменную.
            comment = Comment.objects.create(
                news=cls.news, author=cls.author, text=f'Tекст {index}',
            )
            # Сразу после создания меняем время создания комментария.
            comment.created = now + timedelta(days=index)
            # И сохраняем эти изменения.
            comment.save()

    def test_comments_order(self):
        response = self.client.get(self.detail_url)
        # Проверяем, что объект новости находится в словаре контекста
        # под ожидаемым именем - названием модели.
        self.assertIn('news', response.context)
        # Получаем объект новости.
        news = response.context['news']
        # Получаем все комментарии к новости.
        all_comments = news.comment_set.all()
        # Проверяем, что время создания первого комментария в списке
        # меньше, чем время создания второго.
        self.assertLess(all_comments[0].created, all_comments[1].created) 

    def test_anonymous_client_has_no_form(self):
        response = self.client.get(self.detail_url)
        self.assertNotIn('form', response.context)
        
    def test_authorized_client_has_form(self):
        # Авторизуем клиент при помощи ранее созданного пользователя.
        self.client.force_login(self.author)
        response = self.client.get(self.detail_url)
        self.assertIn('form', response.context) 
