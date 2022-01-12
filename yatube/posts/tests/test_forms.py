import shutil
import tempfile
from copy import copy

from django import forms
from django.conf import settings
from django.contrib import auth
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http.response import HttpResponse
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, User, Post, Group

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
USERNAME = 'auth'
USERNAME_OTHER = 'other_user'
GROUP_FIRST = {'title': 'Test group 1', 'slug': 'test_group1'}
GROUP_SECOND = {'title': 'Test group 2', 'slug': 'test_group2'}
INDEX_URL = reverse('posts:index')
POST_CREATE_URL = reverse('posts:post_create')
PROFILE_URL = reverse('posts:profile', args=(USERNAME,))
LOGIN_PAGE_URL = reverse('users:login')
LOGIN_AND_POST_CREATE_URL = f'{LOGIN_PAGE_URL}?next={POST_CREATE_URL}'
TEST_IMAGE_1 = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
TEST_IMAGE_2 = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00'
    b'\x01\x00\x00\x00\x00\x21\xf9\x04'
    b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
    b'\x00\x00\x01\x00\x01\x00\x00\x02'
    b'\x02\x4c\x01\x00\x3b'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestPostForm(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(USERNAME)
        cls.guest = Client()
        cls.author = Client()
        cls.author.force_login(user=cls.author_user)
        cls.other_user = User.objects.create_user(USERNAME_OTHER)
        cls.other = Client()
        cls.other.force_login(cls.other_user)
        cls.group_first = Group.objects.create(**GROUP_FIRST)
        cls.group_second = Group.objects.create(**GROUP_SECOND)
        cls.post = Post.objects.create(
            author=cls.author_user,
            group=cls.group_first,
            text='Пост для редактирования',
            image=SimpleUploadedFile(
                name='image1.gif',
                content=TEST_IMAGE_1,
                content_type='image/gif'
            )
        )
        cls.POST_EDIT_URL = reverse('posts:post_edit', args=(cls.post.pk,))
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args=(cls.post.pk,))
        cls.LOGIN_AND_POST_EDIT_URL = (
            f'{LOGIN_PAGE_URL}?next={cls.POST_EDIT_URL}'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_create(self):
        """При отправке формы создается публикация"""
        posts = set(Post.objects.all())
        form_data = {
            'text': 'Новый пост',
            'group': self.group_first.pk,
            'image':
            SimpleUploadedFile('image2.gif', TEST_IMAGE_2, 'image/gif')
        }
        response = self.author.post(POST_CREATE_URL, form_data)
        self.assertRedirects(response, PROFILE_URL)
        posts = set(Post.objects.all()) - posts
        self.assertEqual(len(posts), 1, 'Должен добавляться ровно 1 пост')
        post = posts.pop()
        self.assertEqual(post.author, response.wsgi_request.user)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.pk, form_data['group'])
        form_data['image'].seek(0)
        self.assertEqual(post.image.file.read(), form_data['image'].read())

    def test_post_edit(self):
        """При отправке формы публикация редактируется"""
        post_author = self.post.author
        form_data = {
            'text': "Отредактированный пост",
            'group': self.group_second.pk,
            'image':
            SimpleUploadedFile('image2.gif', TEST_IMAGE_2, 'image/gif')
        }
        response = self.author.post(self.POST_EDIT_URL, form_data)
        self.assertRedirects(response, self.POST_DETAIL_URL)
        post = Post.objects.get(pk=self.post.pk)
        self.assertEqual(post.author, post_author)
        self.assertEqual(post.group.pk, form_data['group'])
        self.assertEqual(post.text, form_data['text'])
        form_data['image'].seek(0)
        self.assertEqual(post.image.file.read(), form_data['image'].read())

    def test_post_form(self):
        """На страницу передается правильная форма"""
        cases = [
            [POST_CREATE_URL, None],
            [self.POST_EDIT_URL, self.post]
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for url, post in cases:
            with self.subTest(url=url):
                form = self.author.get(url).context['form']
                for field, expected_type in form_fields.items():
                    self.assertIsInstance(
                        form.fields.get(field), expected_type
                    )
                if post:
                    self.assertEqual(form['text'].value(), post.text)
                    self.assertEqual(form['group'].value(), post.group.pk)

    def test_unauthorized_create_post(self):
        posts = set(Post.objects.all())
        form_data = {
            'text': "Новый пост"
        }
        self.assertRedirects(
            self.guest.post(POST_CREATE_URL, form_data),
            LOGIN_AND_POST_CREATE_URL
        )
        self.assertEqual(set(Post.objects.all()), posts)

    def test_redirection(self):
        """Неуполномоченные пользователи перенаправляются и не меняют данные"""
        pk = self.post.pk
        text = self.post.text
        group = self.post.group
        author = self.post.author
        image = self.post.image
        cases = [
            [self.guest, self.POST_EDIT_URL, self.LOGIN_AND_POST_EDIT_URL],
            [self.other, self.POST_EDIT_URL, self.POST_DETAIL_URL],
            #[self.author, self.POST_EDIT_URL, self.POST_DETAIL_URL]
        ]
        form_data = {
            'text': "Этот пост не должен попасть в базу данных",
            'group': self.group_second.pk,
            'image':
            SimpleUploadedFile('image1.gif', TEST_IMAGE_2, 'image/gif')
        }
        for client, url, redirection in cases:
            with self.subTest(url=url):
                form_data['image'].seek(0)
                self.assertRedirects(client.post(url, form_data), redirection)
                post = Post.objects.get(pk=pk)                              
                self.assertEqual(post.author, author)
                self.assertEqual(post.text, text)
                self.assertEqual(post.group, group)
                self.assertEqual(post.image, image)


class TestCommentForm(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(USERNAME)
        cls.guest = Client()
        cls.authorized = Client()
        cls.authorized.force_login(user=cls.user)
        cls.post = Post.objects.create(
            author=cls.user,
            text='Пост для комментирования'
        )
        cls.COMMENT_ADD_URL = reverse('posts:add_comment', args=(cls.post.pk,))
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args=(cls.post.pk,))
        cls.LOGIN_AND_COMMENT_URL = (
            f'{LOGIN_PAGE_URL}?next={cls.COMMENT_ADD_URL}'
        )

    def test_comment_create(self):
        """При отправке формы создается комментарий"""
        comments = set(self.post.comments.all())
        form_data = {
            'text': 'Новый комментарий'
        }
        response = self.authorized.post(self.COMMENT_ADD_URL, form_data)
        self.assertRedirects(response, self.POST_DETAIL_URL)
        comments = set(self.post.comments.all()) - comments
        self.assertEqual(
            len(comments), 1, 'Должен добавляться ровно 1 комментарий'
        )
        comment = comments.pop()
        self.assertEqual(comment.text, form_data['text'])

    def test_comment_form(self):
        """На страницу передается правильная форма комментария"""
        form_fields = {
            'text': forms.fields.CharField,
        }
        form = self.authorized.get(self.POST_DETAIL_URL).context['form']
        for field, expected_type in form_fields.items():
            with self.subTest(field=field):
                self.assertIsInstance(form.fields.get(field), expected_type)

    def test_redirection(self):
        """Неуполномоченные пользователи перенаправляются и не меняют данные"""
        cases = [
            [
                self.guest,
                self.COMMENT_ADD_URL,
                self.LOGIN_AND_COMMENT_URL
            ],
        ]
        form_data = {
            'text': "Этот комментарий не должен попасть в базу данных",
        }
        for client, url, redirection in cases:
            with self.subTest(url=url, user=auth.get_user(client)):
                comments = set(Comment.objects.all())
                self.assertRedirects(client.post(url, form_data), redirection)
                comments = set(Comment.objects.all()) - comments
                self.assertFalse(comments)
                self.assertFalse(
                    Comment.objects.filter(text=form_data['text']).exists()
                )
