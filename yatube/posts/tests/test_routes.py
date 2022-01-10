from django.test import TestCase
from django.urls import reverse

from ..urls import app_name


class TestPostRouting(TestCase):

    def test_routes(self):
        """Пути приложения вычисляются правильно"""
        POST_ID = 5
        SLUG = 'slug'
        USERNAME = 'username'
        url_routes = {
            '/': ('index', ()),
            f'/group/{SLUG}/': ('group_list', (SLUG,)),
            f'/profile/{USERNAME}/': ('profile', (USERNAME,)),
            f'/posts/{POST_ID}/': ('post_detail', (POST_ID,)),
            f'/posts/{POST_ID}/edit/': ('post_edit', (POST_ID,)),
            f'/posts/{POST_ID}/comment/': ('add_comment', (POST_ID,)),
            '/create/': ('post_create', ()),
            '/follow/': ('follow_index', ()),
            f'/profile/{USERNAME}/follow/': ('profile_follow', (USERNAME,)),
            f'/profile/{USERNAME}/unfollow/': ('profile_unfollow', (USERNAME,))
        }
        for url, (name, args) in url_routes.items():
            route = f'{app_name}:{name}'
            with self.subTest(route=route):
                self.assertEqual(url, reverse(route, args=args))
