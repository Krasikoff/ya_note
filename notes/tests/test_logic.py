
from http import HTTPStatus

from pytils.translit import slugify

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

# Импортируем из файла с формами список стоп-слов и предупреждение формы.
# Загляните в news/forms.py, разберитесь с их назначением.
from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestCommentCreation(TestCase):
    # Текст комментария понадобится в нескольких местах кода, 
    # поэтому запишем его в атрибуты класса.
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Толстой')
        cls.reader = User.objects.create(username='Простой')
        # Создаём пользователя и клиент, логинимся в клиенте.
#        cls.user = User.objects.create(username='Крокодил')
#        cls.auth_client = Client()
#       cls.auth_client.force_login(cls.author)
        #Одна новость
        cls.note = Note.objects.create(
            title='Заголовок5',
            text='Текст5',
            slug='slug_5',
            author=cls.author,
            )      
        cls.SAME_SLUG =  'slug_5' 
        cls.NOTE_TEXT =  'Текст5'
        # Данные для POST-запроса при создании новости.
        cls.form_data = {
            'title':'TitleFormData',
            'text':'TekstFormData',
            'slug':'slug_FormData',
            'author':cls.author,
            }
        # Адрес страницы с новостью.
        cls.url = reverse('notes:detail', args=(cls.note.slug,))
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.add_url = reverse('notes:add', )
        cls.success_url = reverse('notes:success', )


#Залогиненный пользователь может создать заметку, а анонимный — не может.
    def test_anonymous_user_cant_create_note(self):
        # Совершаем запрос от анонимного клиента, в POST-запросе отправляем
        # предварительно подготовленные данные формы с текстом комментария.     
        notes_count_before = Note.objects.count()
        self.client.post(self.url, data=self.form_data)
        # Считаем количество комментариев.
        notes_count_after = Note.objects.count()
        # Ожидаем, что комментариев в базе нет - сравниваем с нулём.
        self.assertEqual(notes_count_after, notes_count_before)

    def test_user_can_create_note(self):
        notes_count_before = Note.objects.count()
        self.client.force_login(self.author)
        response = self.client.post(self.add_url, data=self.form_data)
        # Считаем количество комментариев.
        notes_count_after = Note.objects.count()
        # Убеждаемся, что добавили один комментарий.
        self.assertEqual(notes_count_after, notes_count_before+1)
        # Получаем объект комментария из базы.
        note = Note.objects.get(slug=self.form_data['slug'],)
        # Проверяем, что все атрибуты комментария совпадают с ожидаемыми.
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.author, self.author)

#Невозможно создать две заметки с одинаковым slug.
    def test_user_cant_create_two_note_with_same_slug(self):
        notes_count_before = Note.objects.count()
        self.client.force_login(self.author)
        data=self.form_data['slug'] = self.SAME_SLUG
        response = self.client.post(self.add_url, data=self.form_data)
#        print(response)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=self.form_data['slug'] + WARNING
        )
        # Считаем количество комментариев.
        notes_count_after = Note.objects.count()
        # Убеждаемся, что добавили один комментарий.
        self.assertEqual(notes_count_after, notes_count_before)

#Если при создании заметки не заполнен slug, то он формируется автоматически, с помощью функции pytils.translit.slugify.

    def test_not_filled_slug(self):
        notes_count_before = Note.objects.count()
        self.client.force_login(self.author)
        data=self.form_data['slug'] = ''
        response = self.client.post(self.add_url, data=self.form_data)
        wait_slug = slugify(self.form_data['title'])[:100]
        note = Note.objects.get(slug=wait_slug,)
        # Проверяем, что все атрибуты комментария совпадают с ожидаемыми.
        self.assertEqual(note.slug, wait_slug)
        # Считаем количество комментариев.
        notes_count_after = Note.objects.count()
        # Убеждаемся, что добавили один комментарий.
        self.assertEqual(notes_count_after, notes_count_before + 1)


#Пользователь может редактировать и удалять свои заметки, но не может редактировать или удалять чужие.

    def test_author_can_edit_comment(self):
        self.client.force_login(self.author)
        # Выполняем запрос на редактирование от имени автора комментария.
        response = self.client.post(self.edit_url, data=self.form_data)
        # Проверяем, что сработал редирект.
#        self.assertRedirects(response, self.url_to_comments)
        # Обновляем объект комментария.
        self.note.refresh_from_db()
        # Проверяем, что текст комментария соответствует обновленному.
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.author, self.author)


    def test_author_can_delete_comment(self):
        notes_count_before = Note.objects.count()

        self.client.force_login(self.author)
        # От имени автора комментария отправляем DELETE-запрос на удаление.
        response = self.client.delete(self.delete_url)
        self.assertRedirects(response, self.success_url)
#        note = Note.objects.get(slug=self.form_data['slug'],)
        # Считаем количество комментариев в системе.
        notes_count_after = Note.objects.count()
        # Ожидаем ноль комментариев в системе.
        self.assertEqual(notes_count_after, notes_count_before - 1 )

    def test_user_cant_edit_note_of_another_user(self):
        # Выполняем запрос на редактирование от имени другого пользователя.
        self.client.force_login(self.reader)
        response = self.client.post(self.edit_url, data=self.form_data)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Обновляем объект комментария.
        self.note.refresh_from_db()
        # Проверяем, что текст остался тем же, что и был.
        self.assertEqual(self.note.text, self.NOTE_TEXT)

    def test_user_cant_delete_comment_of_another_user(self):
        notes_count_before = Note.objects.count()
        # Выполняем запрос на удаление от пользователя-читателя.
        self.client.force_login(self.reader)
        response = self.client.delete(self.delete_url)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Убедимся, что комментарий по-прежнему на месте.
        comments_count_after = Note.objects.count()
        self.assertEqual(comments_count_after, notes_count_before)
