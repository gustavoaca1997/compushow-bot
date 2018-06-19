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

# TOKEN = os.environ.get('TOKEN')
TOKEN = "464114645:AAHp2GvwFhbxpLrsokB2upvW5yVcUDcyGbk"
# URL = os.environ.get('URL')
URL = "https://compushow-bot.herokuapp.com/"
SECRET = '/bot' + TOKEN
UPDATE_QUEUE = Queue()

HELP = 'Bot creado para el registro de pagos de los clientes del <i>Cuartico de la Sala de Computación de la USB.</i>\n'+\
'\n\n<b>Comandos básicos:</b>\n'+\
'<code>/start XXXXXXXX</code>\nPara registrarte como usuario del bot con cédula <code>XXXXXXXX</code>\n'+\
'\n\n<code>/start XXXXXXXX username clave</code>\nPara registrarte como usuario administrador del bot '+\
'(e.g, si eres JD del CEIC o Colaborador), con cédula <code>XXXXXXXX</code>, con nombre de usuario del sistema de ventas <code>username</code>'+\
' (<code>clave</code> es la clave secreta acordada con la <i>Coordinación de Información y Tecnología</i>).\n'+\
'\n\n<code>/comprobantes</code>\n(Sólo administrador). Para mostrar los comprobantes pendientes por registrar.\n'+\
'\n\n<b>Cómo mandar un comprobante de pago:</b>\n'+\
'Luego de registrarte como usuario, sólo debes <b>mandar una captura del comprobante al bot</b> y listo.'
# Token para el cuartico
TOKEN_CUARTICO = "chillbro2018"
PORT = os.environ.get('PORT')
SECRET = '/bot' + TOKEN
UPDATE_QUEUE = Queue()


class ChatSesion(telepot.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(ChatSesion, self).__init__(*args, **kwargs)

    # Manejador de mensajes
    def on_chat_message(self, msg):
        pprint(msg)
        content_type, chat_type, chat_id = telepot.glance(msg)
        username = msg['chat']['username'] if 'username' in msg['chat'] else ''
        nombre = msg['chat']['first_name'] if 'first_name' in msg['chat'] else ''

        # Si no es un chat privado con un usuario
        if chat_type != 'private':
            return

        # Si es un comprobante
        if content_type in ['photo']:
            api_endpoint = API + 'pagos/'
            data = {
                'chat_id': chat_id,
                'captura_comprobante': msg['photo'][0]['file_id']
            }
            response = requests.post(url=api_endpoint, data=data)
            data = response.json()
            if data['creado']:
                bot.sendMessage(chat_id, 'Comprobante recibido.')
            else:
                bot.sendMessage(chat_id, 'Error guardando comprobante. Para más información utiliza el comando /help.')

        # Listar comprobantes
        elif content_type in ['text'] and is_comprobantes(msg['text']):
            # si es administrador
            if is_jd(username):
                api_endpoint = API + 'pagos/'
                r = requests.get(url=api_endpoint)
                pagos = r.json()
                #pprint(pagos)
                for p in pagos:
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text='Registrar', callback_data=p['id'])]
                        ])

                    # Obtener cliente
                    params = {'ci': p['cliente']}
                    r_cliente = requests.get(url=API+'clientes/cliente/', params=params)
                    data_cliente = r_cliente.json()
                    cliente = data_cliente[0]

                    bot.sendPhoto(chat_id, p['captura_comprobante'], 
                        reply_markup=keyboard, 
                        caption='Comprobante #{}.\n\n@{}\n{}.'.format(p['id'], 
                            cliente['usuario_telegram'],
                            cliente['ci']))

                if not len(pagos):
                    bot.sendMessage(chat_id, 'No hay comprobantes por registrar.')

            else:
                bot.sendMessage(chat_id, 'Debes ser admin para usar este comando.')

        # START, registrar usuario
        elif content_type in ['text'] and is_start(msg['text']):

            if len(msg['text'].split(' ')) == 1:
                bot.sendMessage(chat_id, HELP, parse_mode='HTML')

            else:
                comando, ci, usuario_cuartico, token_cuartico = get_cuartico_data(msg['text'])
                data = {}
                # Si tiene permisos para ver los comprobantes
                if token_cuartico == TOKEN_CUARTICO:
                    data['usuario_cuartico'] = usuario_cuartico
                    data['jd'] = True

                data['chat_id'] = chat_id
                data['ci'] = ci
                data['usuario_telegram'] = username

                api_endpoint = API + 'clientes/'
                r = requests.post(url = api_endpoint, data = data)
                data_response = r.json()

                if data_response['creado']:
                    bot.sendMessage(chat_id, 'Bienvenido {}'.format(nombre))
                else:
                    bot.sendMessage(chat_id, 'Tus datos han sido actualizados {}'.format(nombre))

        elif content_type is 'text' and is_help(msg['text']):
            bot.sendMessage(chat_id,
                HELP,
                parse_mode='HTML'
            )

        elif content_type is 'text' and is_deuda(msg['text']):
            params = {'usuario_telegram': username}


    def on_callback_query(self, msg):
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
        username = msg['from']['username']
        # si es administrador
        if is_jd(username):
            # Se borra comprobante
            api_endpoint = API + 'pagos/'
            data = {
                'registrar': True,
                'pago_pk': query_data
            }
            r = requests.post(url=api_endpoint, data=data)
            data = r.json()
            if data[0]['borrados']:
                bot.answerCallbackQuery(query_id, text='Registrado')
                bot.sendMessage(from_id, 'Comprobante {} registrado.'.format(int(query_data)))
            else:
                bot.answerCallbackQuery(query_id, text='Error registrando.')
                bot.sendMessage(from_id, 'Error registrando comprobante {}.'.format(int(query_data)+1))

        else:
            bot.sendMessage(from_id, 'Debes ser de la junta directiva para usar este comando.')

# Funcion que chequea si el comando es /deuda
def is_deuda(comando):
    # si no es comando
    if not is_command(comando):
        return False

    # si tiene mas de un token el mensaje
    if len(comando.split(' ')) != 2:
        return False

    if comando[1:] == 'deuda':
        return True

    return False    

# Funcion que chequea si el usuario es JD
def is_jd(username):
    api_endpoint = API + 'clientes/cliente/telegram'
    r = requests.get(url = api_endpoint, params={'usuario_telegram': username})
    data = r.json()
    try:
        return data[0]['jd']
    except IndexError:
        return False

# Funcion que checkea si el texto es un comando
def is_command(text):
    text_list = text.split(' ')

    comando = text_list[0]  # unico token
    if comando[0] != '/':
        return False

    return True

# Funcion que chequea si el comando es /comprobantes
def is_comprobantes(comando):
    # si no es comando
    if not is_command(comando):
        return False

    # si tiene mas de un token el mensaje
    if len(comando.split(' ')) > 1:
        return False

    if comando[1:] == 'comprobantes':
        return True

    return False

# Funcion que checke si el comand es /start
def is_start(entrada):
    if not is_command(entrada):
        return False

    # /start <ci> o /start <ci> <usuario> <token>
    if not len(entrada.split(' ')) in [1, 4]:
        return False

    comando = entrada.split(' ')[0]
    if comando[1:] == 'start':
        return True

    return False

def is_help(entrada):
    if not is_command(entrada):
        return False

    if not len(entrada.split(' ')) == 1:
        return False

    return entrada[1:] == 'help'

# Parser de los argumentos de /start
def get_cuartico_data(entrada):
    entrada_list = entrada.split(' ')
    if not (len(entrada_list) in [2, 4]):
        return False

    ret = []
    for e in entrada_list:
        ret.append(e)

    for i in range(4-len(ret)):
        ret.append(None)

    return ret

app = Flask(__name__)
bot = telepot.DelegatorBot(TOKEN, [
    include_callback_query_chat_id(
        pave_event_space())(
            per_chat_id(), create_open, ChatSesion, timeout=10),
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