# 词表 JSON 规范（60days-zhongkao-vocab）

`generate.py` 接受的输入。最小可用：`{"title": "...", "days": [{"day":"Day 1","words":[{"en":"able","cn":"能够的"}]}]}`。

```json
{
  "title": "中考英语复习词汇（课标1600词 · 5·3词汇册）",
  "days": [
    {
      "day": "Day 1",
      "page": 4,
      "words": [
        {
          "en": "able",
          "ipa": "/ˈeɪbəl/",
          "pos": "adj",
          "cn": "能够；有才能的",
          "forms": [
            {"w": "unable", "label": "未能；无法"},
            {"w": "ability", "label": "能力；才能"}
          ],
          "phrases": [
            {"en": "be able to do sth", "cn": "能够做某事"},
            {"en": "have the ability to do sth", "cn": "有能力做某事"}
          ],
          "ex": [
            {
              "s": "Children believe that the Monkey King is a hero who has many ____.",
              "root": "able",
              "ans": "abilities",
              "zh": "孩子们相信美猴王是一个有许多本领的英雄。",
              "note": "填 able 的名词复数形式，作 has 的宾语"
            }
          ]
        }
      ]
    }
  ]
}
```

## 字段

| 字段 | 必填 | 说明 |
|---|---|---|
| `title` | 否 | 首页大标题下面的说明行 |
| `days[].day` | 是 | 分组名，首页/词汇表按它分块，如 `Day 12` |
| `days[].page` | 否 | 原书页码，溯源用 |
| `words[].en` | 是 | 英文单词/短语；判分时忽略大小写与首尾空格 |
| `words[].cn` | 是 | 中文释义；**多个义项用全角分号 `；` 分隔**，答出任一即算对 |
| `words[].ipa` | 否 | 音标，带斜杠，如 `/ˈeɪbəl/`；建议用 ipa-dict 生成，不要用 OCR 结果 |
| `words[].pos` | 否 | 词性缩写，`n/v/adj/adv/prep/conj/pron/num/det/art/interj`，多词性用 `/` 连接（`n/v`） |
| `words[].forms` | 否 | 派生词 / 词形变化。`w` 是变形后的词，`label` 是中文或「过去式/过去分词」这类说明；做题时用于「例句填空」的宽松判分 |
| `words[].phrases` | 否 | 短语搭配，解析卡里以 chip 展示；`en` 英文、`cn` 中文 |
| `words[].ex` | 否 | 例句。`s` 用 `____`（≥2 个下划线）表示挖空位；`root` 是括号里的提示词（小写）；`ans` 是标准答案（**严格判分必填**，多写法用 `/` 分隔）；`zh` 是整句中文意思（**学习页必备**，学生看句子时下面是这一行）；`note` 是解析提示，留空则不显示 |

## 约定

- `cn` 只用汉字、全角标点、阿拉伯数字；不要混入英文、音标符号（`ˈ ɪ ʃ ə ɡ` 等），否则「看英文写中文」会显示乱码。
- 多义项务必分号分隔：`速度；超速行驶；加速`。整段粘连会让判分把整句当唯一正确答案。
- 例句里 `____` 前后留空格，模板据此高亮填空；`ans` 为空时判分退回「该词任意词形」的宽松匹配，**正式交付前必须补全**（见下节）。
- 一个词可以挂多条 `ex`：答题时随机抽一条，学习页会把该词的全部例句都列出来（空位已用 `ans` 补全，句子下面跟一行 `zh` 中文）。

## 补全 ex.zh（每条例句的中文意思）

学习页每条例句下面都要有一行中文，**没有 `zh` 就是缺功能**（用户会直接指出「例句要有中文意思」）。书里的例句都是英文，`zh` 只能自己写：

1. 先按固定顺序把例句导出成表（带上序号/单词/答案，一眼能看出空里该填什么），例如
   `for i,(w,e) in enumerate(exs): print(f"{i}\t{day}\t{w['en']}\t{e['ans']}\t{e['s']}")`；
2. 按这个顺序写一份中文列表（一条一行，语气跟书里的译文一致，把答案嵌进译句里，不要直译成断句）；
3. 用脚本写回，**必须断言条数相等再落盘**：
   ```python
   assert len(exs) == len(ZH) == 176, (len(exs), len(ZH))
   for i, e in enumerate(exs): e['zh'] = ZH[i]
   ```
4. 同一趟顺手修 OCR 残缺（列表里单列的 `FIX = {序号: 完整句}`）：`1 used ...` → `I used ...`、`until he was` → `until he was 70.`、`1 am ...` → `I am ...`。
5. 校验：`sum(1 for ... if e.get('zh'))` 必须等于例句总数，再抽查 5 条语序与答案是否对得上。

## 补全 ex.ans（严格判分的前提）

书里写「答案见《答案册》」时 `ans` 是空的，而「真题大作战」要求与 `ans` 完全一致才算对，所以补答案是**上线前的硬门禁**：

1. 按固定顺序导出全部例句（`for d in days for w in d['words'] for e in w['ex']`），后面写回必须用同一个顺序；
2. 逐题按句子语法定答案：词形题看主谓一致/单复数/时态（`many ____ → abilities`、`be ____ not to → careful`、`will ____ → disappear`），动词位看 `to do` / `doing` / 过去式；
3. 用脚本批量写回：`assert len(exs)==len(answers)` 后 `for (w,e),a in zip(exs,answers): e['ans']=a`，一次 `json.dump` 落盘；手改 JSON 必错行；
4. 两种写法都算对时写 `organization/organisation`、`practising/practicing`，判分按 `/` 拆开任一命中；
5. 落盘后校验覆盖率，必须等于例句总数：
   ```python
   sum(1 for d in days for w in d['words'] for e in w.get('ex',[]) if e.get('ans'))
   ```
6. 交付时告诉用户「答案是按语法补的」，请他拿答案册抽查，个别差异用 `/` 追加。
## 真题库 exercises（可选，一般自动注入）

`generate.py` 会先看词表里有没有顶层 `exercises`，没有就把 `assets/exercises-答案册.json`（答案册导出的题库）注入成 `DATA.exercises`，「真题大作战」直接用它，不再从 `words[].ex` 抽题。换一本书时重新跑 `scripts/import_answers.py` 即可，不用动词表。

```json
"exercises": [
  {"d": "Day 1", "no": 3, "s": "…has many ____ (able).", "h": "able", "ans": "abilities", "note": "【解析】原文"}
]
```

`d`=Day 名、`no`=原书题号、`s`=带 `____` 的句子、`h`=括号提示词（首字母题留空）、`ans`=标准答案、`note`=解析。见 `references/answer-key-import.md`。

- 数据量参考：约 25 词/天 × 60 天 ≈ 1500 词，JSON 约 220 KB，生成的单文件 HTML 约 230 KB，手机打开无压力。
