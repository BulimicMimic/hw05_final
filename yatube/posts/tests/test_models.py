from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post, SHOW_POST_NAME

User = get_user_model()


class PostsModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_post_field_label(self):
        """verbose_name полей post совпадает с ожидаемым."""
        field_label = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_verbose in field_label.items():
            with self.subTest(field=field):
                verbose_name = Post._meta.get_field(field).verbose_name
                self.assertEqual(verbose_name, expected_verbose)

    def test_post_field_help_text(self):
        """help_text полей post совпадает с ожидаемым."""
        field_help_text = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_help_text in field_help_text.items():
            with self.subTest(field=field):
                help_text = Post._meta.get_field(field).help_text
                self.assertEqual(help_text, expected_help_text)

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostsModelTest.post
        group = PostsModelTest.group
        model_expected_str = {
            post: post.text[:SHOW_POST_NAME],
            group: group.title,
        }
        for model, expected_str in model_expected_str.items():
            with self.subTest(model=model):
                self.assertEqual(expected_str, str(model))
