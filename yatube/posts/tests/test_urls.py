from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Тестовый автор')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.INDEX_URL = '/'
        cls.GROUP_LIST_URL = f'/group/{PostsURLTests.group.slug}/'
        cls.PROFILE_URL = f'/profile/{PostsURLTests.post.author}/'
        cls.POST_DETAIL_URL = f'/posts/{PostsURLTests.post.id}/'
        cls.POST_EDIT_URL = f'/posts/{PostsURLTests.post.id}/edit/'
        cls.CREATE_URL = '/create/'
        cls.UNEXISTING_URL = '/unexisting_page/'
        cls.ADD_COMMENT_URL = f'/posts/{PostsURLTests.post.id}/comment/'

        cls.INDEX_HTML = 'posts/index.html'
        cls.GROUP_LIST_HTML = 'posts/group_list.html'
        cls.PROFILE_HTML = 'posts/profile.html'
        cls.POST_DETAIL_HTML = 'posts/post_detail.html'
        cls.CREATE_POST_HTML = 'posts/create_post.html'
        cls.CUSTOM_404_HTML = 'core/404.html'

    def setUp(self):
        self.guest_client = Client()

        self.authorized_user = User.objects.create_user(username='Тестер')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.authorized_user)

        self.post_author_client = Client()
        self.post_author_client.force_login(PostsURLTests.user)

    def test_guest_client_accessableness_urls(self):
        """Страницы доступны любому пользователю."""
        urls = [
            PostsURLTests.INDEX_URL,
            PostsURLTests.GROUP_LIST_URL,
            PostsURLTests.PROFILE_URL,
            PostsURLTests.POST_DETAIL_URL,
        ]
        for address in urls:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_client_accessableness_urls(self):
        """Страницы доступна авторизованному пользователю."""
        urls = [
            PostsURLTests.POST_EDIT_URL,
            PostsURLTests.CREATE_URL,
        ]
        for address in urls:
            with self.subTest(address=address):
                response = self.post_author_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_url(self):
        """Запрос к несуществующей странице вернёт ошибку 404."""
        response = self.guest_client.get(PostsURLTests.UNEXISTING_URL)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_404_custom_template(self):
        """Страница 404 отдаёт кастомный шаблон."""
        response = self.post_author_client.get(PostsURLTests.UNEXISTING_URL)
        self.assertTemplateUsed(response, PostsURLTests.CUSTOM_404_HTML)

    def test_post_edit_url_redirect_anonymous_on_login(self):
        """Страница по адресу /posts/<int:post_id>/edit/ перенаправит
        пользователя, не являющегося автором записи, на страницу записи.
        """
        response = self.authorized_client.get(
            PostsURLTests.POST_EDIT_URL,
            follow=True,
        )
        self.assertRedirects(
            response, PostsURLTests.POST_DETAIL_URL,
        )

    def test_post_create_url_redirect_anonymous_on_login(self):
        """Страница по адресу /posts/create/ перенаправит
        анонимного пользователя на страницу логина.
        """
        response = self.guest_client.get(PostsURLTests.CREATE_URL, follow=True)
        self.assertRedirects(response, '/auth/login/?next=%2Fcreate%2F')

    def test_add_comment_url_redirect_anonymous_on_login(self):
        """Страница по адресу /posts/<int:post_id>/comment/ перенаправит
        анонимного пользователя на страницу логина.
        """
        response = self.guest_client.get(
            PostsURLTests.ADD_COMMENT_URL,
            follow=True,
        )
        self.assertRedirects(
            response, '/auth/login/?next=%2Fposts%2F1%2Fcomment%2F',
        )

    def test_correct_template_used_by_urls(self):
        """URL-адрес использует соответствующий шаблон."""
        url_templates_names = {
            PostsURLTests.INDEX_URL: PostsURLTests.INDEX_HTML,
            PostsURLTests.GROUP_LIST_URL: PostsURLTests.GROUP_LIST_HTML,
            PostsURLTests.PROFILE_URL: PostsURLTests.PROFILE_HTML,
            PostsURLTests.POST_DETAIL_URL: PostsURLTests.POST_DETAIL_HTML,
            PostsURLTests.POST_EDIT_URL: PostsURLTests.CREATE_POST_HTML,
            PostsURLTests.CREATE_URL: PostsURLTests.CREATE_POST_HTML,
        }
        for address, template in url_templates_names.items():
            with self.subTest(address=address):
                response = self.post_author_client.get(address)
                self.assertTemplateUsed(response, template)
