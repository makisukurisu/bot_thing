import telebot
import sqlite3
from telebot import types

bot = telebot.TeleBot('1447763558:AAHAnuDaqHbDLyvEruZSxSre408DBOB_7vU')
db = sqlite3.connect('db.db', check_same_thread=False)
c = db.cursor()

lst_GNB = ['Отлично', 'Хорошо', 'Плохо']

chats = {'Neg': '-436080592', 'Pos': '-359369842', 'Neu': '-463073970'}
chats_indx = ['-359369842', '-463073970', '-436080592']

quest = {'all': ['Офис менеджер', 'Оператор пульта', 'Служба ГБР', 'Тех.группа'],
		'alert': ['Отработка тревог'],
		'tech': ['Тех.группа']}

class U_TH():

	def __init__(self, t_id, from_):
		self.id = t_id
		self.from_ = from_
		self.answers = []
		self.message = None
		self.numb = None
		self.about = None
	def new_ans(self, answ):
		self.answers.append(answ)
	def new_msg(self, msg):
		self.message = msg
	def new_numb(self, numb):
		self.numb = numb
	def new_about(self, about):
		self.about = about
	def get_all(self):		
		return [self.id, self.from_, self.answers, self.message, self.numb, self.about]


us_answers = []
###Misc###

def append_to_us(id, info, fun = 'ans'):

	for x in us_answers:
		if x.id == id:
			if fun == 'ans':
				x.new_ans(info)
			elif fun == 'msg':
				x.new_msg(info)
			elif fun == 'numb':
				x.new_numb(info)
			elif fun == 'about':
				x.new_about(info)


def get_us(id):

	for x in us_answers:
		if x.id == id:
			return x

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

def get_string(id, type = None):
	None
	#if type == 'Отлично':
		#if get_us(id).type == 'all':

def proc_us(id):
	
	U_Info = get_us(id)
	m_text = ['', '', '']
	answ_var = ['Отлично', 'Хорошо', 'Плохо']
	comp_text = []
	for x in range(len(U_Info.answers)):
		m_text[answ_var.index(U_Info.answers[x])] += quest[U_Info.about][x] + "\n"
	for x in m_text:
		msg = '{} - {} Оставил новый отзыв:\n\n{}\n\nОценил {}\n{}'.format(U_Info.id, U_Info.numb, m_text[m_text.index(x)], answ_var[m_text.index(x)], U_Info.from_)
		bot.send_message(chats_indx[m_text.index(x)], msg)


###SQL Functions###

def get_msg_by_Id(id_, tab, message):

	c.execute("select Text, Users.Name, Users.Surname, Users.Phone, Users.Object from {} inner join Users on U_Id = Users.Id where id = {}".format(tab, id_))
	a = c.fetchall()
	if len(a) == 0:
		bot.send_message(message.chat.id, 'Ошибка')
	else:
		bot.send_message(message.chat.id, 'asd')

###Bot handlers###

@bot.message_handler(commands = ['chat_id'])
def get_chat_id(message):

	bot.send_message(message.chat.id, 'Айди этого чата:\n<code>{}</code>'.format(message.chat.id), parse_mode = "HTML")

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
		us_answers.append(U_TH(message.from_user.id, ''))
		append_to_us(message.from_user.id, message.text)
		append_to_us(message.from_user.id, 'all', 'about')
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
		append_to_us(message.from_user.id, message.text)
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
		append_to_us(message.from_user.id, message.text)
		msg = bot.send_message(message.chat.id, 'Оцените качество  работы технической группы', reply_markup = get_GNB_markup())
		bot.register_next_step_handler(message, concl_msg)
	else:
		non_req_GNB(message, tech_msg)

def concl_msg(message):
	
	if message.text.find('/start') >= 0:
		start_msg(message)
		return
	if message.text in lst_GNB:
		append_to_us(message.from_user.id, message.text)
		info = get_us(message.from_user.id)
		if 'Плохо' in info.answers:
			markup = types.ReplyKeyboardMarkup()
			markup.add(types.KeyboardButton('Да'))
			markup.add(types.KeyboardButton('Нет'))
			msg = bot.send_message(message.chat.id, 'Вам что-то не понравилось, нам комментарий?', reply_markup = markup)
			bot.register_next_step_handler(msg, get_msg_about)
		else:
			msg = bot.send_message(message.chat.id, 'Велп')
	else:
		non_req_GNB(message, tech_msg)

def get_msg_about(message):

	if message.text in ['Да', 'Нет']:

		if message.text == 'Да':
			markup = types.ForceReply()
			msg = bot.send_message(message.chat.id, 'Ваш отзыв тут же попадёт к нашим менеджерам!', reply_markup = markup)
			bot.register_for_reply(msg, get_numb_subm)
		else:
			get_numb_subm(message)
	else:
		non_req_GNB(message, get_msg_about)
def get_numb_subm(message):

	msg_text = ''
	if message.text == 'Нет':
		msg_text = 'Сожалеем что наш сервис вас не устроил.'
	elif message.text.find('/start') >= 0:
		start_msg(message)
		return
	else:
		append_to_us(message.from_user.id, message.text, 'msg')
		if msg_text == '':
			msg_text = 'Спасибо за ваш отзыв, теперь - финальный этап. Поделитесь с нами вашим номером телефона чтобы мы могли вам ответить и помочь с проблемами.'
		markup = types.ReplyKeyboardMarkup()
		markup.add(types.KeyboardButton('Передать номер телефона', True))
		markup.add(types.KeyboardButton('Не предавать'))
		msg = bot.send_message(message.chat.id, msg_text, reply_markup = markup)
		bot.register_next_step_handler(msg, final_step)

def final_step(message):

	if type(message.contact) != type(None):
		append_to_us(message.from_user.id, message.contact.phone_number, 'numb')
		all = get_us(message.from_user.id).get_all()
		bot.send_message(message.chat.id, 'Спасибо за ваш отзыв, будем расти вместе с вами!', reply_markup = types.ReplyKeyboardRemove())
		proc_us(message.from_user.id)
	elif message.text == 'Не передавать':
		bot.send_message(message.chat.id, 'Нам будет труднее вас идентифицировать, но мы что-то придумаем')
	elif message.text.find('/start') >= 0:
		start_msg(message)
	else:
		non_req_GNB(message, final_step)



bot.polling()