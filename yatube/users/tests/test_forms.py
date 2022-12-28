from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import CreationForm

User = get_user_model()


class UsersFormTests(TestCase):
    def setUp(self):
        self.form = CreationForm()
        self.guest_client = Client()

    def test_create_user(self):
        """Валидная форма создает запись в User."""
        users_count = User.objects.count()
        form_data = {
            'first_name': 'Тестовое имя',
            'last_name': 'Тестовая фамилия',
            'username': 'Тестер',
            'email': 'test@test.com',
            'password1': 'test_pass',
            'password2': 'test_pass',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:index',))
        self.assertEqual(User.objects.count(), users_count + 1)
        self.assertTrue(
            User.objects.filter(
                first_name='Тестовое имя',
                last_name='Тестовая фамилия',
                username='Тестер',
                email='test@test.com',
            ).exists()
        )
