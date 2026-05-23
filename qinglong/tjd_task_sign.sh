#!/usr/bin/env bash
# cron:0 9 * * *
# new Env("塔吉多自动签到")

set -e
set -u

QL_DIR=${QL_DIR:-"/ql"}
dir_repo=${dir_repo:-"$QL_DIR/data/repo"}

[ ! -d "$dir_repo" ] && [ -d "$QL_DIR/repo" ] && dir_repo="$QL_DIR/repo"

dir_shell=$QL_DIR/shell
touch $dir_shell/env.sh 2>/dev/null && . $dir_shell/env.sh
touch /root/.bashrc 2>/dev/null && . /root/.bashrc

tjd_repo_dir="$(find $dir_repo -type d -iname "*NTE-SignAutomata*" | head -1)"

if [ -z "$tjd_repo_dir" ]; then
    echo "未找到仓库目录"
    exit 1
fi

cd "$tjd_repo_dir"

if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    echo "Python未安装，正在安装..."
    if command -v apt-get &>/dev/null; then
        apt-get update && apt-get install -y python3 python3-pip
    elif command -v apk &>/dev/null; then
        apk update && apk add python3 py3-pip
    fi
fi

if [ -f "requirements.txt" ]; then
    if command -v pip3 &>/dev/null; then
        pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple -q
    elif command -v pip &>/dev/null; then
        pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple -q
    fi
fi

python_cmd="python3"
command -v python3 &>/dev/null || python_cmd="python"

$python_cmd tjd_sign.py
