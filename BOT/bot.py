import telebot
import sqlite3
from telebot import types

bot = telebot.TeleBot('1447763558:AAHAnuDaqHbDLyvEruZSxSre408DBOB_7vU')
db = sqlite3.connect('cl_db.db', check_same_thread=False)
c = db.cursor()

lst_GNB = ['Отлично', 'Хорошо', 'Плохо']

chats = {'Neg': 'ID', 'Pos': 'ID', 'Neu': 'ID'}

###Misc###

def get_GNB_markup():
	''' Good, neutral, bad markup '''
	markup = types.ReplyKeyboardMarkup()
	markup.add(types.KeyboardButton('Отлично'))
	markup.add(types.KeyboardButton('Хорошо'))
	markup.add(types.KeyboardButton('Плохо'))
	##markup.add(types.KeyboardButton('Не могу оценить')) Если есть возможность того что человек не контактировал с сотрудником

	return markup

def non_req_GNB(message, func):

	msg = bot.send_message(message.chat.id, 'Вам следует нажимать на кнопки снизу.\n\nЕсли они не работают напишите нашей службе поддержки или /start', reply_markup = get_GNB_markup())
	bot.register_next_step_handler(msg, func)


###SQL Functions###

def get_msg_by_Id(id_, tab, message):

	c.execute("select Text, Users.Name, Users.Surname, Users.Phone, Users.Object from {} inner join Users on U_Id = Users.Id where id = {}".format(tab, id_))
	a = c.fetchall()
	if len(a) == 0:
		bot.send_message(message.chat.id, 'Ошибка')
	else:
		bot.send_message(message.chat.id, 'asd')

###Bot handlers###

@bot.message_handler(commands = ['start'])
def start_msg(message):

	a = message.text.split(' ')
	if len(a) > 1:
		markup = types.ReplyKeyboardMarkup()
		markup.add(types.KeyboardButton('Да, конечно'))
		markup.add(types.KeyboardButton('Нет, не хочу'))
		msg = bot.send_message(message.chat.id, 'Выши отзывы помогают нам стать лучше!\n\nПожалуйста, оцените наш сервис!', reply_markup = markup)
		bot.register_next_step_handler(msg, answ_start, a[1])
	else:
		markup = types.ReplyKeyboardMarkup()
		markup.add(types.KeyboardButton('Отзыв о всех'))
		markup.add(types.KeyboardButton('Отзыв о тревогах'))
		markup.add(types.KeyboardButton('Отзыв о тех.группе'))
		msg = bot.send_message(message.chat.id, 'Хотите оставить отзыв самостоятельно?\n\nМожно оставить отзыв на следущие отделения:', reply_markup = markup)
		bot.register_next_step_handler(msg, answ_start)

def answ_start(message, from_ = None):

	if message.text.find('/start') >= 0:
		start_msg(message)
		return
	if from_ is not None:
		if message.text == 'Да, конечно':
			###Записать уже в таблицу? Наверное да, а потом update or insert и так и жить###
			if from_ == 'all':
				message.text = 'Отзыв о всех'
				answ_start(message)
			elif from_ == 'alerts':
				message.text = 'Отзыв о тревогах'
				answ_start(message)
			elif from_ == 'tech':
				message.text = 'Отзыв о тех.группе'
				answ_start(message)
			else:
				return
		elif message.text == 'Нет, не хочу':
			bot.send_message(message.chat.id, 'Очень жаль, помните что вы всегда можете оставить отзыв нам воспользовавшись коммандой /start')
		else:
			bot.send_message(message.chat.id, 'Вы не должны были это видеть (Если вы не игрались с коммандой /start - напишите поддержке)')
		return
	if message.text == 'Отзыв о всех':
		msg = bot.send_message(message.chat.id, 'Оцените качество обслуживания офис-менеджера', reply_markup = get_GNB_markup())
		bot.register_next_step_handler(msg, pult_msg)
	elif message.text == 'Отзыв о тревогах':
		###Это и след надо прописать отдельными функциями###
		None
	elif message.text == 'Отзыв о тех.группе':
		None
	else:
		markup = types.ReplyKeyboardMarkup()
		markup.add(types.KeyboardButton('Отзыв о всех'))
		markup.add(types.KeyboardButton('Отзыв о тревогах'))
		markup.add(types.KeyboardButton('Отзыв о тех.группе'))
		msg = bot.send_message(message.chat.id, 'Вам следует нажимать на кнопки снизу.\n\nЕсли они не работают напишите нашей службе поддержки или /start')
		bot.register_next_step_handler(msg, answ_start)

def pult_msg(message):
	
	###Реализовать сбор данных###
	if message.text.find('/start') >= 0:
		start_msg(message)
		return
	if message.text in lst_GNB:
		msg = bot.send_message(message.chat.id, 'Оцените качество обслуживания операторов пульта', reply_markup = get_GNB_markup())
		bot.register_next_step_handler(msg, gbr_msg)
	else:
		non_req_GNB(message, pult_msg)

def gbr_msg(message):
	
	###Реализовать сбор данных###
	if message.text.find('/start') >= 0:
		start_msg(message)
		return
	if message.text in lst_GNB:
		msg = bot.send_message(message.chat.id, 'Оцените качество обслуживания службы ГБР', reply_markup = get_GNB_markup())
		bot.register_next_step_handler(msg, tech_msg)
	else:
		non_req_GNB(message, gbr_msg)

def tech_msg(message):

	###Реализовать сбор данных###
	if message.text.find('/start') >= 0:
		start_msg(message)
		return
	if message.text in lst_GNB:
		msg = bot.send_message(message.chat.id, 'Оцените качество  работы технической группы', reply_markup = get_GNB_markup())
		bot.register_next_step_handler(message, concl_msg)
	else:
		non_req_GNB(message, tech_msg)

def tech_msg(message):

	###Вывод с предложением написать сообщение###
	None

###def get_msg_about

def get_nymb_subm(message):

	###Функция для запроса номера###
	None

bot.polling()