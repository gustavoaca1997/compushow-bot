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
import json
import re
from html import escape

TOKEN = os.environ.get('TOKEN')
URL = os.environ.get('URL')
SECRET = '/bot' + TOKEN
UPDATE_QUEUE = Queue()

# Token para el cuartico
PORT = os.environ.get('PORT')
SECRET = '/bot' + TOKEN
UPDATE_QUEUE = Queue()
DATABASE_URL = os.environ['DATABASE_URL']
COMPUSHOW_URL = os.environ.get('COMPUSHOW_URL')

PLAYLIST_URL = 'https://open.spotify.com/user/gustavoaca1997/playlist/4Qb026FvM0ieNz4FEFgqUr'

## Mensaje de ayuda
HELP = """Bienvenid@ a la mejor experiencia del año: 
🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟
🌸COMPUSHOW 2018🌈
🌟🌟🌟🌟🌟🌟🌟🌟🌟🌟
Soy un bot creado para ayudarte en el proceso de votación. 
Lo primero que debes hacer es ejecutar el comando /login y seguir las instrucciones.
Para ver las categorías disponibles para votar, utiliza el comando /categorias.
"""

## Diccionario de emojis
EMOJIS = {
    'CompuAdoptado': '👶',
    'CompuBully': '😈',
    'CompuButt': '🍑',
    'CompuCartoon': '🐼',
    'CompuCono': '🚧',
    'CompuLolas': '👙',
    'CompuFitness': '🏃‍♀🏃‍',
    'CompuGordito': '🍔',
    'CompuLove': '💑',
    'CompuMaster': '👩‍🏫👨‍🏫',
    'CompuMami': '👸🏽',
    'CompuPapi': '🙎🏻‍♂️',
    'CompuPro': '💪🏼',
    'CompuProductista': '👷🏻‍',
    'CompuTukky': '👨🏾‍🎤',
    'CompuTeam': '👱🏽‍♀👨👩🏻',
    'CompuChévere': '👻'
}

#####################################
########### Funciones ###############
#####################################

## Funcion que checquea si el mensaje de texto es un comando
def is_command(text):
    return len(text) > 0 and text[0] == '/'

## Funcion que checkea si el comando es /login
def is_login(text, chat_id):
    chat_id = str(chat_id)
    ret = is_command(text) and text[1:] == "login"

    # Si es /login
    if ret:
        # Actualizamos la base de datos
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()

        cur.execute('SELECT chat_id FROM usuario WHERE chat_id = %s;', (chat_id, ))
        usuario_guardado = cur.fetchone()

        if usuario_guardado:
            cur.execute('UPDATE usuario SET is_waiting = true WHERE chat_id = %s;', (chat_id, ))
        else:
            cur.execute('INSERT INTO usuario (chat_id, is_waiting) VALUES (%s, true);', (chat_id, ))
        conn.commit()
        cur.close()
        conn.close()

    return ret


## Funcion que chequea si el comando es /help
def is_help(text):
    return is_command(text) and text[1:] == "help"

## Funcion que chequea si el comando es /categorias
def is_categoria(text):
    return is_command(text) and text[1:] == "categorias"

## Funcion que guarda o actualiza en la base de datos el usuario con su contraseña
def save_user(usuario, password, chat_id):
    data = {
        'carnet': usuario,
        'password': password,
        'token': TOKEN
    }
    r = requests.post(COMPUSHOW_URL + 'login_bot/', data=data)
    print(r.text)
    response = r.json()
    pprint(response)
    if not response['valid']:
        if response.get('error', False):
            bot.sendMessage(chat_id, response['error'])
        else:
            bot.sendMessage(chat_id, 'Parece que te equivocaste con los datos. Intenta de nuevo con /login.')
        return 0

    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()

    # Chequeamos si ya el usuario existe
    cur.execute('SELECT chat_id FROM usuario WHERE chat_id = %s;', (chat_id, ))
    row = cur.fetchone()
    if row:
        usuario_guardado = row[0]
    else:
        usuario_guardado = False

    # Si no está en la base de datos, insertar
    if not usuario_guardado:
        cur.execute('INSERT INTO usuario (carnet, password, chat_id) VALUES (%s, %s, %s);', (usuario, password, chat_id, ))

        conn.commit()
        cur.close()
        conn.close()
        return 1

    # Si no, actualizamos
    else:
        cur.execute('UPDATE usuario SET password = %s, carnet = %s WHERE chat_id = %s;', (password, usuario, chat_id, ))
        conn.commit()
        cur.close()
        conn.close()
        return 2

## Funcion que chequea si se está esperando que el usuario envíe sus datos de usuario
def is_waiting(chat_id):
    # return usuarios_esperando.get(chat_id, False)
    chat_id = str(chat_id)
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()

    cur.execute('SELECT is_waiting FROM usuario WHERE chat_id = %s;', (chat_id, ))

    row = cur.fetchone()
    if row:
        ret = row[0]
    else:
        ret = False

    # Actualizamos la DB
    cur.execute('UPDATE usuario SET is_waiting = false WHERE chat_id = %s;', (chat_id, ))
    conn.commit()
    cur.close()
    conn.close()

    return ret


#####################################
############### Bot #################
#####################################

class ChatSesion(telepot.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(ChatSesion, self).__init__(*args, **kwargs)

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
            if is_waiting(chat_id):
                try:
                    # Parseamos usuario y contraseña
                    usuario, password = msg['text'].split()

                    # Chequear que el carnet cumple el formato correcto
                    pattern = re.compile('^([0-9]{2}-[0-9]{5})$')
                    assert(pattern.match(usuario))

                    # Guardamos en la base de datos
                    guardado = save_user(usuario, password, str(chat_id))
                    if guardado == 1:
                        bot.sendMessage(chat_id, 'Se registró exitosamente tu cuenta.')
                    elif guardado == 2:
                        bot.sendMessage(chat_id, 'Se actualizó correctamente tu cuenta.')
                    else:
                        pass

                except ValueError as e:
                    bot.sendMessage(chat_id, 'Ocurrió un error leyendo el mensaje: <code>{}</code>\nVuelve a intentarlo con el comando /login'.format(e), parse_mode='HTML')

                except psycopg2.DataError as e:
                    bot.sendMessage(chat_id, 'Ocurrió un error modificando la base de datos: <code>{}</code>'.format(e), parse_mode='HTML')
                
                except psycopg2.IntegrityError as e:
                    bot.sendMessage(chat_id, 'Ocurrió un error guardando los datos: <code>{}</code>'.format(e), parse_mode='HTML')

                except AssertionError:
                    bot.sendMessage(chat_id, 'El carnet debe tener formato XX-XXXXX. Intenta de nuevo con /login.')

            elif is_login(msg['text'], chat_id):
                bot.sendMessage(chat_id, 'Por favor envíame tu nombre de usuario (e.g carnet) y tu contraseña separadas por un espacio.')

            elif is_help(msg['text']):
                bot.sendMessage(chat_id, HELP)

            elif is_categoria(msg['text']):
                # Obtenemos las categorías
                r = requests.get(COMPUSHOW_URL + 'categories/')
                response = r.json()

                inline_keyboard = [[]]
                count = 0
                idx = 0
                for categoria in response:
                    if count > 1:
                        count = 0
                        idx += 1
                        inline_keyboard.append([])
                    msg = categoria['fields']['name'] + EMOJIS[categoria['fields']['name']]
                    inline_keyboard[idx].append(InlineKeyboardButton(text=msg, callback_data=categoria['pk']))
                    count += 1

                keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
                bot.sendMessage(chat_id, 'Categorías:', reply_markup=keyboard)
                # for categoria in response:
                #     bot.sendMessage(chat_id, categoria['fields']['name'])

            else:
                bot.sendMessage(chat_id, 'Si necesitas ayuda en como comunicarte conmigo, usa el comando /help mientras escuchas esta brutal playlist: {}'.format(PLAYLIST_URL))

    def on_callback_query(self, msg):
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
        ## Si se recibió un voto
        if query_data.split()[0] == "/voto":
            # Obtenemos el carnet del usuario
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            cur = conn.cursor()

            # Chequeamos si ya el usuario existe
            cur.execute('SELECT carnet FROM usuario WHERE chat_id = %s;', (str(from_id), ))
            row = cur.fetchone()
            if not row or not row[0]:
                bot.sendMessage(from_id, 'Parece que no has iniciado sesión. Utiliza el comando /login.')
                conn.commit()
                cur.close()
                conn.close()
                return

            student_id = row[0]
            data = { 
                'nominee': query_data.split()[1], 
                'categoria': query_data.split()[2], 
                'student_id': student_id, 
                'token': TOKEN
            }
            r = requests.post(COMPUSHOW_URL + 'voting_from_bot/', data=data)

            response = r.json()
            if response.get('success', False):
                bot.sendMessage(from_id, 'Voto registrado')
                bot.answerCallbackQuery(query_id, 'Voto registrado')
            elif not response.get('error', False):
                bot.sendMessage(from_id, 'Ya votaste por esta categoría')
                bot.answerCallbackQuery(query_id, 'Ocurrió un error registrando el voto')
            else:
                bot.sendMessage(from_id, 'Ocurrió un error registrando el voto: {}'.format(response.get('error')))
                bot.answerCallbackQuery(query_id, 'Ocurrió un error registrando el voto')

            conn.commit()
            cur.close()
            conn.close()
            return

        r = requests.get(COMPUSHOW_URL + 'category/', params={'pk': query_data})
        response = r.json()
        categoria = response['categoria']
        nominados = response['nominados']

        bot.answerCallbackQuery(query_id, text=categoria[0]['fields']['name'])

        nominados_btns = []
        for nominado in nominados:
            # Nominado
            nominado_set = ""
            if nominado['person']:
                nominado_set += "{} {}".format(escape(nominado['person'][0]['fields']['name']), escape(nominado['person'][0]['fields']['surname']))

            # Si hay persona extra:
            if nominado['personOpt']:
                nominado_set += ", {} {}".format(escape(nominado['personOpt'][0]['fields']['name']), escape(nominado['personOpt'][0]['fields']['surname']))

            if nominado['nominee'] and nominado['nominee'][0]['fields']['extra']:
                nominado_set += "\n{}".format(escape(nominado['nominee'][0]['fields']['extra']))

            nominados_btns.append([InlineKeyboardButton(text=nominado_set, callback_data="/voto {} {}".format(nominado['nominee'][0]['pk'], categoria[0]['fields']['name']))])


        keyboard = InlineKeyboardMarkup(inline_keyboard=nominados_btns)
        bot.sendMessage(from_id, '<b>{}</b>\n{}\nNominados:'.format(categoria[0]['fields']['name'], categoria[0]['fields']['description']), reply_markup=keyboard, parse_mode='HTML')

        # inline_keyboard = []
        # for categoria in response:
        #     inline_keyboard.append([InlineKeyboardButton(text=categoria['fields']['name'], callback_data=categoria['pk'])])

        # keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
        # bot.sendMessage(chat_id, 'Categorías:', reply_markup=keyboard)


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