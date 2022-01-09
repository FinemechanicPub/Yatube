from uuid import uuid4

from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class TestUserViews(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user('auth')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(user=self.user)

    def test_page_templates(self):
        """Представления используются правильные шаблоны"""
        templates = {
            'users:signup': 'users/signup.html',
            'users:login': 'users/login.html',
            'users:password_change': 'users/password_change_form.html',
            'users:password_change_done': 'users/password_change_done.html',
            'users:password_reset': 'users/password_reset_form.html',
            'users:password_reset_done': 'users/password_reset_done.html',
            'users:reset_confirm': 'users/password_reset_confirm.html',
            'users:reset_complete': 'users/password_reset_complete.html',
            # last in list as it logs out the client
            'users:logout': 'users/logged_out.html'
        }
        kwargs = {
            'users:reset_confirm': {'uidb64': uuid4().hex, 'token': 'token'}
        }
        for name, template in templates.items():
            # Extra variable to allow single-line assert
            response = self.authorized_client.get(
                reverse(name, kwargs=kwargs.get(name, None))
            )
            with self.subTest(view_name=name):
                self.assertTemplateUsed(response, template)


class TestContext(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user('auth')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(user=self.user)

    def test_signup(self):
        """Контекст страницы регистрации сформирован правильно"""
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.EmailField,
        }
        response = self.authorized_client.get(reverse('users:signup'))
        for field, expected_type in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected_type)
