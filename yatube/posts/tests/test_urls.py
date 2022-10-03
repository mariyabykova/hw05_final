from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        user_author = PostURLTests.user
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(user_author)

    def test_available_pages_urls_exist_at_desired_location(self):
        """Страницы доступны любому пользователю."""
        available_pages = [
            '/',
            f'/profile/{self.post.author}/',
            f'/posts/{self.post.id}/',
            f'/group/{self.group.slug}/',
        ]
        for page in available_pages:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_exists_at_desired_location(self):
        """Страница '/create/' доступна авторизированному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_exists_at_desired_location(self):
        """Страница 'posts/<post_id>/edit/' доступна автору поста."""
        edit_address = f'/posts/{self.post.id}/edit/'
        response = self.authorized_client_author.get(edit_address)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_url_redirect_anonimous_on_auth_login(self):
        """Страницы 'create' и 'posts/<post_id>/edit/' перенаправляют
        анонимного пользователя на страницу логина.
        """
        pages_for_authorized_user = {
            '/create/': '/auth/login/?next=/create/',
            f'/posts/{self.post.id}/edit/': (
                f'/auth/login/?next=/posts/{self.post.id}/edit/'
            ),
        }
        for address, redirect_address in pages_for_authorized_user.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, redirect_address)

    def test_not_user_author_redirects_on_post_detail(self):
        """Страница 'post_edit' перенаправляет не автора поста
        на страницу поста.
        """
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_unexisting_pages_url_return_404_code(self):
        """Запрос к несуществующим страницам вернёт ошибку 404."""
        unexisting_pages = [
            '/unexising_page/',
            '/group/unexisting-slug/',
            '/posts/748/',
            '/profile/unexisting_author/',
        ]
        for page in unexisting_pages:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client_author.get(address)
                self.assertTemplateUsed(response, template)
