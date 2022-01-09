from http import HTTPStatus

from django.test import TestCase, Client
from django.contrib import auth
from django.urls import reverse

from ..models import User, Post, Group

USERNAME_AUTHOR = 'author_user'
USERNAME_SILENT = 'silent_user'
GROUP = {'title': 'Test group 1', 'slug': 'test_group1'}
POST = {'text': 'Test post'}
INDEX_URL = reverse('posts:index')
FOLLOW_URL = reverse('posts:follow_index')
GROUP_URL = reverse('posts:group_list', args=(GROUP['slug'],))
PROFILE_URL = reverse('posts:profile', args=(USERNAME_AUTHOR,))
POST_CREATE_URL = reverse('posts:post_create')
NONEXISTENT_PAGE_URL = '/unexisting_page/'
NONEXISTENT_GROUP_URL = reverse('posts:group_list', args=('nonexistent',))
NONEXISTENT_USER_URL = reverse('posts:profile', args=('nonexistent_user',))
LOGIN_PAGE_URL = reverse('users:login')
LOGIN_AND_POST_CREATE_URL = f'{LOGIN_PAGE_URL}?next={POST_CREATE_URL}'
LOGIN_AND_FOLLOW_URL = f'{LOGIN_PAGE_URL}?next={FOLLOW_URL}'


class URLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(USERNAME_AUTHOR)
        cls.silent_user = User.objects.create_user(USERNAME_SILENT)
        cls.group = Group.objects.create(**GROUP)
        cls.post_with_group = Post.objects.create(
            author=cls.author_user,
            group=cls.group,
            **POST
        )
        cls.POST_URL = reverse(
            'posts:post_detail', args=(cls.post_with_group.pk,)
        )
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit', args=(cls.post_with_group.pk,)
        )
        cls.LOGIN_AND_POST_EDIT_URL = (
            f'{LOGIN_PAGE_URL}?next={cls.POST_EDIT_URL}'
        )
        cls.SUBSCRIBE_URL = reverse(
            'posts:profile_follow', args=(cls.author_user,)
        )
        cls.UNSUBSCRIBE_URL = reverse(
            'posts:profile_unfollow', args=(cls.author_user,)
        )

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(user=self.author_user)
        self.silent_client = Client()
        self.silent_client.force_login(user=self.silent_user)

    def test_response_code(self):
        """Сервер возвращает правильный код ответа"""
        cases = [
            [INDEX_URL, self.guest_client, HTTPStatus.OK],
            [GROUP_URL, self.guest_client, HTTPStatus.OK],
            [PROFILE_URL, self.guest_client, HTTPStatus.OK],
            [POST_CREATE_URL, self.guest_client, HTTPStatus.FOUND],
            [POST_CREATE_URL, self.author_client, HTTPStatus.OK],
            [self.POST_URL, self.guest_client, HTTPStatus.OK],
            [self.POST_EDIT_URL, self.guest_client, HTTPStatus.FOUND],
            [self.POST_EDIT_URL, self.silent_client, HTTPStatus.FOUND],
            [self.POST_EDIT_URL, self.author_client, HTTPStatus.OK],
            [NONEXISTENT_PAGE_URL, self.guest_client, HTTPStatus.NOT_FOUND],
            [NONEXISTENT_GROUP_URL, self.guest_client, HTTPStatus.NOT_FOUND],
            [NONEXISTENT_USER_URL, self.guest_client, HTTPStatus.NOT_FOUND],
            [FOLLOW_URL, self.guest_client, HTTPStatus.FOUND],
            [FOLLOW_URL, self.author_client, HTTPStatus.OK],
            [self.SUBSCRIBE_URL, self.guest_client, HTTPStatus.FOUND],
            [self.SUBSCRIBE_URL, self.silent_client, HTTPStatus.FOUND],
            [self.UNSUBSCRIBE_URL, self.guest_client, HTTPStatus.FOUND],
            [self.UNSUBSCRIBE_URL, self.silent_client, HTTPStatus.FOUND]
        ]
        for url, client, expected_status in cases:
            with self.subTest(url=url, user=auth.get_user(client).username):
                self.assertEqual(client.get(url).status_code, expected_status)

    def test_redirection(self):
        """Сервер перенаправляет по правильному адресу"""
        cases = [
            [POST_CREATE_URL, self.guest_client, LOGIN_AND_POST_CREATE_URL],
            [
                self.POST_EDIT_URL,
                self.guest_client,
                self.LOGIN_AND_POST_EDIT_URL
            ],
            [self.POST_EDIT_URL, self.silent_client, self.POST_URL],
            [FOLLOW_URL, self.guest_client, LOGIN_AND_FOLLOW_URL]
        ]
        for url, client, redirection in cases:
            with self.subTest(url=url, user=auth.get_user(client).username):
                self.assertRedirects(client.get(url), redirection)

    def test_page_templates(self):
        """Страницы используют правильные шаблоны"""
        expected_templates = {
            INDEX_URL: 'posts/index.html',
            FOLLOW_URL: 'posts/follow.html',
            self.POST_URL: 'posts/post_detail.html',
            GROUP_URL: 'posts/group_list.html',
            PROFILE_URL: 'posts/profile.html',
            self.POST_EDIT_URL: 'posts/create_post.html',
            POST_CREATE_URL: 'posts/create_post.html',
            NONEXISTENT_PAGE_URL: 'core/404.html'
        }
        for url, template in expected_templates.items():
            with self.subTest(url=url):
                self.assertTemplateUsed(self.author_client.get(url), template)
