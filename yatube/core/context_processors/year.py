import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    today: int = datetime.datetime.now().year
    return {
        'year': today
    }
