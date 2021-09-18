'''
Публичная лицензия этого продукта 
Copyright © 2020 ikatuli
При использовании данного продукта вы соглашаетесь со следующими пунктами лицензии:
1. Вы имеете право делать с данным продуктом всё что угодно, за исключением того, что может являться нарушением законов страны, в которой находитесь вы, или страны, в которой этот продукт будет использоваться.
2. Автор не несёт ответственности за какой-либо прямой, непрямой, особый или иной косвенный ущерб нанесённый в результате использования, не использования и существования продукта.
'''

import vk_api, time, argparse, getpass, urllib.request, threading

def constitute(att): #Выуживание картинок максимального размера.
    Type = ['w','z','y','x','m','s']
    for i in Type:
            for k in range(len(att['sizes'])-1,0,-1): # В обратном порядке приходится перебирать меньше элементов.
                if att['sizes'][k]['type']==i:
                    return [str(att['date'])+'-'+att['sizes'][k]['url'][-15:],att['sizes'][k]['url']]

def download(url,name): #Скачивание файлов
    urllib.request.urlretrieve(url,filename=name)

#Параметры командной строки
parser = argparse.ArgumentParser()
parser.add_argument('-l', '--login' ,action='store',help='Логин от vk.')
parser.add_argument('-p', '--password',action='store', help='Пароль от vk.')
parser.add_argument('-a', '--app_id',action='store', help='ID приложения')
parser.add_argument('-t', '--token',action='store', type=str, help='Токен доступа')
parser.add_argument('-i', '--id',action='store',type=int, help='Id беседы или человека.')
parser.add_argument('-d', '--date',action='store', nargs=2, help='Диапазон дат. Изображения, которые были скачены в этот временной промежуток, будут скачены скриптом. Даты должны быть в формате "гг-мм-дд гг-мм-дд"')
parser.add_argument('-n', '--number',type=int,action='store', help='Скачать NUMBER фотографий начиная с конца переписки.')
parser.parse_args()

#Присвоение значений из параметров.
login = parser.parse_args().login
password = parser.parse_args().password
id_gr =parser.parse_args().id
date = parser.parse_args().date
number= parser.parse_args().number
my_token=parser.parse_args().token
app=parser.parse_args().app_id

if date and number:
    print('Аргумент \x1B[3mnumber\x1B[23m не может использоваться вместе с аргументом \x1B[3mdate\x1B[23m.')
    exit()

while True: #Вход в аккаунт
    if not(my_token):
        my_token =input('Введите токет: ')
    if not(app):
        app =str(input('Введите app_id: '))
    if not(login):
        login = input('Введите логин: ')
    if not(password):
        password = getpass.getpass("Введите пароль: ")
    vk_session = vk_api.VkApi(login, password,api_version='5.92',token=my_token,app_id=app) #Нужно добыть token=
    try:
        vk_session.auth()
    except vk_api.AuthError as error_msg:
        login, password ,my_token ,app  = None, None, None, None
        print(5*'\033[K\033[A',error_msg)
        print('Какие-то из введённых вами не верны.',end=' ')
        continue
    
    vk = vk_session.get_api()
    break

if not(id_gr):
    i=0
    while True: #Выводит список диалогов
        messages = vk.messages.getConversations(offset=i,count=1,)
        id_gr=messages['items'][0]['conversation']['peer']['id']
        if messages['items'][0]['conversation']['peer']['type']=="user":#Если это сообщения пользователя.
            user = vk.users.get(user_ids=id_gr) #Находим имя адрисата по id
            print(user[0]["first_name"],user[0]["last_name"])
        else:
            print(messages['items'][0]['conversation']['chat_settings']['title'])
        if input('Для продолжения введите n. Для остановки введите y ')=='y':
            break
        print(3*'\033[K\033[A')
        i+=1

if len(str(id_gr))<9: #Прибавляет нужное значение к id беседы.
    id_gr+=2000000000

if not(number or date): #Получает количество или дату в случае отсутствия таких в параметрах командной строки.
    number=input('Введите количество фотографий, которое необходимо скачать, начиная с конца переписка или введите n: ')
    if not(number.isdigit()):
        number = 0
    number=int(number)
    if not(number):
        date=input('Дата, перед которой ведется закачка файлов.Запись должна быть в формате "гг-мм-дд гг-мм-дд": ').split()
    
if date:#Переводит строку со временем в секунды с начала эпохи.
    date0=int(time.mktime(time.strptime(date[0],'%y-%m-%d')))
    date2=int(time.mktime(time.strptime(date[1],'%y-%m-%d')))
    if date0<date2: # Меняет даты, в случае если одна больше другой.
        date0, date2 = date2, date0



step = 0 #Инициализация переменой шага.
pic = [] #Инициализация списка фотографий.

if number: #список картинок по номеру
    while number and (step!=None): 
        if number>=200:
            count=200
            number-=200
        else:
            count=number
            number=None
        attach=vk.messages.getHistoryAttachments(peer_id=id_gr,media_type='photo',start_from=step,count=count)
        step=attach.get('next_from')
        for i in range(len(attach['items'])): #Количество фотографий может быть меньше, чем указанно в count.
             pic.append(constitute(attach['items'][i]['attachment']['photo']))

if date: #список картинок по дате.
    while step!=None:
        attach=vk.messages.getHistoryAttachments(peer_id=id_gr,media_type='photo',start_from=step,count=200)
        step=attach.get('next_from')
        for i in range(len(attach['items'])):
            date1=attach['items'][i]['attachment']['photo']['date']
            if date0>date1>date2:
                pic.append(constitute(attach['items'][i]['attachment']['photo']))
        if date1<date2:
            break

for i in pic:
     threading.Thread(target=download,args=(i[1],i[0])).start() #Распоралеливает скачивание (в теории работает быстрее)
