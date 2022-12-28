from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

# from ..models import Group, Post

User = get_user_model()


class UsersURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

        self.authorized_user = User.objects.create_user(username='Тестер')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.authorized_user)

    def test_guest_client_accessableness_urls(self):
        """Страницы доступны любому пользователю."""
        urls = [
            '/auth/signup/',
            '/auth/logout/',
            '/auth/login/',
            '/auth/password_reset/',
            '/auth/password_reset/done/',
            '/auth/reset/<uidb64>/<token>/',
            '/auth/reset/done/',
        ]
        for address in urls:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_client_accessableness_urls(self):
        """Страницы доступны авторизованному пользователю."""
        urls = [
            '/auth/password_change/',
            '/auth/password_change/done/',
        ]
        for address in urls:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_url(self):
        """Запрос к несуществующей странице вернёт ошибку 404."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_edit_url_redirect_anonymous_on_login(self):
        """Страница по адресу /auth/password_change/ перенаправит
        анонимного пользователя на страницу записи.
        """
        response = self.guest_client.get(
            '/auth/password_change/', follow=True,
        )
        self.assertRedirects(
            response, '/auth/login/?next=%2Fauth%2Fpassword_change%2F',
        )

    def test_post_create_url_redirect_anonymous_on_login(self):
        """Страница по адресу /auth/password_change/done/ перенаправит
        анонимного пользователя на страницу логина.
        """
        response = self.guest_client.get(
            '/auth/password_change/done/', follow=True,
        )
        self.assertRedirects(
            response, '/auth/login/?next=%2Fauth%2Fpassword_change%2Fdone%2F',
        )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_templates_names = {
            '/auth/signup/': 'users/signup.html',
            '/auth/login/': 'users/login.html',
            '/auth/password_change/': 'users/password_change_form.html',
            '/auth/password_change/done/': 'users/password_change_done.html',
            '/auth/password_reset/': 'users/password_reset_form.html',
            '/auth/password_reset/done/': 'users/password_reset_done.html',
            '/auth/reset/<uidb64>/<token>/':
                'users/password_reset_confirm.html',
            '/auth/reset/done/': 'users/password_reset_complete.html',
        }
        for address, template in url_templates_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_logout_url_use_correct_template(self):
        """logout URL-адрес использует соответствующий шаблон."""
        response = self.authorized_client.get('/auth/logout/')
        self.assertTemplateUsed(response, 'users/logged_out.html')
