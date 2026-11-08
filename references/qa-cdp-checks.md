# 单文件 HTML 词汇训练器的自动回归（Edge headless + CDP）

成品没有构建系统也没有测试框架，全部交互都在一个 HTML 里。肉眼看截图抓不到「键盘不写入」「答案提前泄露」「朗读没触发」「连连看连不上」这类缺陷——必须用脚本把每条交互点一遍再交付。

## 准备

- `node`（v22 自带全局 `WebSocket` 和 `fetch`，不需要 puppeteer）；Edge：`C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe`
- **每轮跑之前删掉 `--user-data-dir` 目录**。localStorage 跨轮保留，「本轮应该有 1 条练习记录」这类断言会被上一次运行污染。
- 视口用 `Emulation.setDeviceMetricsOverride {width:390,height:844,deviceScaleFactor:2,mobile:true}`。**不要用 `--window-size` 判断布局**：实测它给到的 `innerWidth` 是 518，不是 390，截图会被裁成半张，容易误判成「溢出/被裁切」。

## 骨架

```js
const child = spawn(EDGE, ['--headless=new','--disable-gpu',`--remote-debugging-port=${PORT}`,
  `--user-data-dir=${PROFILE}`,'about:blank'], {stdio:'ignore'});
// 轮询 http://127.0.0.1:PORT/json/list → 取 type==='page' 的 webSocketDebuggerUrl
// send('Runtime.enable'|'Log.enable'|'Page.enable'
//      |'Emulation.setDeviceMetricsOverride'|'Page.navigate',{url:'file:///'+路径.replace(/\\/g,'/')})
const ev = async expr => (await send('Runtime.evaluate',{expression:expr,returnByValue:true,awaitPromise:true}))
  .result?.result?.value;
// 同时收集 Runtime.exceptionThrown 与 Log.entryAdded(level==='error')，最后断言 errors 为空
```

截图用 `Page.captureScreenshot`（`captureBeyondViewport:false`），不要用命令行 `--screenshot`。

**截图要等一帧以上**：`Runtime.evaluate` 改完 class/style 后紧接着 `captureScreenshot`，拍到的常是**上一帧**——刚被 `visibility:hidden` 的卡片还在图里，看起来像「修复没生效」。断言用 `getComputedStyle()`，交付截图在 `await sleep(400)` 之后再拍。

## 必须断言的清单（每条都对应一次真实返工）

1. **键盘真的写进输入框**：`[...document.querySelectorAll('#vk .vkkey')].find(k=>k.textContent==='A').click()` 点两次 → `#ans.value==='aa'`，再点 `⌫` → `'a'`。只断言「键盘可见」抓不到 `readOnly` 误判导致的整块失灵。
2. **答题期零泄露**：`document.querySelector('#quiz .explain')` 为 null，且 `#fb` 文本不含「正确答案」；页面上不存在「看答案」按钮。
3. **朗读被触发，两条路径分别测**：`speak` 是程序自动读（进题），`speakNow` 才是按钮。两个都劫持：`window.__spoken=[]; for (const fn of ['speak','speakNow']) { const os=window[fn]; window[fn]=(t,o)=>{__spoken.push(t); return os(t,o)} }`。断言：①渲染听写题后 `__spoken` 里有当前单词（进入即读，不用点按钮）；②点「🔈 听发音」后再多一条同一个词。只劫持 `speak` 时按钮一路走 `speakNow`，会误判成「按钮没发音」。
4. **三个游戏能自动通关**（操作走页面自己的函数 `click()/matchTap()/linkTap()`，不要在 Node 里重写消除规则；但「哪两张应该配」必须自己算，见下）：
   - 消消乐：按 `data-pair` 分组，每组两张依次 `click()` → 断言 `game.left===0` 且出现「过关」
   - 对对碰：循环找同 `data-pair` 的两张未消除卡 `click()`，直到 `game.matched===game.pairs`
   - 连连看：**配对必须用独立判据找，而且必须带反例**。先用页面数据反查：`dayWords(hubDay)` 里每个词的 `en` 与 `cn.split('；')[0]` 就是一对，按渲染出来的卡片文本定位两张卡再 `linkTap()`；不要用 `t.pair===t2.pair` 去找「配对」——那正是被测代码的判据，判据坏掉时（卡片对象存 `{i:...}` 而 `linkTap` 比 `.pair`，两边都是 `undefined`）测试会跟着一起「通过」。然后补反例：**挑两张 `pair` 不同、或同为 EN 的卡点下去，断言 `game.left` 不变、两张卡都还在、`game.errors` +1**。最后循环到 `game.left===0`。**不要调用路径搜索**——`bfsPath/isFree/linkHint` 已删除，调用会直接 ReferenceError。
5. **导出内容**：把 `window.download` 换成捕获函数 `window.download=(t,f)=>{window.__dl={len:t.length,f,head:t.slice(0,90)}}`，调 `exportWrong(true)` / `exportReview()`，断言长度 > 1000、文件名含日期；要检查排版就把捕获的 HTML 写盘，再用 Edge 单独打开截一张图。
6. **改名轮次 grep 旧文案**：`grep -o '听音默写\|例句填空\|词汇表\|今日复习\|单词大作战' 生成的.html` 必须为空（**把所有历史上出现过的名字都列进去**，改名往往不止一轮）。写死的字符串（按钮、卡片、HUD、`<title>`）最容易漏改，改完再扫一遍 skill 自己的 SKILL.md / references / scripts。
7. **名字+密码门槛**：干净 profile 下 `$('.screen.active').id==='welcome'`、`#wName` 与 `#wPwd`（`type==='password'`）都存在、`.topbar` 隐藏。三连断言：①密码 2 位 → 停在 welcome 且 `#wTip` 含「至少 4 位」；②新名字 + 合法密码 → 进 home、`CUR().pw` 是 64 位散列（说明走的是 SHA-256 不是明文）；③`logout()` 后再用同一名字 + 错密码 → 仍停在 welcome 且提示「密码不对」，换对密码才进。只断言「有输入框」等于没测。
   注意 `startWithName()` 是 `async`（要 `await hashPwd`），探针里必须 `await ev(...)` 之后再 sleep ~500ms 才能断言页面状态。
8. **学习页例句**：`openLearn(day)` 后取 `dayWords(day).findIndex(w=>w.ex&&w.ex.length)` 跳到有例句的词，断言 `.exitem` 数量 === `w.ex.length`（不是固定 2 条）、句子文本里已嵌好答案、**每条例句下面有一行中文**，且**不含**「填：」「点句子可朗读」这类说明字眼；「🔗 短语搭配」区块里的每个 chip 都必须含本词（`includes(w.en.toLowerCase())`），不含就整块不出现。再劫持 `speak` 与 `speakNow`（学习页的点击走 `speakNow`），点 `.exitem` 与 `.wen`，断言分别收到整句和单词。
9. **连连看连线不压字**：点一对后 ~100ms 内抓 `#linkSvg polyline` 的 `points`，把每条**水平段**的 y 加上网格 `getBoundingClientRect().top` 换算成视口坐标，与所有 `#lgrid .tile` 的矩形比对，任一段落在卡片内 → `overlap>0` 即失败（还应断言 `points.length>=4`，说明是折线不是直连）。折线 220ms 后就会移除（和卡片同一帧开始消失），点完必须立刻抓，晚了就是 `noPolyline`。
10. **严格判分闭环**：`startQuiz(allWords(),2,'ex')` 后先填 `zzz`，断言 `Q.log.at(-1).ok===false` 且 `correct===q.ex.ans`；再填 `q.ex.ans.split('/')[0]`，断言 `ok===true`；答满两题后 `#result .qa .ans` 同时含「你的答案」与「标准答案」。
11. **下一轮入口**：翻译/听写/真题各答满一轮后，`[...document.querySelectorAll('#result .btn')].map(b=>b.textContent.trim())` 必须含对应的「进入下一轮翻译 / 听写 / 作战」（且只出现一次），点它之后断言 `$('.screen.active').id==='quiz'`、`Q.mode` 不变、`Q.idx===0`。只断言「有回首页按钮」抓不到这个需求。
12. **排行榜**：先手工注入第二个账号（`blankUser('李雷')` + `stats={days:{...},total,right}`）再 `openStudy('rank')`，断言 tab 高亮、`我的排名 第 N 名` 与表格行数 === 有成绩账号数、排序满足「正确率降序→时长降序」、当前用户那行标 `(我)`。只造一个账号时排行榜看起来「正常」，排序 bug 完全看不出来。
13. **界面不带说明句**：`$('#welcome').innerText` 不含「孩子」、「$('#quiz').innerText` 不含「不给中文提示」「先点喇叭」，首页卡片不含题数与「答案册」字样；干净 profile 下还要断言 `.topbar` 的 `display==='none'`（欢迎页不该出现「同学 / 首页」）。
14. **消失是同一帧**：配对后立刻（同一个 `evaluate` 里）读 `getComputedStyle(tile).visibility` 必须是 `hidden`；仍是 `visible` 说明 `.tile.gone` 没写 `transition:none`，卡片会多留 ~120ms（截图看起来像没消）。再断言 `#lgrid .tile` 中 `visibility!=='hidden'` 的数量 === `game.left`。
15. **发音延迟用调用计数测，别等 `onstart`**：headless 里 `en-*` 音色常全是 `localService:false`（联网合成），`onstart` 可能一直不触发，等它必然超时。改成劫持 `speechSynthesis.speak/cancel` 计数：空闲时点「听发音」→ `speak` 恰好 +1、`cancel` 为 0、且这次 `speak` 发生在点击的同一个同步栈里；再等 1.2s，断言 `cancel` 仍为 0（说明没有 retry 抢麦）。`cancel>0` 就是「慢」的复现。再补一条**播放中**的用例：正在读这个词时再点「听发音」，断言 `speak` 与 `cancel` 都不增加（`speakNow()` 对同一个词直接 return，不重启，否则重播会出现空档）。

16. **「重练本轮错题」必须三种模式各测一遍**：翻译/听写/真题各答满一轮（全答 `zzz`）→ 点「重练本轮错题（N）」→ 断言 `Q.qs.length===N`、`Q.mode` 与原轮一致，且**题型没被改写**：听写轮 `Q.qs[0].type==='dict'` 且卡片里有「🔈 听发音」；翻译轮题型仍是 `cn2en/en2cn`；真题轮 `Q.qs.map(q=>q.ex.s)` 与结果页错题列表的 `ex.s` **逐条相等**（`sameSentences`）。旧实现对所有模式都调 `startQuiz(...,'trans')`，听写错题会变成没喇叭的互译题、真题错题变成随机句子，只断言「有重练按钮」或「进了答题页」完全抓不到。

## 交互是异步的：刷一轮题必须逐题 await

`submitAnswer()` 只做判定，**480ms 后**才 `nextQ()`。所以在一次 `Runtime.evaluate` 里写 `while(Q.idx<Q.qs.length){$('#ans').value=..;submitAnswer()}` 只会提交第一题，剩下的被 `Q.lock`/未换题吞掉——现象是「答完了却停在答题页、`#result` 里 0 个 `.qa`」，很容易误判成结果页坏了。正确做法：

```js
for (let i = 0; i < n; i++) {
  await ev(`(() => { const q=Q.qs[Q.idx]; if(!q) return 'done';
    $('#ans').value=${JSON.stringify(val)}; submitAnswer(); })()`);
  await sleep(800);            // 必须 > 480ms 的换题延迟
}
```

同一条也适用于 `linkTap()`/`matchTap()` 之后的 HUD 断言、`speak()` 的触发断言。

## 判断依据必须独立于被测实现（最贵的一条）

测试里找「应该配上的一对」时，**绝不能用页面代码自己用的那个判据**（例如 `t.pair===t2.pair` 找配对卡、用 `correctOf(q)` 算期望答案、用 `rankHtml` 的排序函数验排名）。判据本身坏掉时，代码和测试同时成立，测试会高高兴兴地给你一个绿灯——连连看曾经因为卡片对象存 `{i:...}` 而判分比 `.pair`（两边 `undefined`），任意两张卡都能消，而自动化测试用同一个 `.pair` 找配对，跑了几轮都「通过」。

做法：从**数据源 + 用户视角**另算一遍——配对从 `dayWords()` 的 `en` / `cn` 反查，标准答案取 `q.ex.ans` 原文，排行从注入的 `stats` 自己算期望顺序；并且**同时断言反例**（不配对的不能消、错的答案要判错、低正确率不能排前面）。正向用例只证明「能过」，反例才证明「不是一律都过」。

## 探针自己出错时，别让它看起来像应用 bug

- 页面表达式里引用了 Node 侧的变量（`${i}` 之类拼错、循环变量没传进去）会让整个 IIFE 抛 ReferenceError，`submitAnswer()` 根本没执行，而 `ev()` 若只取 `.result?.result?.value` 就拿到 `undefined`。**`ev()` 必须把 `exceptionDetails` 显式返回**（`return {__err: ...}`），断言前先看有没有 `__err`。
- 想拍到某个特定状态（例如「结果页带解析」），不要去跑十几轮碰运气：直接把 `Q.qs` 换成挑好的题目数组（`DATA.exercises.filter(e=>e.note).slice(0,3).map(...)`），`Q.idx=0;Q.log=[];renderQ()`，再正常答题。测试专用状态注入比随机抽样可靠得多。

## 判读

全部断言通过 + `errors` 为空 + `generate.py` 输出 `JS: OK` + `grep -c 'prompt(\|alert(\|confirm('` 为 0，才算可以交付。少于这个强度，用户下一轮就会点出 bug。
