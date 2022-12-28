from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

User = get_user_model()


class UsersPagesTests(TestCase):
    def setUp(self):
        self.authorized_user = User.objects.create_user(username='Тестер')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.authorized_user)

    def test_pages_uses_correct_template(self):
        """URL namespace:name использует соответствующий шаблон."""
        pages_templates_names = {
            reverse('users:signup'): 'users/signup.html',
            reverse('users:login'): 'users/login.html',
            reverse('users:password_change'):
                'users/password_change_form.html',
            reverse('users:password_change_done'):
                'users/password_change_done.html',
            reverse('users:password_reset'):
                'users/password_reset_form.html',
            reverse('users:password_reset_done'):
                'users/password_reset_done.html',
            reverse('users:password_reset_confirm', args=['uidb64', 'token']):
                'users/password_reset_confirm.html',
            reverse('users:password_reset_complete'):
                'users/password_reset_complete.html',
        }
        for reverse_name, template in pages_templates_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_logout_page_use_correct_template(self):
        """logout URL namespace:name использует соответствующий шаблон."""
        response = self.authorized_client.get(reverse('users:logout'))
        self.assertTemplateUsed(response, 'users/logged_out.html')

    def test_post_create_show_correct_context(self):
        """Шаблон signup сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('users:signup'))
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.EmailField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
