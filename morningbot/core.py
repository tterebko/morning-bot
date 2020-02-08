import datetime
import functools
import O365
import os
import requests

from functools import reduce
from xml.etree import ElementTree   # pip install elementpath

from morningbot import translations

OFFICE_365_CLIENT_ID = os.getenv('TMB_O365_CLIENT_ID')
GOOGLE_API_CLIENT_ID = ''
CURRENCY = os.getenv('TMB_CURRENCY', 'EUR')
CURRENCY_AMOUNT = int(os.getenv('TMB_CURRENCY_AMOUNT', 1))
OPEN_WEATHER_API_KEY = os.getenv('TMB_OPEN_WEATHER_MAP_API_KEY')
CITY_CODE = os.getenv('TMB_OPENWEATHER_CITY_CODE', '498817') # "name": "Saint Petersburg", "country": "RU"
LANG = os.getenv('TMB_LANG', 'ru')


@functools.lru_cache()
def request_openweathermap(location: str) -> dict:
    api_url = 'https://api.openweathermap.org/data/2.5'
    url = f'{api_url}/forecast?id={location}&appid={OPEN_WEATHER_API_KEY}&units=metric&lang={LANG}'
    return requests.get(url).json()


def get_time_and_place(location_code: str) -> str:
    response = request_openweathermap(location_code)
    d = datetime.date.today()
    return f'{response["city"]["name"]}, {d.strftime("%Y-%m-%d")} ({d.strftime("%GW%V")[2:]})'


def get_weather(location_code: str) -> str:
    response = request_openweathermap(location_code)
    res = ''
    for item in [i for i in response['list'] if i['dt_txt'].startswith(datetime.date.today().strftime('%Y-%m-%d'))]:
        t = str(round(item['main']['temp'])) + '/' + str(round(item['main']['feels_like'])) + ' °C'
        d = item['weather'][0]['description']
        w = str(round(item['wind']['speed'])) + ' ' + translations.get('m*s**-1', LANG)
        p = str(item['main']['pressure']) + ' ' + translations.get('hpa', LANG)
        h = str(item['main']['humidity']) + '%'
        res += item['dt_txt'][11:16] + ': ' + ', '.join([t, d, w, p, h]) + '\n'
    return res


def get_sun_hours(location_code: str) -> str:
    def get_time(t, tz):
        return datetime.datetime.fromtimestamp(t, tz).strftime('%H:%M')
    response = request_openweathermap(location_code)
    timezone = datetime.timezone(offset=datetime.timedelta(seconds=response['city']['timezone']))
    return get_time(response['city']['sunrise'], timezone) + ' - ' + get_time(response['city']['sunset'], timezone)


def get_currency_rate_from_cbr(curr: str) -> float:
    curr_date = datetime.date.today().strftime('%d/%m/%Y')
    root = ElementTree.XML(requests.get(f'http://www.cbr.ru/scripts/XML_daily.asp?date_req={curr_date}').content)
    return float(root.find(f'Valute[CharCode="{curr}"]/Value').text.replace(',', '.'))


def get_currency_exchange(curr: str, amount: int) -> str:
    res = get_currency_rate_from_cbr(curr) * amount
    return f'{round(res, 2):,}'


def get_first_o365_meeting(client_id: str) -> str:
    scopes_graph = O365.MSGraphProtocol().get_scopes_for(['calendar', 'basic'])
    account = O365.Account((client_id, None), scopes=scopes_graph)

    if not account.is_authenticated:
        consent_url, _ = account.con.get_authorization_url()

        print('Visit the following url to give consent:')
        print(consent_url)
        token_url = input('Paste the authenticated url here:\n').rstrip()

        if token_url:
            result = account.connection.request_token(token_url)  # no need to pass state as the session is the same
            if result:
                print('Authentication Flow Completed. Oauth Access Token Stored. You can now use the API.')
            else:
                print('Something go wrong. Please try again.')

    calendar = account.schedule().get_default_calendar()
    s = datetime.date.today()
    f = s + datetime.timedelta(hours=24)
    q = calendar.new_query('start').greater_equal(s).chain('and').on_attribute('start').less_equal(f)
    q.chain('and').on_attribute('end').less_equal(f)

    events = sorted(list(calendar.get_events(query=q, include_recurring=True)), key=lambda e: e.start)

    if events:
        res = events[0].start.strftime('%H:%M') + ': ' + events[0].subject
        if len(events) > 1 and events[0].start == events[1].start:
            res += ' | ' + events[1].subject
    else:
        res = translations.get('no_events', LANG)
    return res


def get_birthdays_from_google_contacts(client_id: str) -> str:
    res = translations.get('no_birthdays', LANG)
    return res


def send_message_to_telegram(message: str) -> None:
    print(message)


if __name__ == '__main__':
    info_providers = [
        ('', get_time_and_place, (CITY_CODE,)),
        (translations.get('day_length', LANG), get_sun_hours, (CITY_CODE,)),
        (translations.get('first_meeting', LANG), get_first_o365_meeting, (OFFICE_365_CLIENT_ID,)),
        (translations.get('currency_basket', LANG), get_currency_exchange, (CURRENCY, CURRENCY_AMOUNT)),
        (translations.get('birthdays', LANG), get_birthdays_from_google_contacts, (GOOGLE_API_CLIENT_ID,)),
        (translations.get('weather', LANG), get_weather, (CITY_CODE,)),
    ]

    message_for_today = reduce(lambda msg, pr: msg + pr[0] + '\n' + pr[1](*pr[2]) + '\n\n', info_providers, '')

    send_message_to_telegram(message_for_today)
