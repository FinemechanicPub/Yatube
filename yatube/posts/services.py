"""Модуль вспомогательных функций"""

from django.core.paginator import Paginator
from django.conf import settings
from django.db.models.query import QuerySet
from django.http import HttpRequest


def get_posts_page(request: HttpRequest, query: QuerySet) -> Paginator.page:
    return Paginator(
        query, settings.POSTS_PER_PAGE
    ).get_page(request.GET.get('page', 1))
