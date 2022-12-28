import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Group, Post, Comment, Follow

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.new_group = Group.objects.create(
            title='Новая тестовая группа',
            slug='new_test_slug',
            description='Новое тестовое описание',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()

        self.authorized_user = User.objects.create_user(username='Тестер')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.authorized_user)

        self.user = User.objects.create_user(username='Тестовый автор')
        self.post_author_client = Client()
        self.post_author_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        uploaded_gif = SimpleUploadedFile(
            name='create_small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': PostsFormTests.group.id,
            'image': uploaded_gif,
        }
        self.post_author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.last()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.image.name,
                         f'posts/{uploaded_gif.name}',
                         )

    def test_create_post_by_guest_client(self):
        """Не авторизованный пользователь не может создать запись в Post."""
        uploaded_gif = SimpleUploadedFile(
            name='not_create_small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': PostsFormTests.group.id,
            'image': uploaded_gif,
        }
        self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), 0)
        self.assertFalse(Post.objects.filter(text='Тестовый текст').exists())
        self.assertFalse(Post.objects.filter(group=PostsFormTests.group.id).
                         exists())
        self.assertFalse(Post.objects.filter(author=self.user.id).exists())
        self.assertFalse(Post.objects.filter(
            image=f'posts/{uploaded_gif.name}'
        ).exists())

    def test_add_comment(self):
        """Валидная форма создает комментарий."""
        uploaded_gif = SimpleUploadedFile(
            name='comment_small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            group=PostsFormTests.group,
            image=uploaded_gif,
        )
        form_data = {
            'text': 'Тестовый текст',
        }
        self.post_author_client.post(
            reverse('posts:add_comment',
                    args=[post.id],
                    ),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.last()
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, post)

    def test_add_comment_by_guest_client(self):
        """Не авторизованный пользователь не может оставить комментарий."""
        uploaded_gif = SimpleUploadedFile(
            name='not_comment_small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            group=PostsFormTests.group,
            image=uploaded_gif,
        )
        form_data = {
            'text': 'Тестовый текст',
        }
        self.guest_client.post(
            reverse('posts:add_comment',
                    args=[post.id],
                    ),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), 0)
        self.assertFalse(Comment.objects.filter(text='Тестовый текст').
                         exists())
        self.assertFalse(Comment.objects.filter(author=self.user.id).exists())
        self.assertFalse(Comment.objects.filter(post=post.id).
                         exists())

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        uploaded_gif = SimpleUploadedFile(
            name='edit_small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        new_uploaded_gif = SimpleUploadedFile(
            name='new_edit_small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        post = Post.objects.create(
            author=self.user,
            text='Старый пост',
            group=PostsFormTests.group,
            image=uploaded_gif,
        )
        form_data = {
            'text': 'Отредактированный пост',
            'group': PostsFormTests.new_group.id,
            'image': new_uploaded_gif,
        }
        self.post_author_client.post(
            reverse('posts:post_edit',
                    args=[post.id],
                    ),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.filter(group=PostsFormTests.group.id
                                             ).count(), 0)
        new_post = Post.objects.last()
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.group.id, form_data['group'])
        self.assertEqual(new_post.author, self.user)
        self.assertEqual(new_post.image.name,
                         f'posts/{new_uploaded_gif.name}',
                         )

    def test_profile_follow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок.
        """
        self.authorized_client.post(
            reverse('posts:profile_follow', args=[self.user]))
        self.assertEqual(Follow.objects.count(), 1)
        follow = Follow.objects.last()
        self.assertEqual(follow.user, self.authorized_user)
        self.assertEqual(follow.author, self.user)

        self.authorized_client.post(
            reverse('posts:profile_unfollow', args=[self.user]))
        self.assertEqual(Follow.objects.count(), 0)
        self.assertFalse(Follow.objects.filter(user=self.authorized_user.id)
                         .exists())
        self.assertFalse(Follow.objects.filter(author=self.user.id).exists())
