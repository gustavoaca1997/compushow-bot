import sys
import os
import time
import telepot
from telepot.loop import MessageLoop, OrderedWebhook
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.delegate import pave_event_space, per_chat_id, create_open, include_callback_query_chat_id
import requests
from flask import Flask, request
from pprint import pprint
from queue import Queue
import psycopg2

TOKEN = os.environ.get('TOKEN')
URL = os.environ.get('URL')
SECRET = '/bot' + TOKEN
UPDATE_QUEUE = Queue()

# Token para el cuartico
TOKEN_CUARTICO = "chillbro2018"
PORT = os.environ.get('PORT')
SECRET = '/bot' + TOKEN
UPDATE_QUEUE = Queue()
DATABASE_URL = os.environ['DATABASE_URL']

PLAYLIST_URL = 'https://open.spotify.com/user/gustavoaca1997/playlist/4Qb026FvM0ieNz4FEFgqUr'
MSG_PLAYLIST = 'No estoy seguro de que me pides, pero seguro quieres escuchar esta maravillosa playlist: {}'\
    .format(PLAYLIST_URL)

#####################################
########### Funciones ###############
#####################################

## Funcion que checquea si el mensaje de texto es un comando
def is_command(text):
    return len(text) > 0 and text[0] == '/'

## Funcion que checkea si el comando es /start
def is_start(text):
    return is_command(text) and text[1:] == "start"

## Funcion que guarda o actualiza en la base de datos el usuario con su contraseña
def save_user(usuario, password):
    conn = psycopg2.connect("dbname={}".format(DATABASE_URL), sslmode='require')
    cur = conn.cursor()

    # Chequeamos si ya el usuario existe
    cur.execute('SELECT carnet FROM usuario WHERE carnet = %s;', (usuario, ))
    usuario_guardado = cur.fetchone()

    # Si no está en la base de datos, insertar
    if not usuario_guardado:
        cur.execute('INSERT INTO usuario (carnet, password) VALUES (%s, %s);', (usuario, password, ))
        return 1

    # Si no, actualizamos
    else:
        cur.execute('UPDATE usuario SET password = %s WHERE carnet = %s;', (password, usuario, ))
        return 0

#####################################
############### Bot #################
#####################################

class ChatSesion(telepot.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(ChatSesion, self).__init__(*args, **kwargs)

        # atributo que permite saber si se está esperando por el usuario y contraseña
        self.start = False

    # Manejador de mensajes
    def on_chat_message(self, msg):
        # Imprimir en consola mensaje recibido
        print('Mensaje recibido:')
        pprint(msg)

        # Obtener info basica del mensaje
        content_type, chat_type, chat_id = telepot.glance(msg)
        # bot.sendMessage(chat_id, '')

        # Si no es un chat privado, pasar
        if chat_type != 'private':
            return

        # Si el mensaje es texto
        if content_type == 'text':
            if self.start:
                try:
                    # Parseamos usuario y contraseña
                    usuario, password = msg['text'].split()

                    # Guardamos en la base de datos
                    if save_user(usuario, password):
                        bot.sendMessage(chat_id, 'Se registró exitosamente tu cuenta.')
                    else:
                        bot.sendMessage(chat_id, 'Se actualizó correctamente tu cuenta.')

                except:
                    bot.sendMessage(chat_id, 'Ocurrió un error leyendo el mensaje. Vuelve a intentarlo con el comando\
                    /start')

            if is_start(msg['text']):
                bot.sendMessage(chat_id, 'Por favor envíame tu nombre de usuario (e.g carnet) y tu contraseña (e.g cédula)\
                separadas por un espacio.')
                self.start = True


    def on_callback_query(self, msg):
        pass


app = Flask(__name__)
bot = telepot.DelegatorBot(TOKEN, [
    include_callback_query_chat_id(
        pave_event_space())(
            per_chat_id(), create_open, ChatSesion, timeout=100),
])
bot.message_loop(source=UPDATE_QUEUE)
webhook = OrderedWebhook(bot)
@app.route('/bot' + TOKEN, methods=['GET', 'POST'])
def pass_update():
    UPDATE_QUEUE.put(request.data)
    return 'ok'
try:
    bot.setWebhook()
except telepot.exception.TooManyRequestsError:
    pass

try:
    bot.setWebhook(URL+SECRET)
except telepot.exception.TooManyRequestsError:
    pass