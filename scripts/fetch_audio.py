#!/usr/bin/env python3
"""生成离线单词语音包：词表 JSON → audio/<slug>.mp3

- 默认取有道美音（dictvoice?type=2），失败自动重试并回落到百度 TTS
- 下载后用 ffmpeg 压成 22.05kHz 单声道 24kbps，体积约为原来的 1/3
- 已存在的文件会跳过，可反复续跑
- 文件名规则必须和模板里的 slugOf() 一致：小写 + 非字母数字变下划线

用法：
  python scripts/fetch_audio.py wordlist.json audio/ [--workers 6] [--no-phrases]
"""
import argparse
import concurrent.futures as cf
import json
import os
import random
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')


def slug(text):
    return re.sub(r'^_+|_+$', '', re.sub(r'[^a-z0-9]+', '_', str(text or '').lower()))


def fetch(url, timeout=6):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def is_mp3(data):
    if not data or len(data) < 800:
        return False
    if data[:3] == b'ID3':
        return True
    return data[0] == 0xFF and (data[1] & 0xE0) == 0xE0


def download(text, tries=4):
    """返回 (bytes, source) 或 (None, error)"""
    youdao = 'https://dict.youdao.com/dictvoice?' + urllib.parse.urlencode({'audio': text, 'type': 2})
    baidu = 'https://fanyi.baidu.com/gettts?' + urllib.parse.urlencode(
        {'lan': 'en', 'text': text, 'spd': 3, 'source': 'web'})
    last = None
    for i in range(tries):
        try:
            d = fetch(youdao)
            if is_mp3(d):
                return d, 'youdao'
            last = 'youdao: bad audio'
        except Exception as e:
            last = 'youdao: %s' % e
        time.sleep(0.15 + 0.2 * i)
    for i in range(2):
        try:
            d = fetch(baidu)
            if is_mp3(d):
                return d, 'baidu'
            last = 'baidu: bad audio'
        except Exception as e:
            last = 'baidu: %s' % e
        time.sleep(0.2)
    return None, last


def ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def transcode(raw, exe, bitrate='24k'):
    if not exe:
        return raw
    try:
        p = subprocess.run(
            [exe, '-hide_banner', '-loglevel', 'error', '-i', 'pipe:0',
             '-ac', '1', '-ar', '22050', '-b:a', bitrate, '-f', 'mp3', 'pipe:1'],
            input=raw, capture_output=True, timeout=30)
        if p.returncode == 0 and len(p.stdout) > 400:
            return p.stdout
    except Exception:
        pass
    return raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('wordlist')
    ap.add_argument('outdir')
    ap.add_argument('--workers', type=int, default=6)
    ap.add_argument('--no-phrases', action='store_true')
    args = ap.parse_args()

    data = json.load(open(args.wordlist, encoding='utf-8'))
    words, phrases = [], []
    for day in data['days']:
        for w in day['words']:
            words.append(w['en'])
            for p in w.get('phrases') or []:
                if p.get('en'):
                    phrases.append(p['en'])
        phrases.extend(p.get('en') for p in (day.get('phrases') or []) if p.get('en'))

    texts, seen = [], set()
    for t in (words + ([] if args.no_phrases else phrases)):
        s = slug(t)
        if s and s not in seen:
            seen.add(s)
            texts.append(t)

    os.makedirs(args.outdir, exist_ok=True)
    exe = ffmpeg_exe()
    todo = [t for t in texts if not os.path.exists(os.path.join(args.outdir, slug(t) + '.mp3'))]
    print('待生成 %d 条（已有 %d 条），ffmpeg=%s' % (len(todo), len(texts) - len(todo), 'yes' if exe else 'no'))

    ok = fail = 0
    failed = []
    src_stat = {}
    t0 = time.time()

    def work(text):
        raw, src = download(text)
        if not raw:
            return text, None, src
        return text, transcode(raw, exe), src

    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for text, data_bytes, src in pool.map(work, todo):
            if not data_bytes:
                fail += 1
                failed.append((text, src))
                print('  ✗ %-24s %s' % (text, src))
                continue
            path = os.path.join(args.outdir, slug(text) + '.mp3')
            with open(path, 'wb') as f:
                f.write(data_bytes)
            ok += 1
            src_stat[src] = src_stat.get(src, 0) + 1
            if ok % 50 == 0:
                print('  ... %d/%d  %.0fs' % (ok, len(todo), time.time() - t0))

    total = 0
    for name in os.listdir(args.outdir):
        if name.endswith('.mp3'):
            total += os.path.getsize(os.path.join(args.outdir, name))
    manifest = {
        'generated': time.strftime('%Y-%m-%d %H:%M'),
        'words': len(words), 'phrases': 0 if args.no_phrases else len(phrases),
        'clips': len([f for f in os.listdir(args.outdir) if f.endswith('.mp3')]),
        'bytes': total, 'sources': src_stat,
    }
    json.dump(manifest, open(os.path.join(args.outdir, 'manifest.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('完成：新增 %d，失败 %d，总计 %d 条 / %.1f MB，用时 %.0fs'
          % (ok, fail, manifest['clips'], total / 1048576.0, time.time() - t0))
    if failed:
        print('失败清单（可重跑本命令补齐）：')
        for t, e in failed[:40]:
            print('  ', t, '|', e)
        sys.exit(0)


if __name__ == '__main__':
    main()
