from os.path import exists
from pickle import dump, load
import requests
import re
import pprint
from pycbrf import ExchangeRates
from collections import Counter
from json import dump as jdump

# Ввод вакансии
vacancy = input('Введите вакансию: ')
url = 'https://api.hh.ru/vacancies'
rate = ExchangeRates() # загрузка текущих курсов валют

# загрузка файла с цифровыми кодами
if exists('area.pkl'):
    with open('area.pkl', mode='rb') as f:
        area = load(f)
else:
    area = {}

p = {'text': vacancy}
r = requests.get(url=url, params = p).json()

# pprint.pprint(r)

count_pages = r['pages']
all_count = len(r['items'])
result = {
        'keywords': vacancy,
        'count': all_count}
sal = {'from': [], 'to': []}
skillis = []

# Смотрим сколько будет страниц
# Переходим по каждой странице
for page in range(count_pages):
    if page > 2:
        break
    else:
        print(f'Обрабатывается страница {page}')
    p = {'text': vacancy,
        'page': page }
    ress = requests.get(url=url,params=p).json()
    all_count = len(ress['items'])
    result['count'] += all_count
    for res in ress['items']:
        # pprint.pprint(res)
        skills = set()
        city_vac = res['area']['name']
        # добавление города из ответа на запроса, если его нет в файле.
        if city_vac not in area:
            area[city_vac] = res['area']['id']
            ar = res['area']
            res_full = requests.get(res['url']).json()
            # pprint.pprint(res_full)
            #  обработка описания вакансии
            pp = res_full['description']
            # pprint.pprint(pp)
            pp_re = re.findall(r'\s[A-Za-z-?]+', pp)
            # pprint.pprint(pp_re)
            its = set(x.strip(' -').lower() for x in pp_re)
            # pprint.pprint(its)
            for sk in res_full['key_skills']:
                skillis.append(sk['name'].lower())
                skills.add(sk['name'].lower())
            # skills |= sk1
            for it in its:
                if not any(it in x for x in skills):
                    skillis.append(it)
            # окончание формирования списка навыков
            # обработка заплаты
            if res_full['salary']:
                code = res_full['salary']['currency']
                if rate[code] is None:
                    code = 'RUR'
                k = 1 if code == 'RUR' else float(rate[code].value)
                sal['from'].append(k * res_full['salary']['from'] if res['salary']['from'] else k * res_full['salary']['to'])
                sal['to'].append(k * res_full['salary']['to'] if res['salary']['to'] else k * res_full['salary']['from'])


# pprint.pprint(skillis)

sk2 = Counter(skillis)
# pprint(sk2)
up = sum(sal['from']) / len(sal['from'])
down = sum(sal['to']) / len(sal['to'])
result.update({'down': round(up, 2),
               'up': round(down, 2)})
add = []
for name, count in sk2.most_common(5):
    add.append({'name': name,
                'count': count,
                'percent': round((count / result['count'])*100, 2)})
result['requirements'] = add
pprint.pprint(result)
# сохранение файла с результами работы
with open('result.json', mode='w') as f:
    jdump([result], f)
with open('area.pkl', mode='wb') as f:
    dump(area, f)
