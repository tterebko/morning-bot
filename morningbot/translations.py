import doctest
from collections import defaultdict

dictionary = defaultdict(dict, {
    'birthdays': {
        'en': 'Birthdays',
        'ru': 'Дни рождения'
    },
    'currency_basket': {
        'en': 'Currency basket',
        'ru': 'Валютная корзина'
    },
    'day_length': {
        'en': 'Length of day',
        'ru': 'Световой день'
    },
    'first_meeting': {
        'en': 'First meeting',
        'ru': 'Первое совещание'
    },
    'hpa': {
        'en': 'hPa',
        'ru': 'гПа'
    },
    'humidity': {
        'en': 'hum',
        'ru': 'влаж.'
    },
    'm*s**-1': {
        'en': 'm/s',
        'ru': 'м/с'
    },
    'no_birthdays': {
        'en': 'There are no birthdays today.',
        'ru': 'Сегодня нет дней рождения.'
    },
    'no_events': {
        'en': 'There are no events today.',
        'ru': 'Календарь на сегодня пуст.'
    },
    'pressure': {
        'en': 'press',
        'ru': 'давл.'
    },
    'temperature': {
        'en': 'temp',
        'ru': 'темп.'
    },
    'weather': {
        'en': 'Weather (temp/feeling, cloud, wind, press, hum)',
        'ru': 'Погода (темп./ощущение, обл, вет, давл, влаж)',
    },
    'wind': {
        'en': 'wind',
        'ru': 'ветр.'
    }
})


def get(key: str, lang: str) -> str:
    """ Return localized string by key.

    >>> get('m*s**-1', 'ru')
    'м/с'

    If there is no translation for some language, then English version is returned.
    >>> get('m*s**-1', 'NO_SUCH_LANG')
    'm/s'

    If there is no such key, then the key itself is returned.
    >>> get('NO_SUCH_KEY', 'en')
    'NO_SUCH_KEY'
    """
    return dictionary[key].get(lang, dictionary[key].get('en', key))


if __name__ == '__main__':
    doctest.testmod()