import shutil
import tempfile

from django.conf import settings
from django.contrib import auth
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import User, Post, Group, Follow

TEMP_MEDIA_ROOT_FORMS = tempfile.mkdtemp(dir=settings.BASE_DIR)
URL_WITH_PAGE = '{url}?page={page}'
POSTS_ON_PAGE_LIMIT = settings.POSTS_PER_PAGE
POST_NUMBER = int(POSTS_ON_PAGE_LIMIT * 1.5)
LAST_PAGE = POST_NUMBER // POSTS_ON_PAGE_LIMIT + 1
POSTS_ON_FIRST_PAGE = min(POST_NUMBER, POSTS_ON_PAGE_LIMIT)
POSTS_ON_LAST_PAGE = POST_NUMBER % POSTS_ON_PAGE_LIMIT
USERNAME_AUTHOR = 'author'
USERNAME_FOLLOWER = 'follower'
USERNAME_ANOTHER = 'another'
GROUP = {'title': 'Группа', 'slug': 'test_group', 'description': 'описание'}
GROUP_OTHER = {'title': 'Другая тестовая группа', 'slug': 'test_group_other'}
POST = {'text': 'Тестовый пост'}
POST_IN_OTHER_GROUP = {'text': 'Пост в другой группе'}
POST_NOT_IN_GROUP = {'text': 'Пост без группы'}
INDEX_URL = reverse('posts:index')
INDEX_LAST_PAGE_URL = URL_WITH_PAGE.format(url=INDEX_URL, page=LAST_PAGE)
FOLLOW_URL = reverse('posts:follow_index')
FOLLOW_LAST_PAGE_URL = URL_WITH_PAGE.format(url=FOLLOW_URL, page=LAST_PAGE)
GROUP_URL = reverse('posts:group_list', args=(GROUP['slug'],))
GROUP_LAST_PAGE_URL = URL_WITH_PAGE.format(url=GROUP_URL, page=LAST_PAGE)
GROUP_OTHER_URL = reverse('posts:group_list', args=(GROUP_OTHER['slug'],))
PROFILE_URL = reverse('posts:profile', args=(USERNAME_AUTHOR,))
PROFILE_LAST_PAGE_URL = URL_WITH_PAGE.format(url=PROFILE_URL, page=LAST_PAGE)
POST_CREATE_URL = reverse('posts:post_create')
AUTHOR_FOLLOW_URL = reverse('posts:profile_follow', args=(USERNAME_AUTHOR,))
ANOTHER_FOLLOW_URL = reverse('posts:profile_follow', args=(USERNAME_ANOTHER,))
ANOTHER_UNFOLLOW_URL = reverse(
    'posts:profile_unfollow', args=(USERNAME_ANOTHER,)
)
TEST_IMAGE = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


class TestPagination(TestCase):

    POST_WITH_GROUP = '{number} групповой пост'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(USERNAME_AUTHOR)
        cls.follower_user = User.objects.create_user(USERNAME_FOLLOWER)
        cls.author = Client()
        cls.author.force_login(user=cls.author_user)
        cls.follower = Client()
        cls.follower.force_login(user=cls.follower_user)
        cls.group = Group.objects.create(**GROUP)
        Post.objects.bulk_create([
            Post(
                text=cls.POST_WITH_GROUP.format(number=i),
                author=cls.author_user,
                group=cls.group
            ) for i in range(POST_NUMBER)
        ])
        Follow.objects.create(user=cls.follower_user, author=cls.author_user)

    def test_pagination(self):
        cases = [
            [INDEX_URL, self.author, POSTS_ON_FIRST_PAGE],
            [INDEX_LAST_PAGE_URL, self.author, POSTS_ON_LAST_PAGE],
            [GROUP_URL, self.author, POSTS_ON_FIRST_PAGE],
            [GROUP_LAST_PAGE_URL, self.author, POSTS_ON_LAST_PAGE],
            [PROFILE_URL, self.author, POSTS_ON_FIRST_PAGE],
            [PROFILE_LAST_PAGE_URL, self.author, POSTS_ON_LAST_PAGE],
            [FOLLOW_URL, self.author, 0],
            [FOLLOW_URL, self.follower, POSTS_ON_FIRST_PAGE],
            [FOLLOW_LAST_PAGE_URL, self.follower, POSTS_ON_LAST_PAGE]
        ]
        for url, client, expected_count in cases:
            with self.subTest(url=url, user=auth.get_user(client)):
                self.assertEqual(
                    len(client.get(url).context['page_obj']),
                    expected_count
                )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT_FORMS)
class TestPostData(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(USERNAME_AUTHOR)
        cls.follower_user = User.objects.create_user(USERNAME_FOLLOWER)
        cls.author = Client()
        cls.author.force_login(user=cls.author_user)
        cls.follower = Client()
        cls.follower.force_login(user=cls.follower_user)
        cls.group = Group.objects.create(**GROUP)
        cls.group_other = Group.objects.create(**GROUP_OTHER)
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=TEST_IMAGE,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.author_user,
            group=cls.group,
            image=cls.image,
            **POST
        )
        cls.POST_URL = reverse('posts:post_detail', args=(cls.post.pk,))
        Follow.objects.create(user=cls.follower_user, author=cls.author_user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT_FORMS, ignore_errors=True)

    def test_post_context(self):
        """Публикация передается с правильными данными"""
        cases = [
            [INDEX_URL, self.author],
            [GROUP_URL, self.author],
            [PROFILE_URL, self.author],
            [FOLLOW_URL, self.follower],
            [self.POST_URL, self.author]
        ]
        for url, client in cases:
            with self.subTest(url=url, user=auth.get_user(client)):
                response = client.get(url)
                if 'page_obj' in response.context:
                    page_obj = response.context['page_obj']
                    self.assertEqual(
                        len(page_obj), 1,
                        'В базе данных и на странице должна быть '
                        'ровно одна публикация'
                    )
                    post = page_obj[0]
                else:
                    post = response.context['post']
                self.assertEqual(post.pk, self.post.pk)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.image, self.post.image)

    def test_not_displayed(self):
        """Публикация не появляется на неправильных страницах"""
        cases = [
            [GROUP_OTHER_URL, self.author],
            [FOLLOW_URL, self.author]
        ]
        for url, client in cases:
            with self.subTest(url=url, user=auth.get_user(client)):
                self.assertNotIn(
                    self.post, client.get(url).context['page_obj']
                )

    def test_group_context(self):
        """Группа передается с правильными данными"""
        group = self.author.get(GROUP_URL).context['group']
        self.assertEqual(group.pk, self.group.pk)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.description, self.group.description)

    def test_profile_context(self):
        """На страницу профиля передается правильный автор"""
        user = self.author.get(PROFILE_URL).context['author']
        self.assertEqual(user, self.author_user)

    def test_cache(self):
        """Кэш главной страницы работает правильно"""
        cache.clear()
        content = self.client.get(INDEX_URL).content
        Post.objects.all().delete()
        self.assertEqual(content, self.client.get(INDEX_URL).content)
        cache.clear()
        self.assertNotEqual(content, self.client.get(INDEX_URL).content)


class TestSubscription(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(USERNAME_AUTHOR)
        cls.follower_user = User.objects.create_user(USERNAME_FOLLOWER)
        cls.another_user = User.objects.create_user(USERNAME_ANOTHER)
        Follow.objects.create(user=cls.follower_user, author=cls.another_user)
        cls.author = Client()
        cls.author.force_login(user=cls.author_user)
        cls.follower = Client()
        cls.follower.force_login(user=cls.follower_user)

    def test_follow(self):
        """Подписка на автора работает правильно"""
        self.follower.get(AUTHOR_FOLLOW_URL)
        self.assertTrue(Follow.objects.filter(
            user=self.follower_user, author=self.author_user).exists()
        )

    def test_unfollow(self):
        """Отписка от автора работает правильно"""
        self.follower.get(ANOTHER_UNFOLLOW_URL)
        self.assertFalse(Follow.objects.filter(
            user=self.follower_user, author=self.another_user).exists()
        )

    def test_unfollow(self):
        """Подписка на самого себя не имеет эффекта"""
        self.author.get(AUTHOR_FOLLOW_URL)
        self.assertFalse(Follow.objects.filter(
            user=self.author_user, author=self.author_user).exists()
        )

    def test_duplicated_subscription(self):
        """Повторная подписка не изменяет состояния подписок"""
        self.follower.get(ANOTHER_FOLLOW_URL)
        self.assertEqual(1, Follow.objects.filter(
            user=self.follower_user, author=self.another_user).count()
        )
