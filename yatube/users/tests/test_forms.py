from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse


User = get_user_model()


class UserFormTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_signup_form(self):
        """Валидная форма создает нового пользователя."""
        users_count = User.objects.count()
        form_data = {
            'first_name': 'Vasya',
            'last_name': 'Ivanov',
            'username': 'Vasya',
            'email': 'vasya@mail.ru',
            'password1': '1234567890asdfg',
            'password2': '1234567890asdfg',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(User.objects.count(), users_count + 1)
        self.assertTrue(
            User.objects.filter(
                username='Vasya'
            ).exists()
        )
