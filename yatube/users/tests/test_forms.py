from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class TestUserForm(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_user_create(self):
        password = User.objects.make_random_password()
        form_data = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'username': 'test_username',
            'email': 'example@example.com',
            'password1': password,
            'password2': password
        }
        # Extra variable to allow single-line assert
        response = self.guest_client.post(
            reverse('users:signup'), form_data
        )
        self.assertRedirects(response, reverse('posts:index'))
        self.assertTrue(
            User.objects.filter(
                first_name=form_data['first_name'],
                last_name=form_data['last_name'],
                username=form_data['username'],
                email=form_data['email']
            ).exists()
        )
