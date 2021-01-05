import telebot
import sqlite3
import random
import schedule
import time
import datetime
import ssl
import sys
import pandas
from threading import Thread
from telebot import types, util
from aiohttp import web

API_TOKEN = "1447763558:AAHAnuDaqHbDLyvEruZSxSre408DBOB_7vU"
WEBHOOK_HOST = "45.32.159.240"
WEBHOOK_PORT = 8443
WEBHOOK_LISTEN = '45.32.159.240'
WEBHOOK_SSL_CERT = './webhook_cert.pem'
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'

WEBHOOK_URL_BASE = "https://{}:{}".format(WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/{}/".format(API_TOKEN)

db = sqlite3.connect('db.db', check_same_thread=False)
c = db.cursor()

bot = telebot.TeleBot(API_TOKEN)

app = web.Application()
app.shutdown()
app.cleanup()


async def handle(request):
	if request.match_info.get('token') == bot.token:
		request_body_dict = await request.json()
		update = telebot.types.Update.de_json(request_body_dict)
		bot.process_new_updates([update])
		return web.Response()
	else:
		None


app.router.add_post('/{token}/', handle)

lst_GNB = ['Отлично', 'Хорошо', 'Плохо']

chats = {'Neg': '-1001280443571', 'Pos': '-1001435933763', 'Neu': '-1001472593128'}
chats_indx = ['-1001435933763', '-1001472593128', '-1001280443571']

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
		return None

def get_GNB_markup():
	''' Good, neutral, bad markup '''
	markup = types.ReplyKeyboardMarkup(one_time_keyboard = True)
	markup.add(types.KeyboardButton('Отлично'))
	markup.add(types.KeyboardButton('Хорошо'))
	markup.add(types.KeyboardButton('Плохо'))
	##markup.add(types.KeyboardButton('Не могу оценить')) Если есть возможность того что человек не контактировал с сотрудником

	return markup

def non_req_GNB(message, func):

	msg = bot.send_message(message.chat.id, 'Вам следует нажимать на кнопки снизу.\n\nЕсли они не работают напишите нашей службе поддержки или /start', reply_markup = get_GNB_markup())
	bot.register_next_step_handler(msg, func)

def proc_us(id, to_us):
	
	U_Info = get_us(id)
	m_text = ['', '', '']
	answ_var = ['Отлично', 'Хорошо', 'Плохо']
	comp_text = []
	table_names = ['Pos_Rev', 'Neu_Rev', 'Neg_Rev']
	res = c.execute("select Phone from Users where TG_Id = {}".format(U_Info.id))
	res = res.fetchall()
	if res != [(None,)] and U_Info.numb is None:
		U_Info.numb = res[0][0]
	elif res == [(None,)] and type(U_Info.numb) != type(None):
		print(U_Info.numb)
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
			um = "\nСообщение: {}\n".format(U_Info.message)
		else:
			um = ""
		r_id = c.execute("insert into Ids (For) values ('{}')".format(table_names[m_text.index(x)]))		
		r_id = r_id.lastrowid
		c.execute("insert into {} (Id, U_Id, Text, Date, About) values ({}, {}, '{}', '{}', '{}')".format(
			table_names[m_text.index(x)],
			r_id,
			U_Info.id,
			U_Info.message,
			datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
			x))
		msg = '{} - {} {}\nОставил новый отзыв:\n{}\nОценил {}\n{}{}Номер отзыва: {}\n\nId пользователя: <code>{}</code>\n\n'.format(U_Info.name, U_Info.numb, us,m_text[m_text.index(x)], answ_var[m_text.index(x)], U_Info.from_, um, r_id, U_Info.id)
		bot.send_message(chats_indx[m_text.index(x)], msg, parse_mode = 'html')
	db.commit()


###SQL Functions###

def get_msg_by_Date(message, date = None):
	
	msgs= ['', '', '']
	table_names = ['Pos_Rev', 'Neu_Rev', 'Neg_Rev']
	addi_names = ['Положительные:\n\n', 'Нейтральные:\n\n', 'Негативные:\n\n']
	for x in range(3):
		t = table_names[x]
		if type(date) == type(list()):
			c.execute("select {}.*, Users.Name, Users.Phone, Users.Username from {} inner join Users on Users.TG_Id = {}.U_Id where date between '{}' and '{}'".format(t, t, t, date[0], date[1]))
		else:
			c.execute("select {}.*, Users.Name, Users.Phone, Users.Username from {} inner join Users on Users.TG_Id = {}.U_Id where date like '{}%'".format(t, t, t, date))
		a = c.fetchall()
		if a == []:
			continue
		for z in a:
			z = list(z)
			if msgs[x] == '':
				msgs[x] = addi_names[x]
			if z[2] != 'None':
				z[2] = "Отзыв: " + z[2]
			else:
				z[2] = ""
			if z[6] == 'None':
				z[6] = ''
			if z[7] != 'None':
				z[7] = '(@{})'.format(z[7])
			else:
				z[7] = ''
			msgs[x] += "Отзыв №{}\n{}\n\nО:\n{}\n{} {} {}\n{}\n\nId пользователя: <code>{}</code>\n\n".format(z[0], z[3], z[4], z[5], z[6], z[7], z[2], z[1])
		for y in util.split_string(msgs[x], 3000):
			bot.send_message(message.chat.id, y, parse_mode = 'html')
	if msgs == ['', '', '']:
		bot.send_message(message.chat.id, 'За эту дату нет отзывов')
	message.text = '/start'
	start_msg(message)

###Bot handlers###

@bot.message_handler(commands = ['chat_id'])
def get_chat_id(message):

	bot.send_message(message.chat.id, 'Айди этого чата:\n<code>{}</code>'.format(message.chat.id), parse_mode = "HTML")

def get_db():

	lst_name = ['Пользователи', 'Положительные отзывы', 'Нейтральные отзывы', 'Негативные отзывы']
	lst_header = [['Айди Пользователя', 'Имя', 'Фамилия', 'Номер телфона', 'Номер объекта', 'Ник'],
			 ['Id', 'Айди пользователя', 'Сообщение', 'Время получения', 'О'],
			 ['Id', 'Айди пользователя', 'Сообщение', 'Время получения', 'О'],
			 ['Id', 'Айди пользователя', 'Сообщение', 'Время получения', 'О']]
	lst_req = [
		'select * from users',
		'select * from Pos_Rev',
		'select * from Neu_Rev',
		'select * from Neg_Rev'
		]

	df_lst = []

	for x in range(4):
		c.execute(lst_req[x])
		a = c.fetchall()
		df_lst.append(pandas.DataFrame(a, columns = lst_header[x]))
	
	with pandas.ExcelWriter('cur_db.xlsx') as writer:
		df_lst[0].to_excel(writer, sheet_name = lst_name[0])
		df_lst[1].to_excel(writer, sheet_name = lst_name[1])
		df_lst[2].to_excel(writer, sheet_name = lst_name[2])
		df_lst[3].to_excel(writer, sheet_name = lst_name[3])

	file1 = open('cur_db.xlsx', 'rb')

	return file1

def manage_msg(message):

	markup = types.ReplyKeyboardMarkup(None, True)
	markup.add(types.KeyboardButton('Статистика'))
	markup.add(types.KeyboardButton('Добавить пост'))
	markup.add(types.KeyboardButton('Управление пользователями'), types.KeyboardButton('Поиск отзывов'))
	markup.add(types.KeyboardButton('Получить файл базы'))
	msg = bot.send_message(message.chat.id, 'Панель управления:', reply_markup = markup)
	bot.register_for_reply(msg, manage_msg_1)

def manage_msg_1(message):

	lst = ['Добавить пост', 'Поиск отзывов', 'Управление пользователями', 'Статистика', "Получить файл базы"]
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
			markup = types.ForceReply()
			msg = bot.send_message(message.chat.id, 'Укажите номер пользователя или его Telegram ID', reply_markup = markup)
			bot.register_for_reply(msg, edit_us_msg)
		elif lst.index(message.text) == 3:
			table_names = ['Pos_Rev', 'Neu_Rev', 'Neg_Rev']
			count_week = [0, 0, 0, 0]
			count_all = [0, 0, 0]
			for name in table_names:
				c.execute("select count(Id) from {} where date between '{}' and '{}'".format(name, datetime.date.today() - datetime.timedelta(7), datetime.date.today() + datetime.timedelta(1)))
				a = c.fetchall()
				count_week[table_names.index(name)] = a[0][0]
				c.execute("select count(Id) from {} where (date between '{}' and '{}') and (Text != 'None')".format(name, datetime.date.today() - datetime.timedelta(7), datetime.date.today() + datetime.timedelta(1)))
				b = c.fetchall()
				count_week[3] += int(b[0][0])
				c.execute("select count(Id) from {}".format(name))
				z = c.fetchall()
				count_all[table_names.index(name)] = z[0][0]
			bot.send_message(message.chat.id, 'За последнюю неделю:\n{} положительных\n{} нейтральных\n{} негативных\n\n{} комментариев\n\nВсего\n{} положительных\n{} нейтральных\n{} негативных'.format(
				count_week[0],
				count_week[1],
				count_week[2],
				count_week[3],
				count_all[0],
				count_all[1],
				count_all[2]
				))
			message.text = '/start'
			start_msg(message)
		elif lst.index(message.text) == 4:
			bot.send_document(message.chat.id, get_db())
			message.text = '/start'
			start_msg(message)
	else:
		manage_msg(message)

def send_us_info_by(message, a):

	try:
		if a != []:
				a = list(a[0])
				markup = types.ReplyKeyboardMarkup(None, True, True)
				markup.add(types.KeyboardButton('Изменить Имя'))
				markup.add(types.KeyboardButton('Изменить Номер'))
				markup.add(types.KeyboardButton('Изменить Участок'))
				markup.add(types.KeyboardButton('Удалить запись'))
				markup.add(types.KeyboardButton('В главное меню'))
				if a[5] != None:
					a[5] = '@' + a[5]
				else:
					a[5] = ''
				if a[4] != None:
					a[4] = 'Участок: ' + a[4]
				else:
					a[4] = ''
				if a[3] != None:
					a[3] = 'Номер: ' + a[3]
				else:
					a[3] = ''
				if a[2] == None:
					a[2] = ''
				msg = bot.send_message(message.chat.id, 'Пользователь: {}\n{} {}\n\n{}\n{}\n{}'.format(a[0], a[1], a[2], a[3], a[5], a[4]), reply_markup = markup)
				bot.register_for_reply(msg, proc_edit_us, a[0])
				return True
	except:
		return False

def proc_edit_us(message, u_id):

	lst = ['Изменить Имя', 'Изменить Номер', 'Изменить Участок', 'Удалить запись', 'В главное меню']

	if message.text in lst:

		if lst.index(message.text) == 0:
			markup = types.ForceReply()
			msg = bot.send_message(message.chat.id, 'Укажите новые данные для имени и фамилии (через пробел)', reply_markup = markup)
			bot.register_for_reply(msg, edit_us_prof, 0, u_id)
		elif lst.index(message.text) == 1:
			markup = types.ForceReply()
			msg = bot.send_message(message.chat.id, 'Укажите новый номер пользователя', reply_markup = markup)
			bot.register_for_reply(msg, edit_us_prof, 1, u_id)
		elif lst.index(message.text) == 2:
			markup = types.ForceReply()
			msg = bot.send_message(message.chat.id, 'Укажите новый участок пользователя', reply_markup = markup)
			bot.register_for_reply(msg, edit_us_prof, 2, u_id)
		elif lst.index(message.text) == 3:
			markup = types.ReplyKeyboardMarkup(None, True, True)
			rand_pic = random.randint(0, 3)
			for x in range(0, 4):
				if x != rand_pic:
					markup.add(types.KeyboardButton('Отмена'))
				else:
					markup.add(types.KeyboardButton('Подтверждаю'))
			msg = bot.send_message(message.chat.id, 'Подтверждаете удаление? (Человек не будет больше получать уведомления и тд!)', reply_markup = markup)
			bot.register_for_reply(msg, del_user_prof, u_id)
		elif lst.index(message.text) == 4:
			message.text = '/start'
			start_msg(message)

def del_user_prof(message, u_id):

	if message.text == 'Подтверждаю':
		c.execute('delete from users where TG_Id = {}'.format(u_id))
		for x in ['Pos_Rev', 'Neu_Rev', 'Neg_Rev']:
			c.execute('delete from {} where U_Id = {}'.format(x, u_id))
		db.commit()
		bot.send_message(message.chat.id, 'Успешно удалён пользователь')
	message.text = '/start'
	start_msg(message)

def edit_us_prof(message, what, u_id):

	what_tab = ['', 'phone', 'object']

	if what == 0:
		if len(message.text.split()) > 1:
			sur = ", Surname = '{}'".format(message.text.split()[1])
		else:
			sur = ''
		c.execute("update Users set Name = '{}'{} where TG_Id = {}".format(message.text.split()[0], sur, u_id))
	else:
		if what == 1:
			if message.text[0] == '0':
				paste = "38" + message.text
			elif message.text[0] == '+':
				paste = message.text[1:]
			elif message.text[0:3] == '380':
				paste = message.text
		else:
			paste = message.text
		c.execute("update Users set {} = '{}' where TG_Id = {}".format(what_tab[what], paste, u_id))
	db.commit()
	message.text = '/start'
	start_msg(message)

def edit_us_msg(message):

	if message.text[0] in ['0', '+'] or message.text[0:3] == '380':
		if message.text[0] == '0':
			ph = "38" + message.text
		elif message.text[0] == '+':
			ph = message.text[1:]
		elif message.text[0:3] == '380':
			ph = message.text			
		c.execute("select * from Users where Phone = '{}'".format(ph))
		a = c.fetchall()
		if send_us_info_by(message, a) == True:
			None
		else:
			bot.send_message(message.chat.id, 'Пользователя с таким номером нет')
			message.text = '/start'
			start_msg(message)
	else:
		try:
			int(message.text)
		except:
			message.text = '-1'
		c.execute("select * from Users where TG_Id = {}".format(message.text))
		a = c.fetchall()
		if send_us_info_by(message, a) == True:
			None
		else:
			bot.send_message(message.chat.id, 'Пользователя с таким Id нет')
			message.text = '/start'
			start_msg(message)

def html_text(text, entities):
        """
        Author: @sviat9440
        Updaters: @badiboy
		"""

        if not entities:
            return text

        _subs = {
            "bold"     : "<b>{text}</b>",
            "italic"   : "<i>{text}</i>",
            "pre"      : "<pre>{text}</pre>",
            "code"     : "<code>{text}</code>",
            #"url"      : "<a href=\"{url}\">{text}</a>", # @badiboy plain URLs have no text and do not need tags
            "text_link": "<a href=\"{url}\">{text}</a>",
            "strikethrough": "<s>{text}</s>",
            "underline":     "<u>{text}</u>"
 	    }
         
        utf16_text = text.encode("utf-16-le")
        html_text = ""

        def func(upd_text, subst_type=None, url=None, user=None):
            upd_text = upd_text.decode("utf-16-le")
            if subst_type == "text_mention":
                subst_type = "text_link"
                url = "tg://user?id={0}".format(user.id)
            elif subst_type == "mention":
                url = "https://t.me/{0}".format(upd_text[1:])
            upd_text = upd_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            if not subst_type or not _subs.get(subst_type):
                return upd_text
            subs = _subs.get(subst_type)
            return subs.format(text=upd_text, url=url)

        offset = 0
        for entity in entities:
            if entity.offset > offset:
                html_text += func(utf16_text[offset * 2 : entity.offset * 2])
                offset = entity.offset
                html_text += func(utf16_text[offset * 2 : (offset + entity.length) * 2], entity.type, entity.url, entity.user)
                offset += entity.length
            elif entity.offset == offset:
                html_text += func(utf16_text[offset * 2 : (offset + entity.length) * 2], entity.type, entity.url, entity.user)
                offset += entity.length
            else:
                # TODO: process nested entities from Bot API 4.5
                # Now ignoring them
                pass
        if offset * 2 < len(utf16_text):
            html_text += func(utf16_text[offset * 2:])
        return html_text

def send_sched_msg(message, time):
	
	c.execute("select TG_Id from Users")
	a = c.fetchall()
	if message.animation is not None:
		if int(datetime.datetime.now().timestamp()) in range(int(time) - 15, int(time) + 15):
			for x in a:
				bot.send_animation(x[0], message.animation.file_id, caption = html_text(message.caption, message.caption_entities), parse_mode = 'html')
			schedule.clear(message.message_id)
	elif message.audio is not None:
		if int(datetime.datetime.now().timestamp()) in range(int(time) - 15, int(time) + 15):
			for x in a:
				bot.send_audio(x[0], message.audio.file_id, caption = html_text(message.caption, message.caption_entities), parse_mode = 'html')
			schedule.clear(message.message_id)
	elif message.photo is not None:
		if int(datetime.datetime.now().timestamp()) in range(int(time) - 15, int(time) + 15):
			for x in a:
				bot.send_photo(x[0], message.photo[-1].file_id, caption = html_text(message.caption, message.caption_entities), parse_mode = 'html')
			schedule.clear(message.message_id)
	elif message.sticker is not None:
		if int(datetime.datetime.now().timestamp()) in range(int(time) - 15, int(time) + 15):
			for x in a:
				bot.send_sticker(x[0], message.sticker.file_id)
		schedule.clear(message.message_id)
	elif	 message.text is not None:
		if int(datetime.datetime.now().timestamp()) in range(int(time) - 15, int(time) + 15):
			for x in a:
					bot.send_message(x[0], html_text(message.text, message.entities), parse_mode = 'html')
			schedule.clear(message.message_id)
	elif message.video is not None:
		if int(datetime.datetime.now().timestamp()) in range(int(time) - 15, int(time) + 15):
			for x in a:
				bot.send_video(x[0], message.video.file_id, caption = html_text(message.caption, message.caption_entities), parse_mode = 'html')
			schedule.clear(message.message_id)
	elif message.voice is not None:
		if int(datetime.datetime.now().timestamp()) in range(int(time) - 15, int(time) + 15):
			for x in a:
				bot.send_voice(x[0], message.voice.file_id)
			schedule.clear(message.message_id)
	

def sched_msg(message):

	msg = bot.send_message(message.chat.id, 'Если вы подтверждаете это сообщение - ответьте на него с датой и временем отправки!')
	bot.register_for_reply(msg, conf_sched, message)

def conf_sched(message, send_msg):
	
	try:
		time = datetime.datetime.strptime(message.text, '%d.%m.%y %H:%M')
		if time.timestamp() < datetime.datetime.now().timestamp():
			msg = bot.send_message(message.chat.id, 'Было до этого!\n\nУкажите правильную дату и время ответив на это сообщение')
			bot.register_for_reply(msg, conf_sched, send_msg)
		else:
			bot.send_message(message.chat.id, 'Окей! (Чтобы удалить отложенное сообщение: /del_sched <code>{}</code>)'.format(send_msg.message_id), parse_mode = 'html')
			schedule.every(10).seconds.do(send_sched_msg, send_msg, time.timestamp()).tag(send_msg.message_id)
			message.text = '/start'
			start_msg(message)
	except Exception as E:
		print(E)
		msg = bot.send_message(message.chat.id, 'Не могу разобрать это сообщение, ответьте на это в таком формате:\n\nГод-Месяц-День Час:Минута')
		bot.register_for_reply(msg, conf_sched, send_msg)

def search_msg(message):

	lst = ['По дате', 'По номеру', 'По айди отзыва', 'По оценке']
	if message.text in lst:
		if lst.index(message.text) == 0:
			markup = types.ForceReply()
			msg = bot.send_message(message.chat.id, 'Укажите дату (или промежуток) ответив на это сообщение', reply_markup = markup)
			bot.register_for_reply(msg, sch_date)
		elif lst.index(message.text) == 1:
			markup = types.ForceReply()
			msg = bot.send_message(message.chat.id, 'Укажите номер в ответе на это сообщение', reply_markup = markup)
			bot.register_for_reply(msg, sch_numb)
		elif lst.index(message.text) == 2:
			markup = types.ForceReply()
			msg = bot.send_message(message.chat.id, 'Укажите номер отзыва ответив на это сообщение', reply_markup = markup)
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

	sep_date = message.text.split('-')
	if len(sep_date) > 1:
		try:
			date_1 = datetime.datetime.strptime(sep_date[0].replace(' ', ''), '%d.%m.%y')
			date_2 = datetime.datetime.strptime(sep_date[1].replace(' ', ''), '%d.%m.%y')
			get_msg_by_Date(message, [date_1.date(), date_2.date()])
			return
		except Exception as E:
			print(E)
			msg = bot.send_message(message.chat.id, 'Не могу понять этот промежуток, попробуйте ещё раз.\n\n01.01.2-05.03.21')
			bot.register_for_reply(msg, sch_date)

	try:
		date = datetime.datetime.strptime(message.text, '%d.%m.%y')
		get_msg_by_Date(message, date = str(date.date()))
	except Exception as E:
		print(E)
		msg = bot.send_message(message.chat.id, 'Не могу понять эту дату, попробуйте ещё раз.')
		bot.register_for_reply(msg, sch_date)

def send_lists(message, u_id):
	
	if u_id == -1:
			bot.send_message(message.chat.id, 'Нет отзывов по указанному номеру')
			message.text = '/start'
			start_msg(message)
			return
	try:
		msgs= ['', '', '']
		table_names = ['Pos_Rev', 'Neu_Rev', 'Neg_Rev']
		addi_names = ['Положительные:\n\n', 'Нейтральные:\n\n', 'Негативные:\n\n']
		for x in range(3):		
			c.execute("select {}.*, Name, Username from {} inner join Users on Users.TG_Id = {}.U_Id where U_Id = {}".format(table_names[x], table_names[x], table_names[x], u_id))
			b = c.fetchall()
			for z in b:
				z = list(z)
				if msgs[x] == '':
					msgs[x] = addi_names[x]
				if z[2] != 'None':
					z[2] = "Отзыв: " + z[2]
				else:
					z[2] = ""
				msgs[x] += "Отзыв №{}\n{}\n\nО:\n{}\n{} (@{})\n{}\n\n".format(z[0], z[3], z[4], z[5], z[6], z[2])
			for y in util.split_string(msgs[x], 3000):
				bot.send_message(message.chat.id, y)
		message.text = '/start'
		start_msg(message)
	except Exception as E:
		bot.send_message(message.chat.id, E)
		
def sch_numb(message):

	ph = message.text
	if ph[0:3] != "380":
		if ph[0] == '+':
			ph = ph[1:]
		else:
			ph = "38"+ph
	c.execute("select TG_Id from users where Phone = {}".format(ph))
	a = c.fetchall()
	try:
		send_lists(message, a[0][0])
	except:
		send_lists(message, -1)

def sch_id(message):

	a = c.fetchall()
	msgs = ['', '', '']
	table_names = ['Pos_Rev', 'Neu_Rev', 'Neg_Rev']
	addi_names = ['Положительные:\n\n', 'Нейтральные:\n\n', 'Негативные:\n\n']
	try:
		int(message.text)
		for x in range(3):
			c.execute("select {}.*, Name, Username, Phone from {} inner join Users on Users.TG_Id = {}.U_Id where Id = {}".format(table_names[x], table_names[x], table_names[x], message.text))
			z = c.fetchall()
			if z == []:
				continue
			else:
				z = list(z[0])
			msgs[x] = addi_names[x]
			if z[2] != 'None':
				z[2] = "Отзыв: " + z[2]
			else:
				z[2] = ""
			if z[7] == 'None':
				z[7] = ''
			if z[6] != 'None':
				z[6] = '(@{})'.format(z[6])
			else:
				z[6] = ''
			msgs[x] += "Отзыв №{}\n{}\n\nО:\n{}\n{} {} {}\n{}\n{}\n\n".format(z[0], z[3], z[4], z[5], z[7], z[6], z[1], z[2])
			for y in util.split_string(msgs[x], 3000):
					bot.send_message(message.chat.id, y)
		if msgs == ['', '', '']:
			bot.send_message(message.chat.id, 'Нет отзывов с таким айди')
		message.text = '/start'
		start_msg(message)
	except Exception as E:
		bot.send_message(message.chat.id, 'Неверно указан номер отзыва.')
		message.text = '/start'
		start_msg(message)

def get_GNB_rev(message):

	if message.text in lst_GNB:

		addi_names = ['Положительные:\n\n', 'Нейтральные:\n\n', 'Негативные:\n\n']

		if lst_GNB.index(message.text) == 0:
			c.execute("select Pos_Rev.*, Name, Username from Pos_Rev inner join Users on Users.TG_Id = Pos_Rev.U_Id where date between '{}' and '{}'".format(datetime.date.today() - datetime.timedelta(7), datetime.date.today() + datetime.timedelta(1)))
			addi_names = addi_names[0]
		elif lst_GNB.index(message.text) == 1:
			c.execute("select Neu_Rev.*, Name, Username from Neu_Rev inner join Users on Users.TG_Id = Neu_Rev.U_Id where date between '{}' and '{}'".format(datetime.date.today() - datetime.timedelta(7), datetime.date.today()  + datetime.timedelta(1)))
			addi_names = addi_names[1]
		elif lst_GNB.index(message.text) == 2:
			c.execute("select Neg_Rev.*, Name, Username from Neg_Rev inner join Users on Users.TG_Id = Neg_Rev.U_Id where date between '{}' and '{}'".format(datetime.date.today() - datetime.timedelta(7), datetime.date.today()  + datetime.timedelta(1)))
			addi_names = addi_names[2]
		a = c.fetchall()
		if a == []:
			return
		msg = ''
		for z in a:
			z = list(z)
			if msg == '':
				msg = addi_names
			if z[2] != 'None':
				z[2] = "Отзыв: " + z[2]
			else:
				z[2] = ""
			msg += "Отзыв №{}\n{}\n\nО:\n{}\n{} (@{})\n{}\n\n".format(z[0], z[3], z[4], z[5], z[6], z[2])
		for y in util.split_string(msg, 3000):
			bot.send_message(message.chat.id, y)
		message.text = '/start'
		start_msg(message)
	else:
		markup = get_GNB_markup()
		markup.one_time_keyboard = True
		msg = bot.send_message(message.chat.id, 'Не понял ввод. Выбирайте из кнпок ниже.', reply_markup = markup)
		bot.register_for_reply(msg, get_GNB_rev)

@bot.message_handler(commands = ['del_sched'])
def del_sched(message):

	if len(message.text.split()) == 2 and message.chat.id == -336427671:
		schedule.clear(int(message.text.split()[1]))
		bot.send_message(message.chat.id, 'Удалено отложенное сообщение')

@bot.message_handler(commands = ['start'])
def start_msg(message):

	if message.chat.id == -1001352923742:
		manage_msg(message)
		return
	if message.chat.type != 'private':
		bot.send_message(message.chat.id, 'К сожалению я не могу работать в групповых чатах. Напишите мне в личные сообщения.')
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
		markup = types.ReplyKeyboardMarkup(one_time_keyboard = True)
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
			markup = types.ReplyKeyboardMarkup(one_time_keyboard = True)
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
			markup = types.ReplyKeyboardMarkup(one_time_keyboard = True)
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
			markup = types.ReplyKeyboardMarkup(one_time_keyboard = True)
			markup.add(types.KeyboardButton('Да'))
			markup.add(types.KeyboardButton('Нет'))
			msg = bot.send_message(message.chat.id, 'Вам что-то не понравилось, оставите нам комментарий?', reply_markup = markup)
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
	c.execute("select phone from Users where TG_Id = {}".format(message.from_user.id))
	a = c.fetchall()
	if a != [(None, )]:
		message.text = 'Не передавать'
		final_step(message)
		return
	markup = types.ReplyKeyboardMarkup(one_time_keyboard = True)
	markup.add(types.KeyboardButton('Передать номер телефона', True))
	markup.add(types.KeyboardButton('Не передавать'))
	msg = bot.send_message(message.chat.id, msg_text, reply_markup = markup)
	bot.register_next_step_handler(msg, final_step)

def final_step(message):

	markup = types.InlineKeyboardMarkup()
	markup.add(types.InlineKeyboardButton('Вернуться на сайт', "https://centr.od.ua/ua/"))
	markup.add(types.InlineKeyboardButton('Оставить новый отзыв', callback_data = 'new_resp'))
	markup.add(types.InlineKeyboardButton('Связаться с менеджером', callback_data = 'call_mgr'))
	
	if type(message.contact) != type(None):
		append_to_us(message.from_user.id, message.contact.phone_number[1:], 'numb')
		msg = bot.send_message(message.chat.id, 'Спасибо за ваш отзыв, будем расти вместе с вами!', reply_markup = markup)
		proc_us(message.from_user.id, message.from_user.id)
		us_answers.remove(get_us(message.from_user.id))
	elif message.text == 'Не передавать':
		msg = bot.send_message(message.chat.id, 'Спасибо за ваш отзыв, будем расти вместе с вами!', reply_markup = markup)
		proc_us(message.from_user.id, message.from_user.id)
		us_answers.remove(get_us(message.from_user.id))
	elif message.text.find('/start') >= 0:
		start_msg(message)
	else:
		msg = bot.send_message(message.chat.id, 'Используйте кнопки снизу!')
		bot.register_next_step_handler(msg, final_step)

@bot.callback_query_handler(func=lambda call: True)
def handle_msg(call):

	bot.answer_callback_query(call.id, 'Обрабатываю')
	if call.data == 'new_resp':
		call.message.text = '/start'
		start_msg(call.message)
	elif call.data == 'call_mgr':
		bot.send_message(call.message.chat.id, 'Желаю вам здоровья и побыстрее найти номер менеджера)')

class MTread(Thread):

	def __init__(self, name):
		Thread.__init__(self)
		self.name = name
	def run(self):
		while True:
			schedule.run_pending()
			time.sleep(1)

name = 'schedule_thr'
schedatetimehr = MTread(name)
schedatetimehr.start()

#bot.polling()

bot.enable_save_next_step_handlers(delay=1)
bot.enable_save_reply_handlers(delay = 1)

# Load next_step_handlers from save file (default "./.handlers-saves/step.save")
# WARNING It will work only if enable_save_next_step_handlers was called!
bot.load_next_step_handlers()
bot.load_reply_handlers()

bot.remove_webhook()

bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))

context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.load_cert_chain(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV)
web.run_app(
    app,
    host=WEBHOOK_LISTEN,
    port=WEBHOOK_PORT,
    ssl_context=context,
)