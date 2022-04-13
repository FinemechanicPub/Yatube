from unittest import skip

from django.test import TestCase, Client
from django.contrib import auth

from ..models import User, Post, Group

# @skip("Это был исследовательский тест")
class TestTest(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        print('\nЗапуск setUpClass')
        cls.method_user = User.objects.create_user(username='method_user')
        Post.objects.create(text='Добавлено в setUpClass', author=cls.method_user)
        cls.class_user = User.objects.create_user(username='class_user')
        cls.class_client = Client()
        cls.class_client.force_login(user=cls.class_user)
        cls.list = ['Добавлено в setUpClass']
        print('Завершение setUpClass')
        
    def setUp(self):
    	print('\nЗапуск setUp')
    	Post.objects.create(text='Добавлено в setUp', author=self.method_user)
    	self.list.append('Добавлено в setUp')
    	self.client = Client()
    	self.client.force_login(user=self.method_user)
    	print('Завершение setUp')

    def print_info(self):    	
        print('database content:')
        for post in Post.objects.all():
            print(post.text)
        print('list content:')
        for item in self.list:
            print(item)

    def print_user(self, client):
        user = auth.get_user(client)
        client_type = 'setUpClass' if client is self.class_client else 'setUp'
        print(
            f'client from {client_type} is logged in? '
            f'{user.is_authenticated}'
        )

    def test1(self):
        Post.objects.create(text='Добавлено в test1', author=self.method_user)
        self.list.append('Добавлено в test1')
        print('\nЗапуск test1')
        self.print_info()
        self.print_user(self.client)
        print('Клиент из setUp выходит из сервера')
        self.client.logout()
        self.print_user(self.client)
        self.print_user(self.class_client)
        print('Клиент из setUpClass выходит из сервера')
        self.class_client.logout()
        self.print_user(self.class_client)
        print('Конец test1')

    def test2(self):
        Post.objects.create(text='Добавлено в test2', author=self.method_user)
        self.list.append('Добавлено в test2')
        print('\nЗапуск test2')
        self.print_info()
        self.print_user(self.client)
        print('Клиент из setUp выходит из сервера')
        self.client.logout()
        self.print_user(self.client)
        self.print_user(self.class_client)
        print('Клиент из setUpClass выходит из сервера')
        self.class_client.logout()
        self.print_user(self.class_client)       
        print('Конец test2')

