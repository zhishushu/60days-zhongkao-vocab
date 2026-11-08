#!/usr/bin/env python3
"""把《词汇答案册》导入成真题大作战的真题库。

输入：两套 OCR 结果（词册页 + 答案册页，由 ocr_pdf.py 生成）
输出：assets/exercises-答案册.json  —— [{d,no,s,h,ans,note}]

做法：
  1. 词册页：每页底部「即时小练」是编号句子，页码 p004 = Day 1（pN = Day N-3），
     框间距 > 55px 处就是原书的填空下划线。
  2. 答案册页：两栏流式排版，每段「Day N 即时小练」后面是 1.xxx 2.xxx，
     部分条目带【解析】；遇到「第二部分」即停（那是别的题型）。
  3. 两边按 Day + 题号配对，题号对不上时用提示词/首字母兜底。
"""
import argparse
import glob
import json
import os
import re
import sys

NUM = re.compile(r'(?:^|(?<=[\s,，]))(\d{1,2})\s*[.．、]\s*')
LATIN_PAREN = re.compile(r'\(\s*([A-Za-z][A-Za-z /\'-]{0,20})\s*\)')


# ---------------- 词册：即时小练句子 ----------------
def visual_lines(page):
    ts = sorted(page['items'], key=lambda t: (t[0], t[1]))
    groups = []
    for t in ts:
        if groups and abs(t[0] - groups[-1][0][0]) < 16:
            groups[-1][1].append(t)
        else:
            groups.append([t, [t]])
    out = []
    for head, g in groups:
        g.sort(key=lambda t: t[1])
        parts, prev = [], None
        for t in g:
            if prev is not None and t[1] - prev[2] > 55:
                parts.append('  ____  ')
            parts.append(t[3])
            prev = t
        out.append([head[0], ''.join(parts).replace('  ', ' ')])
    return out


def parse_exercise_page(page):
    lines = visual_lines(page)
    start = None
    for i, (y, s) in enumerate(lines):
        if '即时小练' in s:
            start = i
            break
    if start is None:
        return []
    items, cur = [], None
    for y, s in lines[start + 1:]:
        s = s.strip()
        if not s or '答案见' in s:
            continue
        if '课标词汇' in s or '第一部分' in s:
            break
        m = re.match(r'^(\d{1,2})\s*[.．]\s*(.*)$', s)
        if m:
            if cur:
                items.append(cur)
            cur = {'no': int(m.group(1)), 'text': m.group(2)}
        elif cur is not None:
            cur['text'] = (cur['text'] + ' ' + s).strip()
    if cur:
        items.append(cur)
    return items


def load_exercises(ocr_dir):
    out = {}
    for f in sorted(glob.glob(os.path.join(ocr_dir, 'p*.json'))):
        idx = int(re.search(r'p(\d+)\.json', os.path.basename(f)).group(1))
        day = idx - 3                      # p004 = Day 1
        if not 1 <= day <= 200:
            continue
        items = parse_exercise_page(json.load(open(f, encoding='utf-8')))
        if items:
            out['Day %d' % day] = items
    return out


# ---------------- 答案册 ----------------
def col_lines(path):
    d = json.load(open(path, encoding='utf-8'))
    mid = d['w'] / 2.0
    out = []
    for col in (0, 1):
        its = [t for t in d['items'] if (((t[1] + t[2]) / 2.0 < mid) == (col == 0))]
        its.sort(key=lambda t: (t[0], t[1]))
        groups = []
        for it in its:
            if groups and abs(it[0] - groups[-1][0]) < 16:
                groups[-1][1].append(it)
            else:
                groups.append([it[0], [it]])
        for y, g in groups:
            g.sort(key=lambda t: t[1])
            out.append((y, ' '.join(t[3] for t in g)))
    return out


def split_segments(line):
    line = re.sub(r'(?<=[a-zA-Z])(?=\d{1,2}[.．])', ' ', line)
    marks = [(m.start(), m.end(), int(m.group(1))) for m in NUM.finditer(line)]
    segs = []
    for i, (s, e, no) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(line)
        body = line[e:end].strip()
        ans, note = body, ''
        m = re.search(r'[【\[]\s*解析\s*[】\]]', body)
        if m:
            ans, note = body[:m.start()].strip(), body[m.end():].strip()
        ans = re.sub(r'[【\[]\s*解析\s*[】\]]$', '', ans).strip()
        segs.append([no, ans, note])
    return segs


def parse_answers(ocr_dir):
    days, cur, stop = {}, None, False
    for p in sorted(glob.glob(os.path.join(ocr_dir, 'p*.json'))):
        if stop:
            break
        for y, line in col_lines(p):
            line = line.strip()
            if not line:
                continue
            if '第二部分' in line:      # 后面的题型不导入
                stop = True
                break
            m = re.match(r'^Day\s*(\d{1,2})', line)
            if m:
                cur = 'Day %d' % int(m.group(1))
                days.setdefault(cur, [])
                rest = line[m.end():].replace('即时小练', '').strip()
                for no, a, n in split_segments(rest):
                    if a:
                        days[cur].append([no, a, n])
                continue
            if cur is None:
                continue
            segs = split_segments(line)
            if segs:
                days[cur].extend([[no, a, n] for no, a, n in segs if a])
            elif days[cur] and days[cur][-1][2]:
                days[cur][-1][2] = (days[cur][-1][2] + ' ' + line).strip()
    return days


# ---------------- 清洗 ----------------
FIX_ANS = {'1ovely': 'lovely', 'l0vely': 'lovely', 'ordering g': 'ordering', 'spend 1': 'spend',
           'cost t': 'cost', 'technologies[': 'technologies', '1uck': 'luck'}
FIX_S = {'as 1 long as': 'as long as', 'hhabit': 'habit'}
# 答案册 Day 52 有两个系列的题号，印刷时撞号；按句子语义校正
DAY_FIX = {('Day 52', 5): 'up', ('Day 52', 6): 'thankful', ('Day 52', 7): 'thoughts'}


def clean_s(s):
    s = s.strip()
    s = re.sub(r'\s+\d{1,3}$', '', s)
    s = s.replace('？', '?').replace('！', '!').replace('，', ',')
    s = s.replace('（', '(').replace('）', ')')
    for a, b in FIX_S.items():
        s = s.replace(a, b)
    s = re.sub(r'(^|[.!?]\s+)1(?=\s+[a-z])', lambda m: m.group(1) + 'I', s)
    s = re.sub(r'\s+1\s*(?=____)', ' ', s)
    s = re.sub(r'([A-Za-z]{2,})____', r'\1 ____', s)
    s = re.sub(r'\)____', r') ____', s)
    s = re.sub(r'\s*_{2,}\s*\(', '____ (', s)
    s = re.sub(r'\(\s+', '(', s)
    s = re.sub(r'\s+\)', ')', s)
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'\s+([,.?!;:])', r'\1', s)
    s = re.sub(r',\s*\.', '.', s)
    if s and s[-1] not in '.?!")':
        s += '.'
    return s.strip()


def clean_ans(a):
    a = FIX_ANS.get(a.strip(), a.strip())
    a = a.replace('（', '(').replace('）', ')')
    a = re.sub(r'\s+', ' ', a)
    a = re.sub(r'\s+([,/])', r'\1', a)
    return a.strip(' .,')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--words-ocr', required=True, help='词册 PDF 的 OCR 目录')
    ap.add_argument('--answers-ocr', required=True, help='答案册 PDF 的 OCR 目录')
    ap.add_argument('--out', required=True, help='输出 exercises json')
    args = ap.parse_args()

    E = load_exercises(args.words_ocr)
    A = parse_answers(args.answers_ocr)
    out, miss = [], []
    for day, items in E.items():
        if day not in A:
            continue
        by_no = {it['no']: it for it in items}
        for no, ans, note in A[day]:
            it = by_no.pop(no, None)
            if it is None:
                miss.append((day, no, ans))
                continue
            s = clean_s(it['text'])
            a = clean_ans(ans)
            if '____' not in s or not a:
                continue
            cands = [c for c in LATIN_PAREN.findall(s) if c.lower() not in ('n', 'a', 'an', 'to')]
            out.append({'d': day, 'no': no, 's': s, 'h': cands[0] if cands else '',
                        'ans': a, 'note': re.sub(r'\s+', ' ', note or '').strip()})
    out.sort(key=lambda o: (int(o['d'].split()[1]), o['no']))
    # 答案册 Day 52 的题号印重了（5. 6. 出现两次），按句子语义校正
    for o in out:
        key = (o['d'], o['no'])
        if key in DAY_FIX:
            o['ans'] = DAY_FIX[key]
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    json.dump(out, open(args.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('导入 %d 题（带解析 %d）→ %s' % (len(out), sum(1 for o in out if o['note']), args.out))
    if miss:
        print('答案册有题号但词册没抓到的句子：', len(miss), '条（多为扫描截断，已跳过）', file=sys.stderr)


if __name__ == '__main__':
    main()
