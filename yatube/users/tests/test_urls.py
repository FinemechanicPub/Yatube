from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus

User = get_user_model()


class UrlTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user('test_user')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(user=self.user)

    def test_guest_access(self):
        """Пользователь без регистрации получает правильную страницу"""
        login_url = '/auth/login/?next='
        redirections = {
            '/auth/logout/': '',
            '/auth/signup/': '',
            '/auth/login/': '',
            '/auth/password_change/': login_url + '/auth/password_change/',
            '/auth/password_change/done/':
                login_url + '/auth/password_change/done/',
            '/auth/password_reset/': '',
            '/auth/password_reset/done/': '',
            '/auth/reset/<uidb64>/<token>/': '',
            '/auth/reset/done/': ''
        }
        for url, redirection in redirections.items():
            response = self.guest_client.get(url)
            with self.subTest(url=url):
                if redirection:
                    self.assertRedirects(response, redirection)
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_user_access(self):
        """Зарегистрированный пользователь получает правильную страницу"""
        redirections = {
            '/auth/signup/': '',
            '/auth/login/': '',
            '/auth/password_change/': '',
            '/auth/password_change/done/': '',
            '/auth/password_reset/': '',
            '/auth/password_reset/done/': '',
            '/auth/reset/<uidb64>/<token>/': '',
            '/auth/reset/done/': '',
            '/auth/logout/': ''  # last in list as it logs out the client
        }
        for url, redirection in redirections.items():
            # Extra variable to allow single-line assert
            response = self.authorized_client.get(url)
            with self.subTest(url=url):
                if redirection:
                    self.assertRedirects(response, redirection)
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_templates(self):
        """Для страниц используются правильные шаблоны"""
        templates = {
            '/auth/signup/': 'users/signup.html',
            '/auth/login/': 'users/login.html',
            '/auth/password_change/': 'users/password_change_form.html',
            '/auth/password_change/done/': 'users/password_change_done.html',
            '/auth/password_reset/': 'users/password_reset_form.html',
            '/auth/password_reset/done/': 'users/password_reset_done.html',
            '/auth/reset/<uidb64>/<token>/':
                'users/password_reset_confirm.html',
            '/auth/reset/done/': 'users/password_reset_complete.html',
            # last in list as it logs out the client
            '/auth/logout/': 'users/logged_out.html'
        }
        for url, template in templates.items():
            # Extra variable to allow single-line assert
            response = self.authorized_client.get(url)
            with self.subTest(url=url):
                self.assertTemplateUsed(response, template)
