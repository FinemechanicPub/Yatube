import datetime


def year(request):
    """Добавляет в контекст текущий год."""
    return {
        'year': datetime.date.today().year
    }
