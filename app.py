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
        bot.sendMessage(chat_id, 'hola mundo')

    def on_callback_query(self, msg):
        pass


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