from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

User = get_user_model()


class UserURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_available_pages_urls_exist_at_desired_location(self):
        """Страницы доступны любому пользователю."""
        available_pages = [
            '/auth/login/',
            '/auth/signup/',
            '/auth/logout/',
            '/auth/password_reset/',
            '/auth/password_reset/done/',
            '/auth/reset/<uidb64>/<token>/',
            '/auth/reset/done/',
        ]
        for page in available_pages:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_password_change_pages_urls_exist_at_desire_location(self):
        """Страницы доступны авторизированному пользователю."""
        pages_for_authorized_user = [
            '/auth/password_change/',
            '/auth/password_change/done/',
        ]
        for page in pages_for_authorized_user:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_not_authorized_user_redirects_on_auth_login(self):
        """Страницы перенаправляют неавторизированного
        пользователя на страницу поста.
        """
        change_redirect_address = '/auth/login/?next=/auth/password_change/'
        doneredirect_address = '/auth/login/?next=/auth/password_change/done/'
        pages_for_authorized_user = {
            '/auth/password_change/': change_redirect_address,
            '/auth/password_change/done/': doneredirect_address
        }
        for address, redirect_address in pages_for_authorized_user.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertRedirects(response, redirect_address)

    def test_available_urls_use_correct_template(self):
        """URL-адреса страниц, доступных любому пользователю,
        используют соответствующие шаблоны."""
        templates_url_names = {
            '/auth/login/': 'users/login.html',
            '/auth/signup/': 'users/signup.html',
            '/auth/logout/': 'users/logged_out.html',
            '/auth/password_reset/': 'users/password_reset_form.html',
            '/auth/password_reset/done/': 'users/password_reset_done.html',
            '/auth/reset/<uidb64>/<token>/': (
                'users/password_reset_confirm.html'
            ),
            '/auth/reset/done/': 'users/password_reset_complete.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_password_change_pages_use_correct_template(self):
        """URL-адреса страниц, доступных авторизированному пользователю,
        используют соответствующие шаблоны."""
        templates_url_names = {
            '/auth/password_change/': 'users/password_change_form.html',
            '/auth/password_change/done/': 'users/password_change_done.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
