#!/usr/bin/env python3
"""把词表 JSON 注入模板，生成单文件 HTML（中考英语词汇复习）。

用法:
    python generate.py <data.json> <out.html>

data.json 结构:
{
  "title": "中考英语复习词汇",
  "days": [ {"day": "Day 1", "words": [
      {"en":"able","ipa":"/ˈeɪbəl/","pos":"adj","cn":"能够；有才能的",
       "forms":[{"w":"ability","label":"n.能力"}],
       "phrases":[{"en":"be able to do sth","cn":"能够做某事"}],
       "ex":[{"s":"He is ____ to swim.","root":"able","ans":"able","note":"be able to 固定结构"}]} ]} ]
}
"""
import json
import os
import re
import subprocess
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
TEMPLATE = os.path.join(SKILL_DIR, 'assets', 'coach-template.html')
ASSETS = os.path.join(SKILL_DIR, 'assets')
PLACEHOLDER = '/*WORD_DATA_PLACEHOLDER*/'


def validate_js(html):
    s = html.find('<script>')
    if s == -1:
        return True, 'no <script>'
    s += len('<script>')
    e = html.find('</script>', s)
    js = html[s:e]
    tmp = os.path.join(tempfile.gettempdir(), 'zk_coach_check.js')
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(js)
    try:
        r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
    except FileNotFoundError:
        return True, 'node not found, skipped'
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
    if r.returncode == 0:
        return True, 'OK'
    return False, r.stderr[:800]


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    data_path, out_path = sys.argv[1], sys.argv[2]
    data = json.load(open(data_path, encoding='utf-8'))
    # 《词汇答案册》配套真题库：有就注入 DATA.exercises，真题大作战直接用它（标准答案 + 解析）
    ex_path = os.path.join(ASSETS, 'exercises-答案册.json')
    if os.path.exists(ex_path) and not data.get('exercises'):
        data['exercises'] = json.load(open(ex_path, encoding='utf-8'))
    words = sum(len(d['words']) for d in data['days'])
    with open(TEMPLATE, encoding='utf-8') as f:
        tpl = f.read()
    if PLACEHOLDER not in tpl:
        print('ERROR: 模板里找不到数据占位符', file=sys.stderr)
        sys.exit(1)
    payload = 'const DATA = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';'
    html = tpl.replace(PLACEHOLDER, payload)
    ok, msg = validate_js(html)
    if not ok:
        print('ERROR: JS 语法检查失败\n' + msg, file=sys.stderr)
        sys.exit(1)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    # 手机端硬约束自检
    bad = [m for m in ('prompt(', 'alert(', 'confirm(') if m in html]
    print(f"✅ {out_path}")
    print(f"   {len(data['days'])} 个 Day / {words} 词 / {len(html)/1024:.0f} KB")
    print(f"   JS: {msg}")
    if bad:
        print(f"   ⚠ 发现被手机浏览器屏蔽的 API: {bad}（应改成网页内弹窗）", file=sys.stderr)


if __name__ == '__main__':
    main()
