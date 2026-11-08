---
name: 60days-zhongkao-vocab
description: Use when 中考英语词汇复习/背单词/默写/词汇游戏。生成单文件 HTML：先学后玩的三个词汇游戏、听写闯关、真题大作战、艾宾浩斯复习与报告（均可导出 PDF）。
version: 1.7.0
author: Elaine-Wu Yi
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [education, vocabulary, 中考, single-file-html, ocr]
    homepage: https://github.com/zhishushu/60days-zhongkao-vocab
    related_skills: [vocab-quiz-builder, dogfood]
---

# 60天搞定中考词汇（60days-zhongkao-vocab）

> **安装**：把整个目录放进助手的 skills 目录即可（Hermes：`$HERMES_HOME/skills/productivity/60days-zhongkao-vocab/`；
> Claude Code：`~/.claude/skills/60days-zhongkao-vocab/`），或直接跑仓库根目录的 `./install.sh` / `.\install.ps1`。
> 所有脚本按 **本文件所在目录** 解析 `assets/`、`references/`，所以装在哪里都能用；不装进助手也能直接
> `python3 scripts/generate.py 词表.json out.html`。

把一本中考词汇书（或一份词表）变成学生手机浏览器就能用的**单文件 HTML 训练器**：
「单词流星雨」（按 Day 玩消消乐/对对碰/连连看，游戏即复习）、「单词翻译官」（中→英 / 英→中随机）、「听写闯关」、「真题大作战」，外加「学习中心」（艾宾浩斯抗遗忘复习 / 错题本 / 学习报告 / 排行榜）。答题期间只回对错，**答满规定题数后才在结果页给答案与逐题解析**（音标 + 词性 + 释义 + 派生词 + 短语 + 例句）。进门前必须名字+密码登录。

## When to Use（什么时候用）

- 用户给一本中考英语词汇/单词表 PDF（多为**扫描版**），想要默写、背诵、听写工具
- 用户说「看中文写英文」「看英文写中文」（都归到「单词翻译官」一个入口里随机切换）
- 用户要求「背单词网页」「词汇训练器」「单词测试」
- 已有词表 JSON（或改了一本教材/一册），只想重新生成页面或换配色

## 目录

```
60days-zhongkao-vocab/
├── SKILL.md
├── scripts/
│   ├── ocr_pdf.py        # 扫描版 PDF → 逐页 OCR 结果(json)
│   ├── parse_pdf.py      # OCR 结果 → 词表 JSON（音标/释义/短语/派生/例句）
│   ├── import_answers.py # 《词汇答案册》OCR → 真题大作战真题库（答案 + 解析）
│   ├── generate.py       # 词表 JSON + 模板 → 单文件 HTML（带 JS 语法自检）
│   └── cdp_verify.js     # 通用回归跑分器：Edge headless + CDP 按 steps.json 断言/截图/导出入盘
├── assets/
│   ├── coach-template.html   # 应用模板（浅粉主题 · 三个游戏 · 内置键盘 · 艾宾浩斯 · 错题本 · 报告）
│   ├── exercises-答案册.json # 334 道真题（标准答案 + 解析），generate.py 自动注入 DATA.exercises
│   ├── coach-template-v1-backup.html  # 旧暗色版，仅作对照，generate.py 不用
│   ├── coach-template-v2-backup.html  # 上一版（无游戏），仅作对照
│   └── sample-wordlist.json  # 2 天示例数据，可直接跑通流程
└── references/
    ├── wordlist-schema.md    # 词表 JSON 字段规范
    ├── answer-key-import.md  # 《答案册》→ 真题大作战题库的完整导入手册（分栏/配对/清洗/显示层）
    ├── qa-cdp-checks.md      # 单文件 HTML 的自动回归断言清单（Edge headless + CDP）
    └── print-export.md       # 错题本/复习计划/学习报告导出成可打印 A4（PDF）的配方
```

## 三步生成

```bash
PY="C:/H/Hermes-Portable-v0.21.6-Windows-x64/Hermes-Portable-v0.21.6-Windows-x64/hermes/app/runtime/python-win-x64/cpython-3.14.8-windows-x86_64-none/python.exe"
SK="C:/H/Hermes-Portable-v0.21.6-Windows-x64/Hermes-Portable-v0.21.6-Windows-x64/data/hermes/state/skills/productivity/60days-zhongkao-vocab"

# 1) 扫描版 PDF → OCR（106 页约 12 分钟；已存在的结果会跳过，可反复续跑）
"$PY" "$SK/scripts/ocr_pdf.py" 课本.pdf out/ocr --dpi 200

# 2) OCR → 词表 JSON（--ipa-dict 可选，用 ipa-dict 的 en_US.txt 质量更好）
"$PY" "$SK/scripts/parse_pdf.py" out/ocr wordlist.json --title "中考英语复习词汇" --ipa-dict en_US_ipa.txt

# 3) 词表 JSON → 单文件 HTML（自动 node --check 校验 JS）
"$PY" "$SK/scripts/generate.py" wordlist.json 单词训练.html
```

只想要个能跑通的样例：`"$PY" "$SK/scripts/generate.py" "$SK/assets/sample-wordlist.json" demo.html`

## 应用功能（模板已内置，改模板前先看这里）

界面与交互是**用户逐条定过的**，改模板时不要回退：

- **每次打开都先输名字+密码**：`boot()` 无条件 `renderWelcome()`；输入框每次都是空的、顶部用户栏隐藏。一个名字对一个密码（`user.pw` = `SHA-256('zk|'+密码)`，至少 4 位；`crypto.subtle` 在 `file://` 下可用，取不到时退化成字符串散列）。名字已存在且设过密码时密码不符就停在欢迎页并提示；老账号（没有 `pw`）第一次输入密码即设为新密码。**不要保留“选择用户”列表**——`openUserModal()` 现在只提示「回登录页切换」，`switchUser/addUser` 都改成提示，否则绕过密码。
- **退出登录**：顶栏「🏠 首页」右边固定一个「退出登录」，`logout()` 清 `DB.cur` 后直接 `renderWelcome()`（记录仍在 localStorage 里，同名+密码进来就接回）。
- **浅色小清新**：淡粉渐变背景（`--bg1..--bg3`）+ 白色卡片 + 粉玫瑰色按钮。用户明确否掉了暗色主题，不要再改回去。
- **首页顺序固定**：① 单词流星雨（第一）② 单词翻译官 ③ 听写闯关 ④ 真题大作战 ⑤ 学习中心。
- **模式命名口语化、同类合并**：中→英/英→中合并成「单词翻译官」；「听音默写」→「听写闯关」；「例句填空」→「真题大作战」；「词汇表」→「单词流星雨」并变成游戏入口；「今日复习」→「艾宾浩斯抗遗忘复习」。不要出现「看着中文写英文」「默写训练」这类旧文案。
- **答题期间零泄露**：只回 ✅/❌；不显示正确答案、不渲染解析卡、页面上不能出现「看答案」按钮。「答案与解析」只能在答满规定题数的结果页出现；中途退出不给答案、不记成绩。
- **界面上不要「教学式说明」**：学习页例句区只留 `🧩 例句`，不要写「点句子可朗读」，也不要在句子下面标「填：xxx」（答案直接嵌在句子里）；听写卡片只写「听发音，写出这个单词」，不要写「不给中文提示」「先点喇叭听一遍」；首页卡片只写功能白话（如「中考真题句子挖空，填出正确词形」），不要写题数、「答案册标准答案 + 解析」这类内部口径；欢迎页不要写「家里有多个孩子」这类提示。用户已多轮要求删这类字眼——写文案时先问「学生看一眼能知道怎么用吗」，不能就直接删。
- **一轮做完要给「下一轮」入口**：结果页统计块下面固定出现按钮——`nextLabel(mode)` 给「进入下一轮翻译 / 听写 / 作战」，`nextRound()` 用 `Q.cfg.words / Q.cfg.count` 原样再开一轮（重新洗牌），三种模式都要有，不要只给「回首页」。
- **连连看：线要和两张卡同一帧消失**：配对成功时立刻给两张卡加 `gone`，折线用 `drawPolyline(pts,220)`（200ms 内淡出移除）；不要再套 `setTimeout(...,180)` 才收卡——用户明确说“速度不能慢”。
- **`.tile.gone` 必须写 `transition:none`**：`.tile` 上有 `transition:.12s`，而 `visibility` 属于离散过渡，会到过渡结束才真正翻成 hidden——不覆盖的话卡片在「消失」后还要多显示 ~120ms，`getComputedStyle` 当场查也还是 `visible`（截图会看起来像没消掉）。
- **发音要「点了就响」**：按钮一律走 `speakNow()`——空闲时**不** `cancel()`（cancel→speak 会让引擎重新起麦，多几百毫秒），只有正在播/排队时才打断；同一个词正在读就直接返回、不重启；`speak()` 原来 250/700/1400 三次 retry 每次都先 cancel，等于自己把起麦推迟到 700ms+，现在只留一次 1.5s 兜底且不 cancel。
- **音色要优先本地**：`pickVoice()` 按 `localService`（+10）打 `Online (Natural)`（−8）、`Google`（−10）。Edge 默认的 "Microsoft Ava/… Online (Natural)" 是**联网合成**，在没装离线英语语音的机器上每次起麦都要几百毫秒——这是"点了半天才出声"的真正根因。代码只能优先本地音色；机器上一个本地英文音色都没有时（`getVoices()` 里 `en-*` 全是 `localService:false`），请用户到「设置 → 时间和语言 → 语音 → 管理语音 → 添加语音 → English (United States)」装一个，装完重启浏览器即秒响。
- **「重练本轮错题」要原样重做**：`retryWrong()` 不能只把错词丢给 `startQuiz(...,'trans')`——那样听写错题会变成中英互译、没有「听发音」，真题错题会变成随机句子。正确做法：按 `Q.log` 里每条 `{w,type,ex}` 重建 `Q`（沿用原 `mode`、`cfg.seconds/words`，`count=错题数`），听写模式还要 `unlockAudio()` 并先读第一题。三种模式都要能原题重做。
- **学习中心四个 tab**：艾宾浩斯复习 / 错题本 / 学习报告 / **排行榜**。排行榜把 `DB.users` 里所有有成绩的账号汇总，按「正确率降序 → 时长降序 → 题数降序」排，显示名次（前三 🥇🥈🥉）、名字、正确率、题数、时长，当前用户高亮并标「(我)」，顶部单独一块「我的排名 第 N 名」。
- **听写闯关的游戏规则**：只给发音、不给中文释义；卡片上只有一个「🔈 听发音」大按钮 + 输入框，进题仍自动读一遍。注意这是**游戏规则**，卡片文案不要写成「不给中文提示」「先点喇叭听一遍」这类说明句（见上一条）。
- **真题大作战严格判分**：只有和标准答案完全一致（忽略大小写/首尾空格，`/` 分隔的可接受写法任一命中）才算对；结果页每题都显示「你的答案 … 标准答案 … ✅一致/❌不一致」。
- **错题本只导出 PDF**：不再提供 txt。
- **学习报告**：四项固定 + 今日分析/建议 + 每一次练习记录 + 汇总，整份可导出 PDF。

### 1. 单词流星雨（首页第一个，**先学后玩**）

流程：选 Day → **第 1 步：学习本 Day 单词**（`openLearn(day)` 逐词卡片：音标/词性/释义/派生/短语/例句/🔊）→ 全部看过才出现「学完了，进入单词消消乐」→ 解锁三个游戏。

- 未学过的 Day，三个游戏卡显示 🔒（`.bigbtn.locked`），`startGame()` 里用 `canPlay()` 拦一手并跳去学习页。
- 学习进度存 `progress().learnSeen[day]=[已看下标]`，学完 `progress().learned[day]=日期`；Day 条形上给已学过的打 ✓。
- **学习页要给完整例句，且只留必要的字**：每个词的 `ex` 全部列出（不截断），空处直接把答案填进句子（`…has many abilities.`）；**不要**在标题写「点句子可朗读」、也不要在句子下面标「填：xxx」。但**每条例句下面必须有一行中文意思**（数据字段 `ex.zh`）；点单词、点短语、点句子照样都会朗读（`onclick="speak(...)"`），朗读靠图标暗示，不靠文字说明。
- **短语搭配只留含本词的**：`renderLearn()` 用单词边界正则过滤 `w.phrases`（`(^|[^a-z])词([^a-z]|$)`），一条都不含就整块不显示；否则学 able 会列出跟该词无关的短语。
- 三个游戏只用该 Day 的词，成绩存 `progress().games[day][kind]`（最好用时 + 次数）显示在卡片上。
- **游戏是链式的**：消消乐通关 → 「进入单词对对碰」；对对碰通关 → 「进入单词连连看」；连连看通关 → 「再来一轮」+「学下一个 Day」。

| 游戏 | 玩法 | 实现要点 |
|---|---|---|
| **单词消消乐** | 12 张卡片（6 对，英文/中文各一），点一张英文再点对应中文，配对即消除；点错抖动并计错 | 同 `data-pair` 即配对，`left` 归零过关；HUD「剩余」要手动更新 |
| **单词对对碰** | 12 张卡片背面朝上，每次翻两张，配对成功消除，失败 700ms 后盖回 | 记翻牌次数；`busy` 锁防止连点翻三张 |
| **单词连连看** | 24 张卡片（12 对），点一个单词再点对应中文 → 出现折线 → 两张卡和线一起消失 | **必须同 `pair` 且一 EN 一 CN 才算对**（`prev.pair===t.pair && prev.kind!==t.kind`）；配错只抖动计错、卡片不动。卡片对象字段就叫 `pair`（不是 `i`），`data-pair` 也用它——早期写成 `{i:...}` 而 `linkTap` 比的是 `.pair`，两边都是 `undefined`，导致**任意两张卡都能消**，用户立刻发现了 |

### 2. 三个练习模式

| 模式 | 说明 | 判分 |
|---|---|---|
| **单词翻译官** | 中→英 / 英→中 随机切换（英文用内置键盘，中文用系统输入法） | 英→中：分号拆义项命中任一即对；中→英：归一化后全等 |
| **听写闯关** | 听发音拼单词，进题**自动朗读**；**不给中文提示**，只有一个「🔈 听发音」大按钮（想再听就再点，靠听写词） | 同中→英 |
| **真题大作战** | 真题句挖空，**明示提示词**（「提示词：break（用它的正确形式填空）」；首字母题显示「提示词：a（首字母提示，填完整单词）」） | **严格判分**：归一化后与 `ex.ans` 全等才算对（`/` 分隔的可接受写法任一命中），结果页每题都列「你的答案 / 标准答案」，有答案册解析的一并显示；没填 ans 的数据不许上线 |

#### 真题大作战的题库来自《词汇答案册》

`assets/exercises-答案册.json`（当前 334 题 / 59 个 Day / 81 条解析）是唯一题源，`generate.py` 自动注入成 `DATA.exercises`：

```json
{"d":"Day 1","no":3,"s":"Children believe that the Monkey King is a hero who has many ____ (able).",
 "h":"able","ans":"abilities","note":"空处作 of 的宾语，应用名词……"}
```

- 模板里 `startQuiz(...,'ex')` 一发现 `DATA.exercises` 就改用真题库（`{d,no,s,h,ans,note}`），不再从单词的 `ex` 抽题；按 Day 进入时只取该 Day 的题。
- 结果页与错题本都带「Day N · 第 K 题」和「解析：…」，错题本记录里也存了 `note`。
- 换一本书要重新导答案册时：先 `ocr_pdf.py` 分别 OCR 词册和答案册，再
  `python scripts/import_answers.py --words-ocr <词册OCR目录> --answers-ocr <答案册OCR目录> --out assets/exercises-答案册.json`。
- 词册页码规律：`p004 = Day 1`（`pN → Day N-3`），题目在每页底部「即时小练」；框间距 > 55px 的位置就是原书下划线（填空处）。
- 答案册是两栏流式排版：每段「Day N 即时小练」后面跟 `1.xxx 2.xxx`，部分条目带`【解析】`；解析会换行续接，遇到「第二部分」必须停（那是别的题型，混进来会把题数撑到 540+）。
- **答案册的完整导入套路（分栏读取、按题号配对、提示词↔答案校验、OCR 噪声清洗、显示层的首字母叠字）见 `references/answer-key-import.md`**；配不上的题号不要去猜，宁可丢掉并报数。

#### 离线单词语音包（可选，装了就是"点了就响"）

浏览器自带的英文音色在多数 Windows 上是联网音色（`Microsoft … Online (Natural)`），起麦几百毫秒；要秒响就配一个离线包：

```
60天搞定中考词汇（离线语音版）/
├── 60天搞定中考词汇.html
├── audio/<slug>.mp3      # 1428 词 + 845 短语的美音录音，约 13 MB
├── audio/manifest.json
└── 安装说明.txt
```

- 生成：`python scripts/fetch_audio.py 词表.json audio/ --workers 3`（有道美音 `type=2`，失败回落百度 TTS，然后 ffmpeg 转 22.05kHz 单声道 24kbps；已存在文件自动跳过，可续跑）。
- 文件名规则：`slugOf()` = 小写 + 非字母数字变 `_` + 去首尾下划线，**脚本和模板必须一致**（`ice cream → ice_cream.mp3`）。
- 模板逻辑：`probeLocalAudio()` 开场探测 `audio/<第一个词>.mp3` 是否存在 → `localAudioOK`；`speak()`/`speakNow()` 开头先 `playLocal(text)`，命中就放本地 mp3（0ms），否则退回 `speechSynthesis`。`playLocal` 只处理**单词/短语**（无标点且 ≤48 字符），整句仍走 TTS；听写题会 `preloadLocal()` 预取下题。
- 只发 html 不打包 audio 也能用，自动退回在线语音——所以文案里要提醒"整个文件夹一起发"。

### 3. 学习中心（复习 / 错题本 / 报告 / 排行榜）

顶部四 tab（`openStudy('review'|'wrong'|'report'|'rank')`）：

- **艾宾浩斯抗遗忘复习**：8 个记忆盒，间隔 `0/1/2/4/7/15/30/60` 天，答对升盒、答错回第 0 盒；展示今日到期词、未来计划分组、曲线说明；「开始今日复习」直接出题；**「导出复习计划 PDF」**生成按日期分组（今天/明天/2 天后…）的 A4 表格（勾选框/单词/音标/释义 + 打印按钮）。
- **错题本**：自动收集默写错词 + 真题大作战错题（题干、你的答案、标准答案、日期、音标释义）；「练这些错词」「导出打印版」「清空」。**不再提供 txt 导出**，只出 PDF。
- **学习报告**：今日/累计统计 + 今日分析 + 明日建议 + **每一次练习记录列表**（`progress().sessions`：时间、模式、对/总、正确率、用时）+ 汇总 + 14 天柱状图 + 8 个记忆盒分布。
- **排行榜**：`rankHtml(p)` 遍历 `DB.users` 里所有有成绩（`stats.total>0`）的账号，按「正确率降序 → 时长降序 → 题数降序」排，顶部一块「我的排名 第 N 名」，下面是名次表（前三 🥇🥈🥉、当前用户整行高亮并标「(我)」）。数据只存在本机 localStorage，**没有服务器**；用户问「能不能跨手机排」时要说清这个限制。
- **错题本里的真题条目**：只显示题干/你的答案/标准答案/Day·题号/解析，**不要**再渲染 `w.en + 音标 + 释义` 那一行（讲的是答案词，不是单词），也不给「完整解析」按钮（那个词可能不在词表里）。

### 4. 其它
- **解析卡/词表详情**：音标、词性、释义、🔄 派生/词形变化、🔗 短语搭配、🧩 例句（带 🔊 读例句）、记忆盒状态。
- **多用户（localStorage，每人名字+密码）**：每个用户独立成绩、错题、记忆盒、练习记录、游戏成绩；切换身份只能退出登录后重新输名字+密码（不再提供免密的用户列表）。
- **密码不存明文**：`user.pw = SHA-256('zk|'+密码)`；只加固定盐、不做迭代哈希——这个场景防的是同学随手登别人账号，不是防拖数据库。密码重置没有入口（忘了只能换名字新开档），交付时提醒用户记牢。
- **每日练习**：按 Day 多选范围 → 选 10/20/30/全部 → 开始。

## 手机端硬约束（模板已满足，改前端时不要回退）

1. **禁用 `prompt/alert/confirm`**：微信/QQ 内置浏览器会直接屏蔽。确认框用 `askConfirm(msg, cb)`（`#confirmModal`），提示用 `toast()`。
2. **英文作答必须用网页内置键盘**：输入框 `readonly` + `inputmode="none"`，点按弹 `#vk`（26 字母 + 空格 + ⌫ + ✓确认）。第三方输入法的联想弹窗无法用 HTML 属性关闭，会让学生「被提示」作弊。
   - **坑**：`readonly` 只拦系统键盘聚焦，JS 照样能写值。`vkPress()` 里若写成 `if(inp.readOnly) return`，键盘会整块失效（v1 的 bug）；正确写法是只判断 `inp.disabled`。
3. **中文作答**（英→中）可以用系统输入法：考中文不存在英文联想问题。
4. **自动朗读：空闲绝不 `cancel()`，否则起麦要多等几百毫秒**。Chrome/Edge 里 `speechSynthesis.speak()` 在无用户手势时会静默失败，voices 也可能还没就绪。模板的最终做法（改这里前先读 `speak/speakNow/pickVoice` 三个函数）：
   - 任意首次 `touchstart/click/keydown` → `unlockAudio()`（播一个空串解锁），「开始」按钮点击时再调一次；
   - **两条路径**：`speak()` 给程序自动触发用（进题自动读），`speakNow()` 给**用户点按钮**用。两者都只在 `speechSynthesis.speaking||pending` 时才 `cancel()`——空闲时 `cancel()`→`speak()` 会让引擎重新起麦，凭空多出几百毫秒；
   - **不要写多次 retry**：早期 `speak()` 在 250/700/1400ms 各 cancel+重播一次，等于自己把起麦推到 700ms 以上（用户原话“读音出现得太慢”）。现在只留一次 1.5s 兜底，且条件是「没开口 **且** 引擎确实空闲」，绝不 cancel；
   - `speakNow()` 发现**同一个词正在读就直接 return**，不打断不重启（点按钮时声音本来就在播，重播反而出现空档）；
   - **听写模式在 `startQuiz()` 里就先读第一题**，`renderQ()` 又在 `innerHTML` 之前调 `speakWord()`；`speakWord()` 对同一个词 1.2 秒内去重，避免“预读 + 进题”互相 `cancel()`；
   - **音色决定延迟**：`pickVoice()` 必须优先 `localService`（+10）、压 `Online (Natural)`（−8）和 `Google`（−10）。没装离线英语语音的机器上 `getVoices()` 里 `en-*` 全是 `localService:false`，每次发音都要联网合成，这一趟就是全部延迟——代码无解，只能让用户去「设置 → 时间和语言 → 语音 → 管理语音 → 添加语音 → English (United States)」装一个（装完重启浏览器）。
5. 键盘要适配 `env(safe-area-inset-bottom)`；`body.vkopen #app{padding-bottom:265px}` 防止键盘压住内容。
6. 生成后必须确认：`grep -c 'prompt(\|alert(\|confirm('` 为 0，且 `generate.py` 输出 `JS: OK`。
7. **一题只能判一次**：`submitAnswer()` 里有 `Q.lock` 闸门（新题 `renderQ()` 时复位）。没有它时，连点确认/键盘回车会重复计分并往错题本里塞重复条目。

## 数据来源与质量口径

- **词条/释义/短语/派生词/例句**：来自用户提供的词汇书（OCR）。例句是书里「即时小练」的真题句（挖空 + 括号提示词或首字母）。**有答案册时全部题型都可用**（中文提示、首字母提示都以答案册为准）；没有答案册时只保留英文提示词的题——中文提示题无法确定唯一标准答案，宁可不出题也不要误判。
- **例句必须有中文意思**：学习页每条 `ex` 下面都要显示 `ex.zh`；书里只有英文，这一项只能逐句自己写（176 条约一次坐下写完，按固定顺序批量写回并用 `assert len(exs)==len(ZH)` 卡住错行），配方见 `references/wordlist-schema.md` 的「补全 ex.zh」。
- **音标**：OCR 出来的音标不可用（IPA 符号会被识别成 ASCII 近似值）。音标一律重新生成：优先 `ipa-dict` 的 `en_US.txt`（125k 词，Wikipedia 风格美音，**不带长音符号**），找不到再用 `eng_to_ipa`（CMU 词库）。
  - 下载：`curl -sSL -o en_US_ipa.txt "https://ghproxy.net/https://raw.githubusercontent.com/open-dict-data/ipa-dict/master/data/en_US.txt"`（raw.githubusercontent 在本机被墙，jsDelivr 会超时，ghproxy 可用）
- **朗读**：Web Speech API，`en-US`，rate 0.85；朗读单词/例句按钮已内置。

## 解析一本新词汇书的检查清单

1. `ocr_pdf.py` 跑完，抽查 2~3 页的 `out/ocr/pNNN.json`：中英文识别是否正常（该 PDF 需扫描清晰，200 DPI 合适）
2. 运行 `parse_pdf.py`，看 stats：`entries` 是否接近书里词数；`skipped_pages` 应是封面/目录/第二部分辨析/第三部分构词表
3. 抽查 20 个词条的 `en / ipa / pos / cn / phrases / forms / ex` 是否正确（`--title` 写清书名版本）
4. **查 `ex.ans` 覆盖率**：有独立答案册就优先导答案册（`scripts/import_answers.py`，见 `references/answer-key-import.md`），而不是自己补答案；只有拿不到答案册时才按语法补（见「已知坑」的答案册条目）。自己补的答案必须告知用户请他对照核对。严格判分没有 ans 就等于没答案。
5. 生成 HTML，手机宽度（390px）打开跑一遍：**登录（新名字设密码 / 错密码被拦 / 退出登录）** → 首页 → 单词流星雨三个游戏 → 翻译官/听写/大作战 → 结果页的「下一轮」按钮 + 「重练本轮错题」（三种模式都要按原题型重做）→ 学习中心四 tab → 导出文件。自动化回归用 `scripts/cdp_verify.js` 跑 `steps.json`（Edge headless + CDP，零依赖），断言清单见 `references/qa-cdp-checks.md`（键盘写入、答题期零泄露、朗读被调用、三个游戏能自动通关、登录与排行榜、导出内容）；导出排版配方见 `references/print-export.md`
6. **改名/合并入口后要 grep 旧文案**：把**所有用过的旧名**都列进去，`grep -o '听音默写\|例句填空\|词汇表\|今日复习\|单词大作战\|5·3' 生成的.html` 必须为空；同时 `grep -rn 旧名` 扫一遍 skill 自己的 SKILL.md / references / scripts（模板改了但文档没改很常见）。改完再跑一次，确认 0 命中。
7. 数据落盘建议：`workspace/zhongkao-vocab/` 下放 `wordlist-*.json`、`data/en_US_ipa.txt`、`build.sh`，方便换书重跑

## 已知坑（都踩过）

- **连连看：配对不用寻路，但连线必须绕行**。玩法是点两张配对卡即消，不需要 BFS 判断能否连通，不要加回 `bfsPath/isFree/linkHint`；但线本身要走卡片缝隙（`drawRoute()`）。早期用 `drawPath([a,b])` 两点直连会横穿中间卡片的文字，被用户否掉过。
- **游戏必须先学后玩**：`startGame()` 开头 `if(!canPlay())return`；`canPlay()` 判定 `progress().learned[day]`，否则弹提示并 `openLearn(day)`。忘了这层，卡片虽然显示 🔒 仍能被脚本/误触直接进游戏。
- **学习进度要落盘**：`learnSeen[day]` 记录看过的下标（进页即记），`learned[day]` 在「学完了」时写入日期；只存在内存里的话，刷新一次游戏又锁上了。
- **模板字符串里别在单引号串中写 `${...}`**：`'…（${rec.plays} 次）'` 会原样输出。卡片的「最好成绩（N 次）」、HUD 的「剩余 X 张」都因此返工过。
- **游戏 HUD 要手动刷新**：消消乐/连连看的「剩余张数」是 `#gameTitle` 的静态文本，消除后必须在 `matchTap()` / `linkTap()` 里改；对对碰的「已配对」在 `#gameStat`。
- **别留重复的函数定义**：模板里同名函数后定义会覆盖前面的。改 `startWithName()` 时旧的（无密码版）没删，导致密码框完全失效、任何名字直接进——用 `grep -n "function 名字"` 确认只有一处。
- **答案册的三个坑**：① 解析里「第二部分」之后是别的题型，必须停，否则题数会把最后一天撑到 76/128；② Day 52 的题号印重了（5. 6. 各出现两次），只能按句子语义人工校正（已写进 `import_answers.py` 的 `DAY_FIX`）；③ 扫描版 OCR 会把「I」认成「1」、把「habit」认成「hhabit」，答案册里的首字母提示拼到句子里会出现「NNothing」——显示答案时要连首字母一起吞掉（正则 `([A-Za-z])?_{2,}`）。
- **严格判分依赖 `ex.ans`**：`judge()` 对真题大作战要求与 `ex.ans` 完全一致。若某批数据没填 ans（例如书里答案在独立答案册），只能退回"该词任意正确词形"，学生随便填个变形就算对——所以**生成词表时务必补齐 ans**；`/` 用来写可接受写法（`organization/organisation`）。
- **名字门槛**：`boot()` 无条件走欢迎页（旧的 `CUR().named` 判断已去掉，否则刷新会直接进上次的用户）；`ensureUser()` 在未登录时仍可能造 `named:false` 的占位用户，`startWithName()` 登录成功后要把这类没成绩的占位账号清掉，否则排行榜/数据里会多一个"同学"。
- **欢迎页要连顶部栏一起藏**：`renderWelcome()` 里把 `.topbar` 设为 `display:none`，而且必须在 `go('welcome')` **之后**设——`go()` 末尾会调 `renderTop()` 把它设回 `flex`，顺序反了就白做（欢迎页上不该出现「同学 / 首页」）。
- **连线画在缝隙里**：`drawRoute()` 用 `gridGeom()` 实测卡片尺寸和 8px gap，横段走 `r*stepY-gap/2`、竖段走 `c*stepX+w+gap/2`；第 0 行走下方，其余走上方。直接连两点会横穿中间卡片的文字，用户明确否掉过。
- **扫描版 PDF 没有文本层**：`get_text()` 返回空。只能 OCR；OCR 约 7-8 秒/页。
- **pip 装 rapidocr 必须 `--no-deps`**：带依赖会尝试升级 onnxruntime，在长路径上报 `OSError: ...DeprecatedNodeIndexAndKernelDefHash.py`。装法：
  ```bash
  "$PY" -m pip install --no-deps -i https://pypi.tuna.tsinghua.edu.cn/simple \
      pymupdf rapidocr-onnxruntime opencv-python pyclipper Shapely PyYAML eng-to-ipa
  ```
- **词表页是双栏**：同一 y 的两个识别框可能是左右两栏的不同词条，也可能是同一条目的「英文 + 中文」，必须按 x 分栏后再按 y 聚行（`band_lines()`）。
- **释义分隔符**：OCR 把「，、;；」混着出，且多词性之间可能没有分隔符（`n.速度 v.超速行驶`）。做法：先把 ASCII 标点转全角，再把词性标记替换成 `；`，最后按 `；` 去重。
- **页眉识别不稳**：`Day 53` 可能被切成 `Day` + `53`。用「有 Day 关键词但没数字 → 按上一页 +1 顺延」兜底，再用「词条数 < 8 视为非词表页」过滤掉辨析页/构词表。
- **答案册常不在同一 PDF**：书里只写「答案见《答案册》P67」。这时不要让 `ans` 空着上线——按句子语法逐题补（170+ 条用一段脚本按顺序批量写回，不要手改 JSON），补完抽查 `many ____ → abilities`、`be ____ not to → careful` 这类**词形题**（最易补错），并把补的答案告知用户请他对照答案册核对；个别写法差异用 `/` 追加可接受答案。严格判分完全依赖这一步。
