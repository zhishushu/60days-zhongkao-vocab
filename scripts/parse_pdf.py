#!/usr/bin/env python3
"""把 ocr_pdf.py 的逐页结果解析成词表 JSON（vocab-quiz 格式）。

用法:
    python parse_pdf.py <ocr_dir> <out.json> [--title "中考英语复习词汇"]

解析规则（对应《5年中考3年模拟·词汇册》排版）：
  每页两栏；一栏内同 y 的多个识别框合并成“视觉行”。
  行以 `数字.` 开头 = 新词条；`×`/`※` = 短语；`→` = 变形/派生词；其余并入上一词条的释义。
"""
import argparse
import glob
import json
import os
import re
import sys

CJK = re.compile(r'[\u3400-\u9fff]')
POS_TOK = r'(?:n|v|vt|vi|adj|adv|pron|conj|prep|interj|num|aux|art|det|modal\s*v)\.'
POS_RE = re.compile(r'\b' + POS_TOK, re.I)
IPA_RE = re.compile(r'[／/]([^／/]{1,40})[／/]')
CN_OK = set('；，。、（）…·—－～《》“”‘’！？：$%℃')
FORM_LABEL = re.compile(r'[（(]\s*([^）)]{1,20})\s*[）)]')


def clean_cn(s):
    s = re.sub(r'答案见.*$|扫码.*$|根据所给.*$', ' ', s)
    s = s.replace(';', '；').replace(',', '，').replace(':', '：').replace('|', '；')
    s = ''.join(ch for ch in s if CJK.match(ch) or ch in CN_OK or ch.isdigit())
    s = s.replace('，', '；').replace('：', '；').replace('、', '；')
    s = re.sub(r'；{2,}', '；', s).strip('；;-· ')
    parts = [p.strip() for p in s.split('；') if p.strip()]
    out, seen = [], set()
    for p in parts:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return '；'.join(out)


def split_en_cn(s):
    """把 'xxx 中文' 拆成 (英文部分, 中文部分)"""
    m = CJK.search(s)
    if not m:
        return s.strip(), ''
    return s[:m.start()].strip(), s[m.start():].strip()


def band_lines(items, y_tol=14):
    """同栏内按 y 聚类成视觉行，行内按 x 排序拼接"""
    rows = []
    for it in sorted(items, key=lambda r: (r[0], r[1])):
        y, x0, x1, t = it[0], it[1], it[2], it[3]
        if rows and abs(y - rows[-1]['y']) <= y_tol:
            rows[-1]['parts'].append((x0, t))
            rows[-1]['y'] = min(rows[-1]['y'], y)
            rows[-1]['x1'] = max(rows[-1]['x1'], x1)
        else:
            rows.append({'y': y, 'x1': x1, 'parts': [(x0, t)]})
    out = []
    for r in rows:
        r['parts'].sort()
        txt = ' '.join(p[1] for p in r['parts'])
        out.append((r['y'], r['x1'], re.sub(r'\s{2,}', ' ', txt).strip()))
    return out


def parse_entry_head(txt):
    """'5.buy /bal/ v.购买;买' -> dict"""
    body = re.sub(r'^\s*\d{1,3}\s*[.,、]\s*', '', txt)
    body = IPA_RE.sub(' ', body)             # OCR 的音标不可用，丢弃
    words = re.split(r'\s{2,}', body, maxsplit=1)
    m = re.match(r'^([A-Za-z][A-Za-z\'’\-\. ]*?)(?=\s|$)', body)
    if not m:
        return None
    en = m.group(1).strip(' .,')
    rest = body[m.end():]
    pos = []
    for pm in POS_RE.finditer(rest):
        pos.append(pm.group(0).replace(' ', '').lower().strip('.'))
    rest = POS_RE.sub('；', rest)          # 多词性释义之间补分号
    cn = clean_cn(rest)
    if not en:
        return None
    return {'en': en, 'pos': '/'.join(dict.fromkeys(pos)), 'cn': cn}


def parse_phrase(txt):
    body = re.sub(r'^\s*[×xX※\*＊]\s*', '', txt)
    body = IPA_RE.sub(' ', body)
    en, cn = split_en_cn(body)
    en = re.sub(r'^[\-→>\s]+', '', en).strip(' .')
    cn = clean_cn(cn)
    if not en or not CJK.search(cn or ''):
        return None
    return {'en': en, 'cn': cn}


def parse_form(txt):
    body = re.sub(r'^\s*[\-]?\s*[→一➜]\s*', '', txt)
    en, cn = split_en_cn(body)
    label = ''
    lm = FORM_LABEL.search(body)
    if lm:
        label = clean_cn(lm.group(1))
    cn_clean = clean_cn(cn)
    if cn_clean and not label:
        label = cn_clean
    en = re.sub(r'[（(].*$', '', en)
    en = re.sub(r'\b' + POS_TOK, ' ', en, flags=re.I)      # 去掉词性标记
    en = re.sub(r'\s+', ' ', en).strip(' .,/')
    if not re.match(r"^[A-Za-z][A-Za-z'’\- ]*$", en or ''):
        return None
    return {'w': en, 'label': label}


def parse_page(page):
    """返回 (day_name, entries, exercises)"""
    w, h = page['w'], page['h']
    items = page['items']
    head_text = ' '.join(i[3] for i in items[:12])
    m = re.search(r'Day\s*(\d+)', head_text)
    day = 'Day ' + m.group(1) if m else None

    # 正文区域（去掉页眉页脚与底部小练）
    body_top = h * 0.075
    body_bottom = h * 0.70
    ex_top = h * 0.70
    mid = w * 0.5
    left = [i for i in items if i[1] < mid and body_top <= i[0] <= body_bottom]
    right = [i for i in items if i[1] >= mid and body_top <= i[0] <= body_bottom]
    ex_items = [i for i in items if i[0] > ex_top and i[0] < h * 0.95]

    entries = []
    cur = None
    for col in (left, right):
        for y, x1, txt in band_lines(col):
            if not txt or '扫码' in txt or '打卡' in txt or re.match(r'^Day\s*\d+', txt):
                continue
            if re.match(r'^\s*\d{1,3}\s*[.,、]', txt):
                e = parse_entry_head(txt)
                if not e:
                    continue
                cur = {'en': e['en'], 'pos': e['pos'], 'cn': e['cn'], 'forms': [], 'phrases': []}
                entries.append(cur)
                continue
            if re.match(r'^\s*[×xX※\*＊]', txt):
                p = parse_phrase(txt)
                if p and cur:
                    cur['phrases'].append(p)
                continue
            if re.match(r'^\s*[\-]?\s*[→一➜]', txt):
                f = parse_form(txt)
                if f and cur:
                    cur['forms'].append(f)
                continue
            # 续行：多词性释义 / 短语的中文
            if cur is not None:
                extra_cn = clean_cn(txt)
                if extra_cn and CJK.search(extra_cn):
                    # 若上一行是短语且其 cn 缺失，则补到短语上
                    if cur['phrases'] and not cur['phrases'][-1]['cn']:
                        cur['phrases'][-1]['cn'] = extra_cn
                    else:
                        cur['cn'] = (cur['cn'] + '；' + extra_cn).strip('；')
    exercises = parse_exercises(ex_items)
    return day, entries, exercises


def parse_exercises(items):
    """底部『即时小练』：先拼成连续文本，再按题号切句，括号里是提示词。"""
    if not items:
        return []
    keep = [i for i in items if not re.search(r'即时小练|答案见|根据所给|第一部分|背默练|扫码|课标词汇', i[3])]
    if not keep:
        return []
    text = ' '.join(t for _, _, t in band_lines(keep, y_tol=20))
    text = re.sub(r'\s+', ' ', text).strip()
    parts = re.split(r'(?:^|(?<=\s))(\d{1,2})\s*[.,、]\s*', text)
    out = []
    for k in range(1, len(parts) - 1, 2):
        s = parts[k + 1].strip()
        m = re.search(r'[（(]\s*([A-Za-z][A-Za-z\- ]{1,20}?)\s*[）)]', s)
        if not m:
            continue
        root = m.group(1).strip().lower()
        stem = s[:m.start()].rstrip(' ,.;')
        tail = s[m.end():]
        if '__' not in stem:
            stem = stem + ' ____'
        sentence = (stem + tail).strip()
        sentence = re.sub(r'\s+([.!?,;])', r'\1', sentence)
        if len(sentence) < 12 or not re.search(r'[A-Za-z]{3,}', sentence):
            continue
        out.append({'s': sentence, 'root': root, 'ans': '', 'note': ''})
    return out


def load_ipa_dict(path):
    """加载 ipa-dict 的 en_US.txt（word<TAB>/ipa/）"""
    d = {}
    if not path or not os.path.exists(path):
        return d
    with open(path, encoding='utf-8') as f:
        for line in f:
            parts = line.rstrip('\n').split('\t')
            if len(parts) >= 2:
                d[parts[0].strip().lower()] = parts[1].split(',')[0].strip()
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('ocr_dir')
    ap.add_argument('out')
    ap.add_argument('--title', default='中考英语复习词汇')
    ap.add_argument('--ipa-dict', default='', help='ipa-dict 的 en_US.txt（可选，质量更好）')
    a = ap.parse_args()

    try:
        import eng_to_ipa as ipa
    except ImportError:
        ipa = None
    ipa_map = load_ipa_dict(a.ipa_dict)

    days = []
    stats = {'pages': 0, 'entries': 0, 'skipped_pages': 0, 'ex_pool': 0, 'ex_attached': 0}
    ex_pool = []
    last_no = 0
    for f in sorted(glob.glob(os.path.join(a.ocr_dir, 'p*.json'))):
        page = json.load(open(f, encoding='utf-8'))
        stats['pages'] += 1
        day, entries, exercises = parse_page(page)
        # 词表页 = 有 Day 页眉 + 词条够多；第二/三部分的辨析页、构词表跳过
        if not entries or len(entries) < 8:
            stats['skipped_pages'] += 1
            continue
        if day and day.startswith('Day '):
            try:
                last_no = int(day.split()[1])
            except ValueError:
                pass
        else:
            last_no += 1
            day = f'Day {last_no}'
        for e in entries:
            key = e['en'].lower()
            got = ipa_map.get(key)
            if got:
                e['ipa'] = got if got.startswith('/') else '/' + got + '/'
            elif ipa and re.match(r'^[A-Za-z\- ]+$', e['en']):
                p = ipa.convert(key)
                if p and not p.startswith('*'):
                    e['ipa'] = '/' + p.replace('ʧ', 'tʃ').replace('ʤ', 'dʒ') + '/'
        kept = [e for e in entries if e['cn']]
        stats['entries'] += len(kept)
        days.append({'day': day, 'page': page['page'], 'words': kept})
        ex_pool.extend(exercises)

    # 例句按提示词挂到全书的词条上（提示词可能不在当天这页）
    stats['ex_pool'] = len(ex_pool)
    index = {}
    for d in days:
        for w in d['words']:
            index.setdefault(w['en'].lower(), w)
    for ex in ex_pool:
        w = index.get(ex['root'])
        if not w:
            continue
        w.setdefault('ex', []).append(ex)
        stats['ex_attached'] += 1
    # 合并同一天重复词条
    for d in days:
        seen, uniq = set(), []
        for w in d['words']:
            if w['en'].lower() in seen:
                continue
            seen.add(w['en'].lower())
            uniq.append(w)
        d['words'] = uniq
    days = [d for d in days if len(d['words']) >= 5]

    data = {'title': a.title, 'days': days}
    with open(a.out, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    print(json.dumps(stats, ensure_ascii=False), 'days:', len(days))
    print('out:', a.out, os.path.getsize(a.out) // 1024, 'KB')


if __name__ == '__main__':
    main()
