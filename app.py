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

## Mensaje de ayuda
HELP = """Bienvenid@ a la mejor experiencia del año: 
🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟
🌸COMPUSHOW 2018🌈
🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟
Soy un bot creado para ayudarte en el proceso de votación. Lo primero que debes hacer es ejecutar el comando /login y seguir las instrucciones.
"""

#####################################
############ Variables Globales######
#####################################
usuarios_esperando = {}

#####################################
########### Funciones ###############
#####################################

## Funcion que checquea si el mensaje de texto es un comando
def is_command(text):
    return len(text) > 0 and text[0] == '/'

## Funcion que checkea si el comando es /start
def is_login(text):
    return is_command(text) and text[1:] == "login"

## Funcion que chequea si el comando es /help
def is_help(text):
    return is_command(text) and text[1:] == "help"

## Funcion que guarda o actualiza en la base de datos el usuario con su contraseña
def save_user(usuario, password, chat_id):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()

    # Chequeamos si ya el usuario existe
    cur.execute('SELECT carnet FROM usuario WHERE carnet = %s;', (usuario, ))
    usuario_guardado = cur.fetchone()[0]

    # Si no está en la base de datos, insertar
    if not usuario_guardado:
        cur.execute('INSERT INTO usuario (carnet, password, chat_id) VALUES (%s, %s, %s);', (usuario, password, chat_id, ))

        conn.commit()
        cur.close()
        conn.close()
        return 1

    # Si no, actualizamos
    else:
        cur.execute('UPDATE usuario SET password = %s, chat_id = %s WHERE carnet = %s;', (password, chat_id, usuario, ))
        conn.commit()
        cur.close()
        conn.close()
        return 0

## Funcion que chequea si se está esperando que el usuario envíe sus datos de usuario
def is_waiting(chat_id):
    return usuarios_esperando.get(chat_id, False)

#####################################
############### Bot #################
#####################################

class ChatSesion(telepot.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(ChatSesion, self).__init__(*args, **kwargs)

    # Manejador de mensajes
    def on_chat_message(self, msg):
        pprint(usuarios_esperando)
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
            if is_waiting(chat_id):
                # Actualizamos diccionario
                usuarios_esperando[chat_id] = False

                try:
                    # Parseamos usuario y contraseña
                    usuario, password = msg['text'].split()
                    # Guardamos en la base de datos
                    if save_user(usuario, password, str(chat_id)):
                        bot.sendMessage(chat_id, 'Se registró exitosamente tu cuenta.')
                    else:
                        bot.sendMessage(chat_id, 'Se actualizó correctamente tu cuenta.')

                except ValueError:
                    bot.sendMessage(chat_id, 'Ocurrió un error leyendo el mensaje. Vuelve a intentarlo con el comando /start')

                except psycopg2.DataError as e:
                    bot.sendMessage(chat_id, 'Ocurrió un error modificando la base de datos: <code>{}</code>'.format(e), parse_mode='HTML')

            elif is_login(msg['text']):
                # Actualizamos el diccionario
                usuarios_esperando[chat_id] = True
                bot.sendMessage(chat_id, 'Por favor envíame tu nombre de usuario (e.g carnet) y tu contraseña (e.g cédula) separadas por un espacio.')

            elif is_help(msg['text']):
                bot.sendMessage(chat_id, HELP)

            else:
                bot.sendMessage(chat_id, 'Si necesitas ayuda en como comunicarte conmigo, usa el comando /help mientras escuchas esta brutal playlist: {}'.format(PLAYLIST_URL))



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