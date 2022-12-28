from http import HTTPStatus
from django.test import TestCase, Client


class PostsURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_guest_client_accessableness_urls(self):
        """Страницы доступны любому пользователю."""
        urls = [
            '/about/author/',
            '/about/tech/',
        ]
        for address in urls:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_templates_names = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for address, template in url_templates_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
