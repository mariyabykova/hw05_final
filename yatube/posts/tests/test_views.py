import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.cache import cache
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Group, Post, Comment, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        small_gif = (            
             b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded,
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание 2',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        user_author = PostPagesTests.user
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(user_author)

    def assert_form_fields(self, response):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_pages_use_correct_templates(self):
        """Во view-функциях используются правильные HTML-шаблоны."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={
                    'slug': self.group.slug
                    }): 'posts/group_list.html',
            reverse('posts:profile', kwargs={
                    'username': self.post.author.username
                    }): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                    'post_id': self.post.id
                    }): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={
                    'post_id': self.post.id
                    }): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.context['page_obj'][0], self.post)
        self.assertEqual(
            response.context['page_obj'][0].image, self.post.image
        )

    def test_group_list_shows_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = (self.authorized_client.get(reverse(
                    'posts:group_list', kwargs={'slug': self.group.slug})))
        self.assertEqual(response.context['page_obj'][0], self.post)
        self.assertEqual(
            response.context['page_obj'][0].image, self.post.image
        )
        self.assertEqual(response.context['group'], self.group)

    def test_profile_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (self.authorized_client.get(reverse('posts:profile',
                    kwargs={'username': self.post.author.username})))
        self.assertEqual(response.context['page_obj'][0], self.post)
        self.assertEqual(
            response.context['page_obj'][0].image, self.post.image
        )
        self.assertEqual(response.context['author'], self.post.author)

    def test_post_detail_shows_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id})))
        self.assertEqual(response.context['post'], self.post)
        self.assertEqual(response.context['post'].image, self.post.image)

    def test_create_post_shows_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assert_form_fields(response)

    def test_post_edit_shows_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        self.assert_form_fields(response)
        self.assertEqual(response.context['post'], self.post)
        self.assertEqual(response.context.get('is_edit'), True)

    def test_new_post_appears_at_pages(self):
        """Если при создании поста указывается группа,
        этот пост появляется на страницах
        index, group_list, profile.
        """
        new_post = Post.objects.create(
            author=PostPagesTests.user,
            text='Новый пост',
            group=self.group,
        )
        reverse_adresses = [
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.post.author.username}),
            reverse('posts:index')
        ]
        for reverse_name in reverse_adresses:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client_author.get(reverse_name)
                self.assertIn(new_post, response.context['page_obj'])

    def test_new_post_does_not_appear_at_another_group_list(self):
        """Если при создании поста указывается группа,
        этот пост не появляется на странице той группы,
        к которой он не относится.
        """
        new_post = Post.objects.create(
            author=PostPagesTests.user,
            text='Новый пост',
            group=self.group,
        )
        response = (self.authorized_client.get(reverse('posts:group_list',
                    kwargs={'slug': self.group_2.slug})))
        self.assertNotIn(new_post, response.context['page_obj'])

    def test_new_comment_appears_at_post_detail(self):
        """Если создаётся комментарий,
        то он появлется на странице post_detail.
        """
        new_comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Тестовый комментарий'
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail',
            kwargs={'post_id': self.post.id})
        )
        self.assertIn(new_comment, response.context['comments'])

    def test_cache_works_correctly(self):
        """Кеширование главной страницы работает корректно."""
        new_post = Post.objects.create(
            author=PostPagesTests.user,
            text='Новый пост',
            group=self.group,
        )
        response = self.authorized_client.get(reverse('posts:index'))
        initial_content = response.content
        new_post.delete()
        response = self.authorized_client.get(reverse('posts:index'))
        new_content = response.content
        self.assertEqual(initial_content, new_content)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        after_cache_clear_content = response.content
        self.assertNotEqual(initial_content, after_cache_clear_content)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for post_number in range(settings.TEST_PAGINATOR_NUMBER):
            cls.post = Post.objects.create(
                author=cls.user,
                text='Тестовый пост',
                group=cls.group,
            )

    def setUp(self):
        self.guest_client = Client()

    def test_first_page_contains_expected_number_of_records(self):
        """Паджинатор на первой странице работает правильно."""
        reverse_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': (reverse('posts:group_list',
                                      kwargs={'slug': self.group.slug})),
            'posts/profile.html': (reverse('posts:profile', kwargs={
                                   'username': self.post.author.username})),
        }
        for page, reverse_name in reverse_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), settings.POSTS_PER_PAGE
                )

    def test_second_page_contains_expected_number_of_records(self):
        """Паджинатор на второй странице работает правильно."""
        reverse_pages_names = {
            'posts/index.html': (reverse('posts:index') + '?page=2'),
            'posts/group_list.html': (
                reverse('posts:group_list', kwargs={
                        'slug': self.group.slug}) + '?page=2'),
            'posts/profile.html': (reverse('posts:profile', kwargs={
                                   'username': f'{self.post.author}'})
                                   + '?page=2'),
        }
        for page, reverse_name in reverse_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(len(
                    response.context['page_obj']), settings.TEST_SECOND_PAGE
                )


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.author = User.objects.create_user(username='author')
        cls.client = User.objects.create_user(username='client')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )
    
    def setUp(self):
        self.guest_client = Client()
        user_author = FollowTests.author
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(user_author)
        user_follower = FollowTests.user
        self.authorized_client_follower = Client()
        self.authorized_client_follower.force_login(user_follower)
        user_follower = FollowTests.client
        self.authorized_client = Client()
        self.authorized_client.force_login(user_follower)
    
    def test_authorized_user_can_follow_author(self):
        """Авторизированный пользователь может подписаться на автора."""
        count = Follow.objects.count()
        self.authorized_client_follower.get(reverse('posts:profile_follow', kwargs={'username': self.author.username}))
        self.assertTrue(Follow.objects.filter(user=self.user, author=self.author).exists())
        self.assertEqual(Follow.objects.count(), count + 1)

    def test_authorized_user_can_unfollow_author(self):
        """Авторизированный пользователь может отписаться от автора."""
        Follow.objects.create(user=self.user, author=self.author)
        self.authorized_client_follower.get(reverse('posts:profile_unfollow', kwargs={'username': self.author.username}))
        self.assertFalse(Follow.objects.filter(user=self.user, author=self.author).exists())

    def test_guest_client_cannot_follow_author(self):
        """Неавторизированный пользователь не может 
        подписаться на автора.
        """
        count = Follow.objects.count()
        self.guest_client.get(reverse('posts:profile_follow', kwargs={'username': self.author.username}))
        self.assertEqual(Follow.objects.count(), count)

    def test_new_posts_appear_at_page_of_followers(self):
        """Если пользователь подписывается на автора,
        посты автора появляются на странице пользователя follow_index."""
        Follow.objects.create(
            user=self.user,
            author=self.author
        )
        response = self.authorized_client_follower.get(reverse('posts:follow_index'))
        self.assertEqual(response.context['page_obj'][0], self.post)
        self.assertTrue(Follow.objects.filter(user=self.user, author=self.author).exists())

    def test_new_posts_are_not_on_page_of_not_follower(self):
        """Посты автора не появляются на странице follow_index
        пользователя, который не подписан на автора."""
        Follow.objects.create(
            user=self.user,
            author=self.author
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotIn(self.post, response.context['page_obj'])
        