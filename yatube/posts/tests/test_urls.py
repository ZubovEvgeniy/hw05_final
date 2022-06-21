from django.test import TestCase, Client

from django.contrib.auth import get_user_model
from http import HTTPStatus
from django.core.cache import cache
from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test_slug',
            description='Test description',
        )
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_urls_take_correct_status_codes_auth(self):
        ''''Страницы доступны любому пользователю'''
        url_status_codes = {
            '/': HTTPStatus.OK,
            '/group/test_slug/': HTTPStatus.OK,
            '/profile/auth/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for address, status_code in url_status_codes.items():
            with self.subTest(status_code=status_code):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status_code)

    def test_urls_take_correct_status_codes_guest(self):
        ''''Страницы доступны авторизованному пользователю'''
        url_status_codes = {
            f'/posts/{self.post.id}/edit/': HTTPStatus.OK,
            '/create/': HTTPStatus.OK,
        }
        for address, status_code in url_status_codes.items():
            with self.subTest(status_code=status_code):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, status_code)

    def test_post_edit_url_not_author_redirect(self):
        """Страница /posts/<post_id>/edit/ перенаправит не автора
        на страницу просмотра записи"""
        self.user_2 = User.objects.create_user(username='auth2')
        self.authorized_client.force_login(self.user_2)
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/',
            follow=True,
            kwargs={'username': 'auth2'},
        )
        self.assertRedirects(
            response, f'/posts/{self.post.id}/')

    def test_post_edit_url_redirect(self):
        """Страница /posts/<post_id>/edit/ перенаправит неавторизованного
        пользователя на страницу авторизации"""
        response = self.guest_client.get(
            f'/posts/{self.post.id}/edit/', follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/')

    def test_post_edit_url_redirect(self):
        """Страница /create/ перенаправит неавторизованного пользователя
        на страницу авторизации"""
        response = self.guest_client.get(
            '/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        templates_url_names = {
            '': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template, in templates_url_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
