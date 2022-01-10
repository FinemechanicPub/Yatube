import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import User, Post, Group

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
USERNAME = 'auth'
GROUP_FIRST = {'title': 'Test group 1', 'slug': 'test_group1'}
GROUP_SECOND = {'title': 'Test group 2', 'slug': 'test_group2'}
INDEX_URL = reverse('posts:index')
POST_CREATE_URL = reverse('posts:post_create')
PROFILE_URL = reverse('posts:profile',args=(USERNAME,))
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
        cls.user = User.objects.create_user(USERNAME)
        cls.group_first = Group.objects.create(**GROUP_FIRST)
        cls.group_second = Group.objects.create(**GROUP_SECOND)
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group_first,
            text='Пост для редактирования',
            image=SimpleUploadedFile(
                name='image1.gif',
                content=TEST_IMAGE_1,
                content_type='image/gif'
            )
        )
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit', kwargs={'post_id': cls.post.pk}
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', kwargs={'post_id': cls.post.pk}
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(user=self.user)

    def test_post_create(self):
        """При отправке формы создается публикация"""
        posts = set(Post.objects.all())
        form_data = {
            'text': "Новый пост",
            'group': self.group_first.pk,
            'image':
            SimpleUploadedFile('image2.gif', TEST_IMAGE_2, 'image/gif')
        }
        response = self.authorized_client.post(POST_CREATE_URL, form_data)
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
        response = self.authorized_client.post(self.POST_EDIT_URL, form_data)
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
                form = self.authorized_client.get(url).context['form']
                for field, expected_type in form_fields.items():
                    self.assertIsInstance(
                        form.fields.get(field), expected_type
                    )
                if post:
                    self.assertEqual(form['text'].value(), post.text)
                    self.assertEqual(form['group'].value(), post.group.pk)


class TestCommentForm(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(USERNAME)
        cls.post = Post.objects.create(
            author=cls.user,
            text='Пост для комментирования'
        )
        cls.COMMENT_ADD_URL = reverse('posts:add_comment', args=(cls.post.pk,))
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args=(cls.post.pk,))

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(user=self.user)

    def test_comment_create(self):
        """При отправке формы создается комментарий"""
        comments = set(self.post.comments.all())
        form_data = {
            'text': 'Новый комментарий'
        }
        response = self.authorized_client.post(self.COMMENT_ADD_URL, form_data)
        self.assertRedirects(response, self.POST_DETAIL_URL)
        comments = set(self.post.comments.all()) - comments
        self.assertEqual(
            len(comments), 1, 'Должен добавляться ровно 1 комментарий'
        )
        comment = comments.pop()
        self.assertEqual(comment.text, form_data['text'])

    def test_post_form(self):
        """На страницу передается правильная форма комментария"""
        form_fields = {
            'text': forms.fields.CharField,
        }
        form = self.authorized_client.get(self.POST_DETAIL_URL).context['form']
        for field, expected_type in form_fields.items():
            with self.subTest(field=field):
                self.assertIsInstance(form.fields.get(field), expected_type)
