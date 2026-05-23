#!/usr/bin/env python3
"""
塔吉多 Token 获取工具
在本地运行，输入手机号和验证码后输出 Token，手动填入青龙面板环境变量
"""
import base64
import hashlib
import json
import time
import uuid
from urllib import parse

try:
    import requests
except ImportError:
    print("请先安装 requests: pip install requests")
    exit(1)

try:
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
except ImportError:
    print("请先安装 cryptography: pip install cryptography")
    exit(1)

SECRET = '89155cc4e8634ec5b1b6364013b23e3e'
DEVICETYPE = 'LGE-AN10'
TYPE = '16'
DEVICENAME = 'LGE-AN10'
VERSIONCODE = '1'
AREACODEID = '1'
DEVICESYS = '12'
DEVICEMODEL = 'LGE-AN10'
SDKVERSION = '4.129.0'
BID = 'com.pwrd.htassistant'
CHANNELID = '1'
APP_ID = '10550'
USER_CENTER_APP_ID = '10551'
APPVERSION = '1.1.0'
OKHTTP_UA = 'okhttp/4.12.0'
DEFAULT_GAME_ID = '1289'

REQUEST_HEADERS_BASE = {
    'platform': 'android',
    'Content-Type': 'application/x-www-form-urlencoded',
}

SEND_CAPTCHA_URL = 'https://user.laohu.com/m/newApi/sendPhoneCaptchaWithOutLogin'
CHECK_CAPTCHA_URL = 'https://user.laohu.com/m/newApi/checkPhoneCaptchaWithOutLogin'
LOGIN_URL = 'https://user.laohu.com/openApi/sms/new/login'
USER_CENTER_LOGIN_URL = 'https://bbs-api.tajiduo.com/usercenter/api/login'
GET_GAME_ROLES_URL = 'https://bbs-api.tajiduo.com/usercenter/api/v2/getGameRoles'


def generate_signature(params):
    sorted_keys = sorted(params.keys())
    values = ''.join(str(params[key]) for key in sorted_keys)
    return hashlib.md5((values + SECRET).encode('utf-8')).hexdigest()


def aes_base64_encode(text):
    key = SECRET[-16:].encode('utf-8')
    padder = padding.PKCS7(128).padder()
    padded = padder.update(text.encode('utf-8')) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.ECB())
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(encrypted).decode('utf-8')


def random_device_id():
    return uuid.uuid4().hex


def request_form(url, data, headers):
    return requests.post(url, data=parse.urlencode(data), headers=headers, timeout=30)


def safe_json(response, endpoint):
    try:
        return response.json()
    except:
        raise Exception(f'{endpoint} 返回非JSON: {response.text[:200]}')


def is_ok(resp):
    return resp.get('code') == 0


def send_captcha(phone, device_id):
    print(f'\n正在发送验证码到 {phone}...')
    data = {
        'deviceType': DEVICETYPE,
        'type': TYPE,
        'deviceId': device_id,
        'deviceName': DEVICENAME,
        'versionCode': VERSIONCODE,
        't': str(int(time.time())),
        'areaCodeId': AREACODEID,
        'appId': APP_ID,
        'deviceSys': DEVICESYS,
        'cellphone': phone,
        'deviceModel': DEVICEMODEL,
        'sdkVersion': SDKVERSION,
        'bid': BID,
        'channelId': CHANNELID,
    }
    data['sign'] = generate_signature(data)
    resp = safe_json(request_form(SEND_CAPTCHA_URL, data, REQUEST_HEADERS_BASE), '发送验证码')
    if not is_ok(resp):
        raise Exception(f'发送失败：{resp.get("message") or resp.get("msg")}')
    print('验证码已发送，请注意查收')


def check_captcha(phone, code, device_id):
    data = {
        'deviceType': DEVICETYPE,
        'deviceId': device_id,
        'deviceName': DEVICENAME,
        'versionCode': VERSIONCODE,
        't': str(int(time.time())),
        'captcha': code,
        'appId': APP_ID,
        'deviceSys': DEVICESYS,
        'cellphone': phone,
        'deviceModel': DEVICEMODEL,
        'sdkVersion': SDKVERSION,
        'bid': BID,
        'channelId': CHANNELID,
    }
    data['sign'] = generate_signature(data)
    resp = safe_json(request_form(CHECK_CAPTCHA_URL, data, REQUEST_HEADERS_BASE), '验证验证码')
    if not is_ok(resp):
        raise Exception(f'验证码错误')


def login(phone, code, device_id):
    data = {
        'deviceType': DEVICETYPE,
        'idfa': '',
        'sign': '',
        'adm': '',
        'type': TYPE,
        'deviceId': device_id,
        'version': VERSIONCODE,
        'deviceName': DEVICENAME,
        'mac': '',
        't': str(int(time.time() * 1000)),
        'areaCodeId': AREACODEID,
        'captcha': aes_base64_encode(code),
        'appId': APP_ID,
        'deviceSys': DEVICESYS,
        'cellphone': aes_base64_encode(phone),
        'deviceModel': DEVICEMODEL,
        'sdkVersion': SDKVERSION,
        'bid': BID,
        'channelId': CHANNELID,
    }
    data['sign'] = generate_signature(data)
    resp = safe_json(request_form(LOGIN_URL, data, REQUEST_HEADERS_BASE), '登录')
    if not is_ok(resp):
        raise Exception(f'登录失败：{resp.get("message") or resp.get("msg")}')
    result = resp.get('result') or {}
    return result.get('token'), str(result.get('userId'))


def user_center_login(token, user_id, device_id):
    headers = {
        **REQUEST_HEADERS_BASE,
        'deviceid': device_id,
        'authorization': '',
        'appversion': APPVERSION,
        'uid': '10000000',
        'User-Agent': OKHTTP_UA,
    }
    payload = {
        'token': token,
        'userIdentity': user_id,
        'appId': USER_CENTER_APP_ID,
    }
    resp = safe_json(request_form(USER_CENTER_LOGIN_URL, payload, headers), '用户中心登录')
    if not is_ok(resp):
        raise Exception(f'用户中心登录失败：{resp.get("msg")}')
    return resp.get('data') or {}


def get_game_role_ids(access_token, uid, device_id, game_id):
    headers = {
        'platform': 'android',
        'authorization': access_token,
        'uid': uid,
        'deviceid': device_id,
        'appversion': APPVERSION,
        'User-Agent': OKHTTP_UA,
    }
    response = requests.get(GET_GAME_ROLES_URL, headers=headers, params={'gameId': game_id}, timeout=30)
    resp = safe_json(response, '获取角色列表')
    if not is_ok(resp):
        return []
    data = resp.get('data') or {}
    roles = data.get('roles', []) if isinstance(data, dict) else []
    return [str(r.get('roleId', '')).strip() for r in roles if r.get('roleId')]


def main():
    print('=' * 60)
    print('塔吉多 Token 获取工具')
    print('=' * 60)
    print('\n此工具用于获取塔吉多账号的 Token，获取后请手动填入青龙面板环境变量')
    print()

    phone = input('请输入手机号：').strip()
    if not phone:
        print('手机号不能为空')
        return

    device_id = random_device_id()
    
    try:
        send_captcha(phone, device_id)
    except Exception as e:
        print(f'错误：{e}')
        return

    code = input('请输入验证码：').strip()
    if not code:
        print('验证码不能为空')
        return

    try:
        print('\n正在登录...')
        check_captcha(phone, code, device_id)
        token, user_id = login(phone, code, device_id)
        user_center = user_center_login(token, user_id, device_id)
        
        refresh_token = user_center.get('refreshToken')
        uid = str(user_center.get('uid', ''))
        access_token = user_center.get('accessToken')
        
        if not refresh_token:
            print('登录失败：未获取到 refreshToken')
            return

        print('登录成功！\n')
        
        role_ids = []
        if access_token and uid:
            try:
                role_ids = get_game_role_ids(access_token, uid, device_id, DEFAULT_GAME_ID)
            except:
                pass

        account = {
            'refreshToken': refresh_token,
            'uid': uid,
            'deviceId': device_id,
            'gameId': DEFAULT_GAME_ID,
            'roleIds': role_ids
        }
        
        token_json = json.dumps(account, ensure_ascii=False, separators=(',', ': '))
        
        print('=' * 60)
        print('获取成功！请复制以下内容到青龙面板 TOKEN.txt 文件')
        print('=' * 60)
        print()
        print('文件位置: 脚本管理 → YU-1021_NTE-SignAutomata → qinglong → TOKEN.txt')
        print()
        print('内容：')
        print(token_json)
        print()
        print('=' * 60)
        print('\n操作步骤：')
        print('1. 登录青龙面板')
        print('2. 点击左侧「脚本管理」')
        print('3. 进入 YU-1021_NTE-SignAutomata/qinglong 目录')
        print('4. 找到 TOKEN.txt 文件，点击编辑')
        print('5. 粘贴上面的 JSON 内容')
        print('6. 点击保存')
        print('=' * 60)
        
    except Exception as e:
        print(f'错误：{e}')


if __name__ == '__main__':
    main()
