from django.test import TestCase

from ..models import Post, Group, User


TEST_GROUP = {
    'title': 'Тестовая группа',
    'slug': 'test_group',
    'description': 'Описание тестовой группы'
}

TEST_POST_LONG = {
    'text': 'Текст тестового поста'
}

TEST_POST_SHORT = {
    'text': 'Краткий пост'
}


class PostModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(**TEST_GROUP)
        cls.post_long = Post.objects.create(
            author=cls.user,
            group=cls.group,
            **TEST_POST_LONG
        )
        cls.post_short = Post.objects.create(
            author=cls.user,
            group=cls.group,
            **TEST_POST_SHORT
        )

    def test_models_have_correct_object_names(self):
        """У моделей корректно работает __str__."""
        expected_truncation = 15
        self.assertEqual(str(self.group), self.group.title)
        self.assertEqual(
            str(self.post_long),
            self.post_long.text[:expected_truncation]
        )
        self.assertEqual(
            str(self.post_short),
            self.post_short.text[:expected_truncation]
        )

    def test_models_have_correct_helptext(self):
        """В модели Post правильные help_text"""
        post_help_texts = {
            'group': 'выберите группу',
            'text': 'введите текст поста'
        }
        for field, expected_value in post_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Post._meta.get_field(field).help_text,
                    expected_value
                )

    def test_models_have_correct_verbose_name(self):
        """В модели Post правильные verbose_name"""
        post_verbose_names = {
            'author': 'автор',
            'group': 'группа',
            'text': 'текст'
        }
        for field, expected_value in post_verbose_names.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Post._meta.get_field(field).verbose_name,
                    expected_value
                )
