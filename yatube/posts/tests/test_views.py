import shutil
import tempfile

from math import ceil

from django.contrib.auth import get_user_model
from django.core.cache import cache, caches
from django.core.cache.backends import locmem
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Group, Post, Follow
from ..views import POST_DISPLAY

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

LIST_LENGTH = 13
POSTS_TEXT = [f'Тестовый пост {x}' for x in range(LIST_LENGTH)]

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Тестовый автор')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.second_group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug_2',
            description='Тестовое описание 2',
        )
        cls.uploaded_gif = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.posts = []
        for text in POSTS_TEXT:
            cls.posts.append(Post.objects.create(
                author=cls.user,
                group=cls.group,
                text=text,
                image=cls.uploaded_gif,
            )
            )
        cls.INDEX_URL = reverse('posts:index')
        cls.GROUP_LIST_URL = reverse('posts:group_list',
                                     kwargs={'slug': cls.group.slug},
                                     )
        cls.PROFILE_URL = reverse('posts:profile',
                                  kwargs={'username': cls.posts[0].author},
                                  )
        cls.POST_DETAIL_URL = reverse('posts:post_detail',
                                      kwargs={'post_id': cls.posts[0].id},
                                      )
        cls.POST_EDIT_URL = reverse('posts:post_edit',
                                    kwargs={'post_id': cls.posts[0].id},
                                    )
        cls.CREATE_URL = reverse('posts:post_create')
        cls.FOLLOW_URL = reverse('posts:follow_index')

        cls.INDEX_HTML = 'posts/index.html'
        cls.GROUP_LIST_HTML = 'posts/group_list.html'
        cls.PROFILE_HTML = 'posts/profile.html'
        cls.POST_DETAIL_HTML = 'posts/post_detail.html'
        cls.CREATE_POST_HTML = 'posts/create_post.html'

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.post_author_client = Client()
        self.post_author_client.force_login(PostsPagesTests.user)

        self.follower_1 = User.objects.create_user(username='Подписчик 1')
        self.follower_1_client = Client()
        self.follower_1_client.force_login(self.follower_1)

        self.follower_2 = User.objects.create_user(username='Подписчик 2')
        self.follower_2_client = Client()
        self.follower_2_client.force_login(self.follower_2)

    def tearDown(self):
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL namespace:name использует соответствующий шаблон."""
        pages_templates_names = {
            PostsPagesTests.INDEX_URL: PostsPagesTests.INDEX_HTML,
            PostsPagesTests.GROUP_LIST_URL: PostsPagesTests.GROUP_LIST_HTML,
            PostsPagesTests.PROFILE_URL: PostsPagesTests.PROFILE_HTML,
            PostsPagesTests.POST_DETAIL_URL: PostsPagesTests.POST_DETAIL_HTML,
            PostsPagesTests.POST_EDIT_URL: PostsPagesTests.CREATE_POST_HTML,
            PostsPagesTests.CREATE_URL: PostsPagesTests.CREATE_POST_HTML,
        }
        for reverse_name, template in pages_templates_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.post_author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.post_author_client.get(PostsPagesTests.INDEX_URL)
        first_post_object = response.context['page_obj'][0]
        post_text_0 = first_post_object.text
        post_author_0 = first_post_object.author
        post_group_0 = first_post_object.group
        post_image_0 = first_post_object.image
        self.assertEqual(post_text_0, PostsPagesTests.posts[-1].text)
        self.assertEqual(post_author_0, PostsPagesTests.posts[-1].author)
        self.assertEqual(post_group_0, PostsPagesTests.posts[-1].group)
        self.assertEqual(post_image_0,
                         PostsPagesTests.posts[-1].image,
                         )

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = (self.post_author_client.
                    get(PostsPagesTests.GROUP_LIST_URL))
        group_object = response.context['group']
        group_title = group_object.title
        group_slug = group_object.slug
        group_description = group_object.description
        self.assertEqual(group_title, 'Тестовая группа')
        self.assertEqual(group_slug, 'test_slug')
        self.assertEqual(group_description, 'Тестовое описание')

        first_post_object = response.context['page_obj'][0]
        post_text_0 = first_post_object.text
        post_author_0 = first_post_object.author
        post_group_0 = first_post_object.group
        post_image_0 = first_post_object.image
        self.assertEqual(post_text_0, PostsPagesTests.posts[-1].text)
        self.assertEqual(post_author_0, PostsPagesTests.posts[-1].author)
        self.assertEqual(post_group_0, PostsPagesTests.posts[-1].group)
        self.assertEqual(post_image_0,
                         PostsPagesTests.posts[-1].image,
                         )


    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (self.post_author_client.
                    get(PostsPagesTests.PROFILE_URL))
        author_object = response.context['author']
        author_username = author_object.username
        self.assertEqual(author_username, 'Тестовый автор')

        first_post_object = response.context['page_obj'][0]
        post_text_0 = first_post_object.text
        post_author_0 = first_post_object.author
        post_group_0 = first_post_object.group
        post_image_0 = first_post_object.image
        self.assertEqual(post_text_0, PostsPagesTests.posts[-1].text)
        self.assertEqual(post_author_0, PostsPagesTests.posts[-1].author)
        self.assertEqual(post_group_0, PostsPagesTests.posts[-1].group)
        self.assertEqual(post_image_0,
                         PostsPagesTests.posts[-1].image,
                         )

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.post_author_client.
                    get(PostsPagesTests.POST_DETAIL_URL))
        self.assertEqual(response.context.get('post').text,
                         PostsPagesTests.posts[0].text,
                         )
        self.assertEqual(response.context.get('post').author,
                         PostsPagesTests.user,
                         )
        self.assertEqual(response.context.get('post').group,
                         PostsPagesTests.group,
                         )
        self.assertEqual(response.context.get('post').image,
                         PostsPagesTests.posts[0].image,
                         )

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = (self.post_author_client.get(PostsPagesTests.POST_EDIT_URL))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        self.assertIn('form', response.context)
        self.assertIn('is_edit', response.context)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.post_author_client.get(PostsPagesTests.CREATE_URL)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        self.assertIn('form', response.context)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_goes_into_correct_group(self):
        """Пост не попал в группу, для которой не был предназначен."""
        response = (self.post_author_client.
                    get(PostsPagesTests.GROUP_LIST_URL))
        first_post_object = response.context['page_obj'][0]
        post_group_0 = first_post_object.group
        self.assertEqual(post_group_0, PostsPagesTests.group)
        self.assertNotEqual(post_group_0, PostsPagesTests.second_group)

    def test_pages_contains_expected_records(self):
        """Записи на страницах соответствуют содержанию и количеству."""
        num_pages = ceil(len(PostsPagesTests.posts) / POST_DISPLAY)
        for page_number in range(1, num_pages):
            urls = [
                PostsPagesTests.INDEX_URL + f'?page={page_number}',
                PostsPagesTests.GROUP_LIST_URL + f'?page={page_number}',
                PostsPagesTests.PROFILE_URL + f'?page={page_number}',
            ]
            for reverse_number in urls:
                with self.subTest(page_number=page_number,
                                  reverse_name=reverse_number,
                                  ):
                    response = self.post_author_client.get(reverse_number)
                    page_obj = response.context.get('page_obj')
                    page_number = page_obj.number
                    last_page = page_number == num_pages
                    page_length = (POST_DISPLAY if not last_page
                                   else len(PostsPagesTests.posts)
                                   - (page_number - 1) * POST_DISPLAY)
                    self.assertEqual(len(response.context['page_obj']),
                                     page_length,
                                     )
                    object_list = page_obj.object_list
                    for post_number, post_obj in enumerate(object_list):
                        num_element = (post_number
                                       + (page_number - 1) * POST_DISPLAY)
                        inverse_num = (len(PostsPagesTests.posts)
                                       - num_element - 1)
                        self.assertEqual(PostsPagesTests.posts[inverse_num],
                                         post_obj,
                                         )

    def test_index_cache(self):
        """Кеш на главной странице сохраняется."""
        post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
        )
        response_1 = self.post_author_client.get(PostsPagesTests.INDEX_URL)
        post.delete()
        response_2 = self.post_author_client.get(PostsPagesTests.INDEX_URL)
        self.assertEqual(response_1.content,
                         response_2.content)
        cache.clear()
        response_3 = self.post_author_client.get(PostsPagesTests.INDEX_URL)
        self.assertNotEqual(response_1.content,
                            response_3.content)

    def test_follow_index_page_show_correct_context(self):
        """Шаблон follow_index сформирован с правильным контекстом."""
        Follow.objects.create(
            user=self.follower_1,
            author=self.user,
        )
        post = Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            group=PostsPagesTests.group,
            image=PostsPagesTests.uploaded_gif,
        )
        response = self.follower_1_client.get(PostsPagesTests.FOLLOW_URL)
        first_post_object = response.context['page_obj'][0]
        post_text_0 = first_post_object.text
        post_author_0 = first_post_object.author
        post_group_0 = first_post_object.group
        post_image_0 = first_post_object.image
        self.assertEqual(post_text_0, post.text)
        self.assertEqual(post_author_0, post.author)
        self.assertEqual(post_group_0, post.group)
        self.assertEqual(post_image_0, post.image)

        response = self.follower_2_client.get(PostsPagesTests.FOLLOW_URL)
        self.assertEqual(len(response.context['page_obj']), 0)

        post.delete()
