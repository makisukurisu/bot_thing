import telebot
import sqlite3
from telebot import types

bot = telebot.TeleBot('861027023:AAGgkQWySnkXN-qk5TqS47t_PzWYPMfS3_8')
db = sqlite3.connect('cl_db.db', check_same_thread=False)
c = db.cursor()

reply_cb = types.ReplyKeyboardMarkup()

chats = {'Neg': 'ID', 'Pos': 'ID', 'Neu': 'ID'}

def get_msg_by_Id(id_, tab, message):

	c.execute("select Text, Users.Name, Users.Surname, Users.Phone, Users.Object from {} inner join Users on U_Id = Users.Id where id = {}".format(tab, id_))
	a = c.fetchall()
	if len(a) == 0:
		bot.send_message(message.chat.id, 'Ошибка')
	else:
		bot.send_message(message.chat.id, 'asd')

@bot.message_handler(commands = ['start'])
def start_msg(message):

	a = message.text.split(' ')
	if len(a) < 2:
		from_thing = True	
	else:
		from_thing = False
		### Сделать передачу "Из раздела ***" Если будет надо
	markup = types.ReplyKeyboardMarkup()
	markup.add(types.KeyboardButton('Да, конечно'))
	markup.add(types.KeyboardButton('Нет, не хочу'))
	msg = bot.send_message(message.chat.id, 'Выши отзывы помогают нам стать лучше!\n\nПожалуйста, оцените наш сервис!', reply_markup = markup)
	bot.register_next_step_handler(msg, answ_start)


def answ_start(message):

	lst = ['Да, конечно', 'Нет, не хочу']
	if message.text in lst:
		if message.text == lst[0]:
			markup = reply_cb
			markup.add(types.KeyboardButton('Отлично'))
			markup.add(types.KeyboardButton('Хорошо'))
			markup.add(types.KeyboardButton('Плохо'))
			##markup.add(types.KeyboardButton('Не могу оценить')) Если есть возможность того что человек не контактировал с сотрудником
			msg = bot.send_message(message.chat.id, 'Оцените качество обслуживания офис-менеджера', reply_markup = markup)
			bot.register_next_step_handler(msg, )
		else:
			bot.send_message(message.chat.id, 'Жаль это слышать')
	else:
		markup = types.ReplyKeyboardMarkup()
		markup.add(types.KeyboardButton('Да, конечно'))
		markup.add(types.KeyboardButton('Нет, не хочу'))
		msg = bot.send_message(message.chat.id, 'Вам следует нажимать на кнопки паенли снизу.\n\nЕсли они не работают напишите нашей службе поддержки или /start')
		bot.register_next_step_handler(msg, answ_start)

def pult_msg(message):
	
	lst = ['Отлично', 'Хорошо', 'Плохо']
	if message.text in lst:
		'качество обслуживания операторов пульта'