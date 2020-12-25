import telebot
import sqlite3
import datetime as dt
import schedule
import time
from threading import Thread
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

	def __init__(self, t_id, from_, name, username = None):
		self.id = t_id
		self.from_ = from_
		self.answers = []
		self.message = None
		self.numb = None
		self.about = None
		self.name = name
		self.username = username
		self.cab = None
	def new_ans(self, answ):
		self.answers.append(answ)
	def new_msg(self, msg):
		self.message = msg
	def new_numb(self, numb):
		self.numb = numb
	def new_about(self, about):
		self.about = about
	def new_cab(self, cab):
		self.cab = cab
	def get_all(self):		
		return [self.id, self.from_, self.answers, self.message, self.numb, self.about, self.name, self.username, self.cab]


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
			elif fun == 'cab':
				x.new_cab(info)


def get_us(id):
	for x in us_answers:
		if x.id == id:
			return x
	else:
		return Noned

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

def proc_us(id):
	
	U_Info = get_us(id)
	m_text = ['', '', '']
	answ_var = ['Отлично', 'Хорошо', 'Плохо']
	comp_text = []
	table_names = ['Pos_Rev', 'Neu_Rev', 'Neg_Rev']
	#object
	res = c.execute("select Phone from Users where TG_Id = {}".format(U_Info.id))
	res = res.fetchall()
	if res != [(None,)] and U_Info.numb is None:
		U_Info.numb = res[0][0]
	elif res == [(None,)] and type(U_Info.numb) != type(None):
		c.execute("update Users set Phone = '{}' where TG_Id = {}".format(U_Info.numb, U_Info.id))
		db.commit()
	for x in range(len(U_Info.answers)):
		m_text[answ_var.index(U_Info.answers[x])] += quest[U_Info.about][x] + "\n"
	for x in m_text:
		if x == "":
			continue
		if U_Info.username is not None:
			us = "(@{})".format(U_Info.username)
		else:
			us = ""
		if U_Info.message is not None:
			um = "Сообщение: {}".format(U_Info.message)
		else:
			um = ""
		msg = '{} - {} {}\nОставил новый отзыв:\n\n{}\n\nОценил {}\n{}\n\n{}'.format(U_Info.name, U_Info.numb, us,m_text[m_text.index(x)], answ_var[m_text.index(x)], U_Info.from_, um)
		bot.send_message(chats_indx[m_text.index(x)], msg)
		c.execute("insert into {} (U_Id, Text, Date, About) values ({}, '{}', '{}', '{}')".format(
			table_names[m_text.index(x)],
			U_Info.id,
			U_Info.message,
			dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
			x))

	db.commit()


###SQL Functions###

def get_msg_by_Id(id_, tab, message):

	c.execute("select Text, Users.Name, Users.Surname, Users.Phone, Users.Object from {} inner join Users on U_Id = Users.Id where id = {}".format(tab, id_))
	a = c.fetchall()
	if len(a) == 0:
		bot.send_message(message.chat.id, 'Ошибка')
	else:
		bot.send_message(message.chat.id, 'asd')

def get_msg_by_Date(tab = 'Neg_Rev', date = None):
	print("select {}.*, Users.Name, Users.Phone from {} inner join Users on Users.TG_Id = {}.U_Id where date like '{}%'".format(tab, tab, tab, date))
	c.execute("select {}.*, Users.Name, Users.Phone from {} inner join Users on Users.TG_Id = {}.U_Id where date like '{}%'".format(tab, tab, tab, date))
	a = c.fetchall()
	print(a)

###Bot handlers###

@bot.message_handler(commands = ['chat_id'])
def get_chat_id(message):

	bot.send_message(message.chat.id, 'Айди этого чата:\n<code>{}</code>'.format(message.chat.id), parse_mode = "HTML")

def manage_msg(message):

	markup = types.ReplyKeyboardMarkup(None, True)
	markup.add(types.KeyboardButton('Статистика'))
	markup.add(types.KeyboardButton('Добавить пост'))
	markup.add(types.KeyboardButton('Управление пользователями'), types.KeyboardButton('Поиск отзывов'))
	msg = bot.send_message(message.chat.id, 'Панель управления:', reply_markup = markup)
	bot.register_for_reply(msg, manage_msg_1)

def manage_msg_1(message):

	lst = ['Добавить пост', 'Поиск отзывов', 'Управление пользователями', 'Статистика']
	if message.text in lst:
		if lst.index(message.text) == 0:
			msg = bot.send_message(message.chat.id, 'Ответьте на это сообщение постом который надо запланировать.')
			bot.register_for_reply(msg, sched_msg)
		elif lst.index(message.text) == 1:
			markup = types.ReplyKeyboardMarkup(None, True)
			markup.add(types.KeyboardButton('По дате'))
			markup.add(types.KeyboardButton('По номеру'))
			markup.add(types.KeyboardButton('По айди отзыва'), types.KeyboardButton('По оценке'))
			msg = bot.send_message(message.chat.id, 'Как будем искать?', reply_markup = markup)
			bot.register_for_reply(msg, search_msg)
		elif lst.index(message.text) == 2:
			bot.send_message(message.chat.id, 'Укажите номер пользователя или его Telegram ID')
		elif lst.index(message.text) == 3:
			bot.send_message(message.chat.id, 'За последнюю неделю:\n{} положительных\n{} нейтральных\n{} негативных\n\n{} комментариев\n\nВсего: {} -- {} -- {}')
	else:
		manage_msg(message)

def send_sched_msg(message, time):
	
	if int(dt.datetime.now().timestamp()) in range(int(time) - 15, int(time) + 15):
		bot.send_message(message.chat.id, 'Счед тут нада ({})'.format(message.message_id))
		schedule.clear(message.message_id)

def sched_msg(message):

	msg = bot.send_message(message.chat.id, 'Если вы подтверждаете это сообщение - ответьте на него с датой и временем отправки!')
	bot.register_for_reply(msg, conf_sched, message)

def conf_sched(message, send_msg):
	
	try:
		time = dt.datetime.fromisoformat(message.text + ":00")
		if time.timestamp() < dt.datetime.now().timestamp():
			msg = bot.send_message(message.chat.id, 'Было до этого!\n\nУкажите правильную дату и время ответив на это сообщение')
			bot.register_for_reply(msg, conf_sched, send_msg)
		else:
			bot.send_message(message.chat.id, 'Окей! (Чтобы удалить отложенное сообщение: /del_sched <code>{}</code>)'.format(send_msg.message_id), parse_mode = 'html')
			schedule.every(20).seconds.do(send_sched_msg, send_msg, time.timestamp()).tag(send_msg.message_id)
	except Exception as E:
		print(E)
		msg = bot.send_message(message.chat.id, 'Не могу разобрать это сооющение, ответьте на это в таком формате:\n\nГод-Месяц-День Час:Минута')
		bot.register_for_reply(msg, conf_sched, send_msg)

def search_msg(message):

	lst = ['По дате', 'По номеру', 'По айди отзыва', 'По оценке']
	if message.text in lst:
		if lst.index(message.text) == 0:
			msg = bot.send_message(message.chat.id, 'Укажите дату ответив на это сообщение в формате ИСО (Год-Мессяц-Дата)')
			bot.register_for_reply(msg, sch_date)
		elif lst.index(message.text) == 1:
			msg = bot.send_message(message.chat.id, 'Укажите номер в ответе на это сообщение')
			bot.register_for_reply(msg, sch_numb)
		elif lst.index(message.text) == 2:
			msg = bot.send_message(message.chat.id, 'Укажите номер (МБ промежуток?) ответив на это сообщение')
			bot.register_for_reply(msg, sch_id)
		elif lst.index(message.text) == 3:
			markup = get_GNB_markup()
			markup.one_time_keyboard = True
			msg = bot.send_message(message.chat.id, 'Укажите оценку из клавиатуры отвечая на это сообщение', reply_markup = markup)
			bot.register_for_reply(msg, get_GNB_rev)
	elif message.text == '/start':
		manage_msg(message)
	else:
		message.text = 'Поиск отзывов'
		manage_msg_1(message)

def sch_date(message):

	try:
		date = dt.date.fromisoformat(message.text)
		get_msg_by_Date(date = str(date))
	except:
		msg = bot.send_message(message.chat.id, 'Не могу понять эту дату, попробуйте ещё раз.')
		bot.register_for_reply(msg, sch_date)

def sch_numb(message):

	try:
		ph = message.text
		if ph[0:3] != "380":
			if ph[0] == '+':
				ph = ph[1:]
			else:
				ph = "38"+ph
		c.execute("select TG_Id from users where Phone = {}".format(ph))
		a = c.fetchall()
		msgs= ['', '', '']
		table_names = ['Pos_Rev', 'Neu_Rev', 'Neg_Rev']
		addi_names = ['Положительные:\n\n', 'Нейтральные:\n\n', 'Негативные:\n\n']
		for x in range(3):		
			c.execute("select {}.*, Name, Username from {} inner join Users on Users.TG_Id = {}.U_Id where U_Id = {}".format(table_names[x], table_names[x], table_names[x], a[0][0]))
			b = c.fetchall()
			for z in b:
				if msgs[x] == '':
					msgs[x] = addi_names[x]
				msgs[x] += "Отзыв №{}\n{}\n{} (@{})\nОтзыв: {}\n\n".format(z[0], z[3], z[4], z[5], z[2])
			bot.send_message(message.chat.id, msgs[x])
	except:
		None

def sch_id(message):

	c.execute("select * from Neg_Rev where Id = {}".format(message.text))
	a = c.fetchall()
	print(a)

def get_GNB_rev(message):

	if message.text in lst_GNB:

		if lst_GNB.index(message.text) == 0:
			c.execute('select * from Pos_Rev where Text not NULL')
		elif lst_GNB.index(message.text) == 1:
			c.execute('select * from Neu_Rev where Text not NULL')
		elif lst_GNB.index(message.text) == 2:
			c.execute('select * from Neg_Rev where Text not NULL')
		a = c.fetchall()
		print(a)

@bot.message_handler(commands = ['del_sched'])
def del_sched(message):

	if len(message.text.split()) == 2 and message.chat.id == -336427671:
		schedule.clear(int(message.text.split()[1]))
		bot.send_message(message.chat.id, 'Удалено отложенное сообщение')

@bot.message_handler(commands = ['start'])
def start_msg(message):

	if message.chat.id == -336427671:
		manage_msg(message)
		return
	a = message.text.split(' ')
	try:
		us_answers.remove(get_us(message.from_user.id))
	except:
		None
	b = c.execute("select * from Users where TG_Id = {}".format(message.from_user.id))
	if len(b.fetchall()) == 0:
		c.execute("insert into Users (Name, Surname, TG_Id, Username) values ('{}', '{}', {}, '{}')".format(
			message.from_user.first_name,
			message.from_user.last_name,
			message.from_user.id,
			message.from_user.username
			))
		db.commit()
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
				message.text = '/start'
				answ_start(message)
		elif message.text == 'Нет, не хочу':
			bot.send_message(message.chat.id, 'Очень жаль, помните что вы всегда можете оставить отзыв нам воспользовавшись коммандой /start')
		else:
			bot.send_message(message.chat.id, 'Вы не должны были это видеть (Если вы не игрались с коммандой /start - напишите поддержке)')
		return
	if message.text == 'Отзыв о всех':
		msg = bot.send_message(message.chat.id, 'Оцените качество обслуживания офис-менеджера', reply_markup = get_GNB_markup())
		bot.register_next_step_handler(msg, pult_msg)
	elif message.text == 'Отзыв о тревогах':
		msg = bot.send_message(message.chat.id, "Оцените качество отработки тревог на Вашем объекте", reply_markup = get_GNB_markup())
		bot.register_next_step_handler(msg, trev_msg)
	elif message.text == 'Отзыв о тех.группе':
		msg = bot.send_message(message.chat.id, 'Оцените качество работы технической группы', reply_markup = get_GNB_markup())
		bot.register_next_step_handler(msg, tech_rev_msg)
	else:
		markup = types.ReplyKeyboardMarkup()
		markup.add(types.KeyboardButton('Отзыв о всех'))
		markup.add(types.KeyboardButton('Отзыв о тревогах'))
		markup.add(types.KeyboardButton('Отзыв о тех.группе'))
		msg = bot.send_message(message.chat.id, 'Вам следует нажимать на кнопки снизу.\n\nЕсли они не работают напишите нашей службе поддержки или /start')
		bot.register_next_step_handler(msg, answ_start)

def tech_rev_msg(message):
	
	if message.text.find('/start') >= 0:
		start_msg(message)
		return
	if message.text in lst_GNB:
		us_answers.append(U_TH(message.from_user.id, '', message.from_user.first_name, message.from_user.username))
		append_to_us(message.from_user.id, message.text)
		append_to_us(message.from_user.id, 'tech', 'about')
		info = get_us(message.from_user.id)
		if 'Плохо' in info.answers:
			markup = types.ReplyKeyboardMarkup()
			markup.add(types.KeyboardButton('Да'))
			markup.add(types.KeyboardButton('Нет'))
			msg = bot.send_message(message.chat.id, 'Вам что-то не понравилось, нам комментарий?', reply_markup = markup)
			bot.register_next_step_handler(msg, get_msg_about)
		else:
			message.text = "-1testbug"
			get_numb_subm(message)
	else:
		non_req_GNB(message, trev_msg)

def trev_msg(message):

	if message.text.find('/start') >= 0:
		start_msg(message)
		return
	if message.text in lst_GNB:
		us_answers.append(U_TH(message.from_user.id, '', message.from_user.first_name, message.from_user.username))
		append_to_us(message.from_user.id, message.text)
		append_to_us(message.from_user.id, 'alert', 'about')
		info = get_us(message.from_user.id)
		if 'Плохо' in info.answers:
			markup = types.ReplyKeyboardMarkup()
			markup.add(types.KeyboardButton('Да'))
			markup.add(types.KeyboardButton('Нет'))
			msg = bot.send_message(message.chat.id, 'Вам что-то не понравилось, нам комментарий?', reply_markup = markup)
			bot.register_next_step_handler(msg, get_msg_about)
		else:
			message.text = "-1testbug"
			get_numb_subm(message)
	else:
		non_req_GNB(message, trev_msg)

def pult_msg(message):
	
	###Реализовать сбор данных###
	if message.text.find('/start') >= 0:
		start_msg(message)
		return
	if message.text in lst_GNB:
		us_answers.append(U_TH(message.from_user.id, '', message.from_user.first_name, message.from_user.username))
		append_to_us(message.from_user.id, message.text)
		append_to_us(message.from_user.id, 'all', 'about')
		msg = bot.send_message(message.chat.id, 'Оцените качество обслуживания операторов пульта', reply_markup = get_GNB_markup())
		bot.register_next_step_handler(msg, gbr_msg)
	else:
		non_req_GNB(message, pult_msg)

def gbr_msg(message):
	
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
			message.text = "-1testbug"
			get_numb_subm(message)
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
	if message.text != "-1testbug":
		append_to_us(message.from_user.id, message.text, 'msg')
	else:
		append_to_us(message.from_user.id, None, 'msg')
	if msg_text == '':
		msg_text = 'Спасибо за ваш отзыв, теперь - финальный этап. Поделитесь с нами вашим номером телефона чтобы мы могли вам ответить и помочь с проблемами.'
	markup = types.ReplyKeyboardMarkup()
	markup.add(types.KeyboardButton('Передать номер телефона', True))
	markup.add(types.KeyboardButton('Не передавать'))
	msg = bot.send_message(message.chat.id, msg_text, reply_markup = markup)
	bot.register_next_step_handler(msg, final_step)

def final_step(message):

	if type(message.contact) != type(None):
		append_to_us(message.from_user.id, message.contact.phone_number, 'numb')
		bot.send_message(message.chat.id, 'Спасибо за ваш отзыв, будем расти вместе с вами!', reply_markup = types.ReplyKeyboardRemove())
		proc_us(message.from_user.id)
		us_answers.remove(get_us(message.from_user.id))
	elif message.text == 'Не передавать':
		bot.send_message(message.chat.id, 'Нам будет труднее вас идентифицировать, но мы что-то придумаем')
		proc_us(message.from_user.id)
		us_answers.remove(get_us(message.from_user.id))
	elif message.text.find('/start') >= 0:
		start_msg(message)
	else:
		msg = bot.send_message(message.chat.id, 'Используйте кнопки снизу!')
		bot.register_next_step_handler(msg, final_step)

class MTread(Thread):

	def __init__(self, name):
		Thread.__init__(self)
		self.name = name
	def run(self):
		while True:
			schedule.run_pending()
			time.sleep(1)

name = 'schedule_thr'
schedthr = MTread(name)
schedthr.start()

bot.polling()