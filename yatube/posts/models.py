from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    """Модель группы."""

    title = models.CharField(max_length=200, verbose_name='заголовок')
    slug = models.SlugField(unique=True, verbose_name='идентификатор')
    description = models.TextField(verbose_name='описание')

    class Meta:
        verbose_name = 'группу'  # accusative
        verbose_name_plural = 'группы'

    def __str__(self):
        return self.title


class Post(models.Model):
    """Модель публикации."""

    text = models.TextField(
        verbose_name='текст',
        help_text='введите текст поста'
    )
    pub_date = models.DateTimeField(auto_now_add=True, verbose_name='дата')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='автор'
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='группа',
        help_text='выберите группу'
    )
    image = models.ImageField(
        verbose_name='картинка',
        help_text='выберите графический файл',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)
        default_related_name = 'posts'
        verbose_name = 'публикацию'  # accusative
        verbose_name_plural = 'публикации'

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    """Модель комментария."""

    text = models.TextField(
        verbose_name='текст',
        help_text='введите текст комментария'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='автор'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='комментируемая публикация'
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name='дата')

    class Meta:
        ordering = ('created',)
        default_related_name = 'comments'
        verbose_name = 'комментарий'  # accusative
        verbose_name_plural = 'комментарии'

    def __str__(self) -> str:
        return self.text[:15]


class Follow(models.Model):
    """Модель учета подписок"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='пользователь',
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='автор',
        related_name='following'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_subscription'
            )
        ]

    def __str__(self):
        return f'{self.user.username} is following {self.author.username}'
