"""Telegram interface demo. No campaign content or outbound messaging."""
import json
import os
import threading
import time
import urllib.request
import urllib.error

TOKEN = os.environ.get('BOT_TOKEN', '').strip()
if not TOKEN:
    raise SystemExit('Set the BOT_TOKEN environment variable before starting.')
BASE = f'https://api.telegram.org/bot{TOKEN}/'
COUNTRIES = ('FR', 'IT', 'UK', 'AU', 'DE', 'ES', 'PT', 'BE', 'CZ', 'RO', 'SK', 'GR', 'AT', 'NO', 'DK', 'SE', 'NL')
FLAGS = ('🇫🇷', '🇮🇹', '🇬🇧', '🇦🇺', '🇩🇪', '🇪🇸', '🇵🇹', '🇧🇪', '🇨🇿', '🇷🇴', '🇸🇰', '🇬🇷', '🇦🇹', '🇳🇴', '🇩🇰', '🇸🇪', '🇳🇱')
KEYS = [{'text': f'{flag} {code}', 'callback_data': f'demo:{code}'} for code, flag in zip(COUNTRIES, FLAGS)]
MENU = {'inline_keyboard': [KEYS[i:i+3] for i in range(0, len(KEYS), 3)]}

def api(method, **data):
    req = urllib.request.Request(BASE + method, data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=40) as response:
        result = json.load(response)
    if not result.get('ok'):
        raise RuntimeError('Telegram API request failed')
    return result['result']

def delete_demo(chat_id, message_id):
    try:
        api('deleteMessage', chat_id=chat_id, message_id=message_id)
    except Exception:
        pass

def handle(update):
    message = update.get('message', {})
    if message.get('chat', {}).get('type') == 'private' and message.get('text', '').split(' ', 1)[0] == '/start':
        api('sendMessage', chat_id=message['chat']['id'], text='BunnixText — тест интерфейса. Выберите страну:', reply_markup=MENU)
    query = update.get('callback_query')
    if not query:
        return
    api('answerCallbackQuery', callback_query_id=query['id'])
    chat = query.get('message', {}).get('chat', {})
    code = query.get('data', '').removeprefix('demo:')
    if chat.get('type') != 'private' or code not in COUNTRIES:
        return
    sent = api('sendMessage', chat_id=chat['id'], text=f'Тест интерфейса: {code}. Это демонстрационное сообщение.')
    timer = threading.Timer(120, delete_demo, args=(chat['id'], sent['message_id']))
    timer.daemon = True
    timer.start()

def main():
    print('Demo started.', flush=True)
    offset = None
    while True:
        try:
            args = {'timeout': 25, 'allowed_updates': ['message', 'callback_query']}
            if offset is not None:
                args['offset'] = offset
            for update in api('getUpdates', **args):
                offset = update['update_id'] + 1
                try:
                    handle(update)
                except Exception as exc:
                    print('Update failed:', type(exc).__name__, flush=True)
        except urllib.error.HTTPError as exc:
            print('Telegram HTTP status:', exc.code, flush=True)
            if exc.code in (401, 404):
                raise SystemExit('Invalid bot token.') from None
            time.sleep(5)
        except Exception as exc:
            print('Polling retry:', type(exc).__name__, flush=True)
            time.sleep(5)

if __name__ == '__main__':
    main()
