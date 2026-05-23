#!/usr/bin/env python3
"""
塔吉多（异环）自动签到脚本
支持青龙API自动更新Token
"""
import base64
import hashlib
import json
import os
import re
import sys
import time
import uuid
from urllib import parse

try:
    import requests
except ImportError:
    print("错误: 请先安装 requests")
    print("运行: pip install requests")
    sys.exit(1)

try:
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
except ImportError:
    print("错误: 请先安装 cryptography")
    print("运行: pip install cryptography")
    sys.exit(1)

DEFAULT_GAME_ID = '1289'
COMMUNITY_ID = '1'
APP_ID = '10550'
USER_CENTER_APP_ID = '10551'
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
APPVERSION = '1.1.0'
OKHTTP_UA = 'okhttp/4.12.0'

HEADERS = {
    'platform': 'android',
    'Content-Type': 'application/x-www-form-urlencoded',
}

REFRESH_TOKEN_URL = 'https://bbs-api.tajiduo.com/usercenter/api/refreshToken'
GET_GAME_ROLES_URL = 'https://bbs-api.tajiduo.com/usercenter/api/v2/getGameRoles'
APP_SIGNIN_URL = 'https://bbs-api.tajiduo.com/apihub/api/signin'
GAME_SIGNIN_URL = 'https://bbs-api.tajiduo.com/apihub/awapi/sign'
GAME_SIGNIN_STATE_URL = 'https://bbs-api.tajiduo.com/apihub/awapi/signin/state'
GAME_SIGN_REWARDS_URL = 'https://bbs-api.tajiduo.com/apihub/awapi/sign/rewards'


class QingLongAPI:
    def __init__(self):
        self.url = ''
        self.client_id = ''
        self.client_secret = ''
        self.access_token = ''
        self.enabled = False
        self._parse_config()
    
    def _parse_config(self):
        config = os.environ.get('TJD_API', '').strip()
        if not config:
            return
        
        try:
            for item in config.split(';'):
                item = item.strip()
                if '=' in item:
                    key, value = item.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key == 'QL_URL':
                        self.url = value.rstrip('/')
                    elif key == 'CLIENT_ID':
                        self.client_id = value
                    elif key == 'CLIENT_SECRET':
                        self.client_secret = value
            
            if self.url and self.client_id and self.client_secret:
                self.enabled = True
        except:
            pass
    
    def _get_token(self):
        if not self.enabled:
            return ''
        try:
            resp = requests.get(
                f"{self.url}/open/auth/token",
                params={'client_id': self.client_id, 'client_secret': self.client_secret},
                timeout=10
            )
            data = resp.json()
            if data.get('code') == 200:
                self.access_token = data.get('data', {}).get('token', '')
                return self.access_token
        except:
            pass
        return ''
    
    def _auth_header(self):
        if not self.access_token:
            self._get_token()
        return {'Authorization': f'Bearer {self.access_token}'}
    
    def get_env(self, name):
        if not self.enabled:
            return None
        try:
            if not self.access_token:
                self._get_token()
            resp = requests.get(
                f"{self.url}/open/envs",
                params={'searchValue': name},
                headers=self._auth_header(),
                timeout=10
            )
            data = resp.json()
            if data.get('code') == 200:
                envs = data.get('data', [])
                for env in envs:
                    if env.get('name') == name:
                        return {
                            'id': env.get('id'),
                            'value': env.get('value', ''),
                            'remarks': env.get('remarks', '')
                        }
        except:
            pass
        return None
    
    def update_env(self, name, value, env_id=None, remarks=''):
        if not self.enabled:
            return False
        try:
            if not self.access_token:
                self._get_token()
            
            if env_id:
                resp = requests.put(
                    f"{self.url}/open/envs",
                    json={
                        'id': env_id,
                        'name': name,
                        'value': value,
                        'remarks': remarks
                    },
                    headers=self._auth_header(),
                    timeout=10
                )
            else:
                resp = requests.post(
                    f"{self.url}/open/envs",
                    json=[{
                        'name': name,
                        'value': value,
                        'remarks': remarks
                    }],
                    headers=self._auth_header(),
                    timeout=10
                )
            return resp.json().get('code') == 200
        except:
            pass
        return False


ql_api = QingLongAPI()


def sign(params):
    sorted_keys = sorted(params.keys())
    values = ''.join(str(params[key]) for key in sorted_keys)
    return hashlib.md5((values + SECRET).encode('utf-8')).hexdigest()


def aes_encode(text):
    key = SECRET[-16:].encode('utf-8')
    padder = padding.PKCS7(128).padder()
    padded = padder.update(text.encode('utf-8')) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.ECB())
    return base64.b64encode(cipher.encryptor().update(padded)).decode('utf-8')


def post(url, data, headers=None):
    return requests.post(url, data=parse.urlencode(data), headers=headers or HEADERS, timeout=30)


def get(url, params=None, headers=None):
    return requests.get(url, params=params, headers=headers, timeout=30)


def json_resp(resp, name):
    try:
        return resp.json()
    except:
        raise Exception(f'{name} 返回异常')


def is_ok(data):
    return data.get('code') == 0


def is_signed(msg):
    return any(k in msg for k in ['已签到', '签到过', '重复签到'])


def refresh_token(account):
    headers = {
        **HEADERS,
        'deviceid': account['deviceId'],
        'authorization': account['refreshToken'],
        'appversion': APPVERSION,
        'uid': '10000000',
        'User-Agent': OKHTTP_UA,
    }
    resp = requests.post(REFRESH_TOKEN_URL, headers=headers, timeout=30)
    if resp.status_code == 402:
        raise Exception('Token已失效，请重新获取')
    data = json_resp(resp, '刷新Token')
    if not is_ok(data):
        raise Exception(f'刷新Token失败: {data.get("msg")}')
    result = data.get('data') or {}
    token = result.get('accessToken')
    refresh = result.get('refreshToken')
    if not token or not refresh:
        raise Exception('刷新Token返回数据异常')
    
    if refresh != account['refreshToken']:
        account['refreshToken'] = refresh
        account['_token_updated'] = True
    
    if result.get('uid'):
        account['uid'] = str(result['uid'])
    return token


def get_roles(token, uid, device_id, game_id):
    headers = {
        'platform': 'android',
        'authorization': token,
        'uid': uid,
        'deviceid': device_id,
        'appversion': APPVERSION,
        'User-Agent': OKHTTP_UA,
    }
    resp = get(GET_GAME_ROLES_URL, {'gameId': game_id}, headers)
    data = json_resp(resp, '获取角色')
    if not is_ok(data):
        return []
    roles = (data.get('data') or {}).get('roles', [])
    return [str(r.get('roleId', '')).strip() for r in roles if r.get('roleId')]


def app_sign(token, uid, device_id):
    headers = {
        **HEADERS,
        'authorization': token,
        'uid': uid,
        'deviceid': device_id,
        'appversion': APPVERSION,
        'User-Agent': OKHTTP_UA,
    }
    resp = post(APP_SIGNIN_URL, {'communityId': COMMUNITY_ID}, headers)
    data = json_resp(resp, '社区签到')
    if is_ok(data):
        result = data.get('data') or {}
        return True, f"社区签到成功，获得{result.get('exp', 0)}经验，{result.get('goldCoin', 0)}金币"
    msg = data.get('msg') or data.get('message') or ''
    if is_signed(msg):
        return True, '社区今日已签到'
    return False, msg


def get_sign_state(token, game_id):
    resp = get(GAME_SIGNIN_STATE_URL, {'gameId': game_id}, {'Authorization': token})
    data = json_resp(resp, '签到状态')
    if is_ok(data):
        return data.get('data') or {}
    return {}


def get_rewards(token, role_id, game_id):
    params = {'gameId': game_id}
    if role_id:
        params['roleId'] = role_id
    resp = get(GAME_SIGN_REWARDS_URL, params, {'Authorization': token})
    data = json_resp(resp, '签到奖励')
    if is_ok(data):
        result = data.get('data')
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            for key in ['items', 'rewards', 'list']:
                if isinstance(result.get(key), list):
                    return result[key]
    return []


def game_sign(token, role_id, game_id):
    headers = {
        **HEADERS,
        'authorization': token,
        'appversion': APPVERSION,
        'User-Agent': OKHTTP_UA,
    }
    
    def reward_text(gid):
        try:
            state = get_sign_state(token, gid)
            days = int(state.get('days') or 0)
            if days <= 0:
                return ''
            rewards = get_rewards(token, role_id, gid)
            if len(rewards) >= days:
                item = rewards[days - 1]
                name = item.get('name') or item.get('itemName') or ''
                num = item.get('num') or item.get('count') or ''
                return f"，今日道具: {name}{'x'+str(num) if num else ''}"
        except:
            pass
        return ''
    
    for gid in [game_id, DEFAULT_GAME_ID, '1257']:
        resp = post(GAME_SIGNIN_URL, {'roleId': role_id, 'gameId': gid}, headers)
        data = json_resp(resp, '游戏签到')
        if is_ok(data):
            return True, f'签到成功(gameId={gid}){reward_text(gid)}'
        msg = data.get('msg') or data.get('message') or ''
        if is_signed(msg):
            state = get_sign_state(token, gid)
            if state.get('todaySign'):
                return True, f'今日已签到(gameId={gid}){reward_text(gid)}'
            continue
    return False, '游戏签到失败'


def parse_account(text):
    text = text.strip()
    if not text:
        return None
    try:
        raw = json.loads(text)
    except:
        return {
            'refreshToken': text,
            'uid': '',
            'deviceId': uuid.uuid4().hex,
            'gameId': DEFAULT_GAME_ID,
            'roleIds': [],
        }
    return {
        'refreshToken': raw.get('refreshToken') or raw.get('token') or '',
        'uid': str(raw.get('uid') or ''),
        'deviceId': raw.get('deviceId') or raw.get('deviceid') or uuid.uuid4().hex,
        'gameId': raw.get('gameId') or raw.get('game_id') or DEFAULT_GAME_ID,
        'roleIds': raw.get('roleIds') or raw.get('role_ids') or raw.get('roleId') or [],
    }


def account_to_json(account):
    return json.dumps({
        'refreshToken': account['refreshToken'],
        'uid': account.get('uid', ''),
        'deviceId': account.get('deviceId', ''),
        'gameId': account.get('gameId', DEFAULT_GAME_ID),
        'roleIds': account.get('roleIds', [])
    }, ensure_ascii=False, separators=(',', ': '))


def load_accounts():
    token = os.environ.get('TJD_TOKEN', '').strip()
    if not token:
        return [], None
    
    lines = [l.strip() for l in token.replace('\r\n', '\n').split('\n') if l.strip()]
    if len(lines) == 1 and ',' in lines[0] and not lines[0].startswith('{'):
        lines = [l.strip() for l in lines[0].split(',') if l.strip()]
    
    accounts = [a for a in [parse_account(l) for l in lines] if a and a['refreshToken']]
    
    env_info = ql_api.get_env('TJD_TOKEN')
    return accounts, env_info


def save_accounts(accounts, env_info):
    if not ql_api.enabled:
        return
    
    token_value = '\n'.join(account_to_json(acc) for acc in accounts)
    
    if env_info:
        ql_api.update_env('TJD_TOKEN', token_value, env_info.get('id'), env_info.get('remarks', ''))
        print('Token已自动更新到青龙环境变量')
    else:
        ql_api.update_env('TJD_TOKEN', token_value, remarks='塔吉多签到Token')
        print('Token已自动保存到青龙环境变量')


def do_sign(account):
    account['gameId'] = account.get('gameId') or DEFAULT_GAME_ID
    account['deviceId'] = account.get('deviceId') or uuid.uuid4().hex
    
    token = refresh_token(account)
    success = True
    uid = account.get('uid', '')
    
    if uid:
        ok, msg = app_sign(token, uid, account['deviceId'])
        print(f'账号{uid}: {msg}')
        if not ok:
            success = False
    else:
        print('无uid，跳过社区签到')
    
    role_ids = list(account.get('roleIds', []))
    env_roles = os.environ.get('TGD_ROLE_IDS', '')
    if env_roles:
        role_ids.extend([r.strip() for r in env_roles.replace('\n', ',').split(',') if r.strip()])
    if not role_ids and uid:
        role_ids = get_roles(token, uid, account['deviceId'], account['gameId'])
    
    if not role_ids:
        print('未找到角色ID')
        return False
    
    for role_id in role_ids:
        ok, msg = game_sign(token, role_id, account['gameId'])
        print(f'角色{role_id}: {msg}')
        if not ok:
            success = False
    
    return success


def notify(title, content):
    try:
        from notify import send
        send(title, content)
    except:
        pass


def main():
    print('塔吉多自动签到')
    print('=' * 50)
    
    if ql_api.enabled:
        print(f'青龙API已启用: {ql_api.url}')
    print()
    
    accounts, env_info = load_accounts()
    if not accounts:
        print('未配置账号，请设置环境变量 TJD_TOKEN')
        print('获取Token方法: 在本地运行 get_token.py')
        return False
    
    print(f'读取到 {len(accounts)} 个账号\n')
    
    results = []
    success = True
    need_save = False
    
    for i, account in enumerate(accounts, 1):
        print(f'--- 账号 {i} ---')
        try:
            ok = do_sign(account)
            results.append(f'账号{i}: {"成功" if ok else "失败"}')
            if not ok:
                success = False
            if account.get('_token_updated'):
                need_save = True
        except Exception as e:
            print(f'签到失败: {e}')
            results.append(f'账号{i}: 失败 - {e}')
            success = False
        print()
    
    if need_save and ql_api.enabled:
        save_accounts(accounts, env_info)
    
    print('=' * 50)
    print('签到结果:')
    for r in results:
        print(f'  {r}')
    
    notify('塔吉多签到', '\n'.join(results))
    return success


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
