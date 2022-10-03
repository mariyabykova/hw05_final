from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django import forms

User = get_user_model()


class UserPagesTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_available_pages_use_correct_templates(self):
        templates_pages_names = {
            'users/login.html': reverse('users:login'),
            'users/signup.html': reverse('users:signup'),
            'users/logged_out.html': reverse('users:logout'),
            'users/password_reset_form.html': reverse(
                'users:password_reset_form'
            ),
            'users/password_reset_done.html': reverse(
                'users:password_reset_done'
            ),
            'users/password_reset_complete.html': reverse(
                'users:password_reset_complete'
            ),
            'users/password_reset_confirm.html': (
                reverse('password_reset_confirm', kwargs={
                        'uidb64': 'uidb64', 'token': 'token'}))
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_password_change_pages_use_correct_templates(self):
        templates_pages_names = {
            'users/password_change_form.html': 'users:password_change_form',
            'users/password_change_done.html': 'users:password_change_done',
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse(reverse_name))
                self.assertTemplateUsed(response, template)

    def test_create_post_shows_correct_context(self):
        """Шаблон signup.html сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('users:signup'))
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.CharField,
            'email': forms.EmailField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
