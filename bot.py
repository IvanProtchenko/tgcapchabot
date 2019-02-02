import telebot
from telebot import types
import os
import time
from threading import Thread
#Токен бота
TOKEN=os.environ['TOKEN'] 

#Сообщение под которым будут кнопки выбора
CAPCHA_MESSAGE="Идём со мной {0} , если хочешь жить. Долго не раздумывай, у тебя есть всего 1 минута."

#Сообщение приветствия, в случае выбора успешной кнопки
CAPCHA_OK="{0} будет жить. Поприветствуем!" 

#Время для размышлений выбора "правильной кнопки" (в секундах). Нужно исправить время CAPCHA_MESSAGE
TIME_KICK=60

#Словарь с кнопками, можно добавить/удалить, обработка происходжит в функции callback()
DATA_CAPCHA={
    'OK':'Идём',
    'NOT':'Я еще вернусь',
    #'DEBUG':'DEBUG'
}

#Просто переменные которые используются
DATA_KICK={}
LIST_KEY=[]

bot = telebot.TeleBot(TOKEN)
for key in DATA_CAPCHA:
    LIST_KEY.append(DATA_CAPCHA[key])


class MyThread(Thread):
    """
    A threading example
    """
    def __init__(self, name):
        """Инициализация потока"""
        Thread.__init__(self)
        self.name = name
    def run(self):
        """Запуск потока"""
        while True:
            if len(DATA_KICK)>0:
                for i in DATA_KICK.copy():
                    if time.time() > i:
                       bot.kick_chat_member(DATA_KICK[i]['chatid'], DATA_KICK[i]['userid'], until_date=time.time() + 60)
                       bot.delete_message(DATA_KICK[i]['chatid'], DATA_KICK[i]['messageid_to'])
                       bot.delete_message(DATA_KICK[i]['chatid'], DATA_KICK[i]['messageid'])
                       #Вывод данные о тех кто долго думает
                       print('DELETE - ' + str(DATA_KICK[i]))
                       DATA_KICK.pop(i)
            time.sleep(1)
def create_threads():
    """
    Создаем группу потоков
    """
    i=0
    name = "Thread #%s" % (i+1)
    my_thread = MyThread(name)
    my_thread.start()

# Обработка соообщений 'ololosh теперь в группе'
@bot.message_handler(content_types=["new_chat_members"])
def handler_new_members(message):
    date_kick=time.time() + TIME_KICK
    user_name = message.new_chat_member.first_name
    keyboard_capcha = types.InlineKeyboardMarkup()
    keyboard_capcha.add(*[types.InlineKeyboardButton(text=keyname, callback_data=keyname) for keyname in LIST_KEY])
    msg=bot.reply_to(message, CAPCHA_MESSAGE.format(user_name),reply_markup=keyboard_capcha)
    DATA_KICK[date_kick]={'chatid':message.chat.id,'userid':message.new_chat_member.id,'messageid_to':msg.message_id,'messageid':message.message_id}
    #Выдача всем новым пользователям бесконечного бана
    bot.restrict_chat_member(message.chat.id, message.new_chat_member.id, 
        until_date=0,
        )
    #Разворот списка и названиями кнопок
    LIST_KEY.reverse()

#Обработка нажатия кнопок
@bot.callback_query_handler(func=lambda c: True)
def callback(c):
    user_name = c.message.reply_to_message.new_chat_member.first_name
    if c.data==DATA_CAPCHA['OK']:
        if c.from_user.id == c.message.reply_to_message.new_chat_member.id:
            for d in DATA_KICK.copy():
                if DATA_KICK[d]['userid']==c.from_user.id and DATA_KICK[d]['chatid']==c.message.chat.id:
                    DATA_KICK.pop(d)
            bot.delete_message(c.message.chat.id, c.message.message_id)
            bot.send_message(c.message.chat.id,CAPCHA_OK.format(user_name))
            #Убирает бесконечный бан
            bot.restrict_chat_member(c.message.chat.id, c.from_user.id, 
            can_send_messages=True, 
            can_send_media_messages=True, 
            can_send_other_messages=True,
            can_add_web_page_previews=True)            
    else:
        if c.from_user.id == c.message.reply_to_message.new_chat_member.id:
            bot.delete_message(c.message.chat.id, c.message.reply_to_message.message_id)
            bot.delete_message(c.message.chat.id, c.message.message_id)
            bot.kick_chat_member(c.message.chat.id, c.from_user.id, until_date=time.time() + 60 )
            for d in DATA_KICK.copy():
                if DATA_KICK[d]['userid']==c.from_user.id and DATA_KICK[d]['chatid']==c.message.chat.id:
                    DATA_KICK.pop(d)

#На сообщение которое равно тексту 'ping' формирование ответа. Этакая проверка что бот работает
@bot.message_handler(content_types=["text"])
def ping(m):
    if m.text == 'ping':
        bot.reply_to(m,str('pong'))

if __name__ == '__main__':
    try:
        create_threads()
        bot.polling(none_stop=True)
    except:
        print('ошибка')
