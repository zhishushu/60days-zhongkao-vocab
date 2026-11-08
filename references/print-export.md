# 把学习数据导出成「可打印 A4 / 另存 PDF」

训练器的三个导出口（错题本、艾宾浩斯复习计划、学习报告）走同一条路子：**前端拼一段完整 HTML → Blob 下载 → 用户点「打印 / 存为 PDF」**。不用后端、不装库，微信里也能落地成文件。

## 骨架

```js
function download(text, filename, mime){
  // 带 BOM：从 file:// 打开时中文才不会按 GBK 解成乱码
  const blob = new Blob(['\ufeff' + text], { type: (mime||'text/plain') + ';charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;               // 文件名带日期：错题本-2026-11-08.html
  document.body.appendChild(a); a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1500);
}
```

导出页里放一个常驻按钮（打印时隐藏）：

```html
<div class="bar"><button onclick="window.print()">打印 / 存为 PDF</button></div>
<style>
 body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;color:#3f2b36;margin:26px}
 table{width:100%;border-collapse:collapse;font-size:12.5px}
 th,td{border:1px solid #f3d3e0;padding:6px 8px;text-align:left}
 th{background:#fff0f6;color:#b03a68}
 .bar{position:fixed;right:18px;top:18px}
 @media print{
   .bar{display:none}
   body{margin:10mm}
   th{background:#fff0f6 !important;-webkit-print-color-adjust:exact}  /* 不写这句表头底色会被浏览器吃掉 */
 }
</style>
```

## 版式规则（都是返工过的）

- **指标表不要一行铺满**：11 个指标塞进一行 `<td>` 时，每个表头都被压成竖排单字（「今日题数」竖着写）。改成两对一行：`<tr><td>项目</td><td>数值</td><td>项目</td><td>数值</td></tr>`，表头写「项目/数值/项目/数值」。
- **分组用整行色带**：复习计划按日期分组，`<tr class="g"><td colspan="5">明天（2026-11-09） · 12 词</td></tr>`，比每行重复日期清楚。
- **背诵清单留勾选框**：第一列放 `☐`（居中、字号 15px），学生打印后可手写打勾。
- **列宽要钉**：`td.w{color:#dc2626;white-space:nowrap}` 钉住「我的答案/正确答案」，长题干列给 `max-width:300px` 让它换行，否则窄列被挤爆。
- **一行别超过 7 列**；超过就拆表，或把「单词/音标/释义」合并成一列三行。
- 表格末尾给一句打印建议：「A4 纵向；电脑上 Ctrl+P 可直接另存为 PDF。」

## 交付前怎么验

1. 用 `scripts/cdp_verify.js` 的 `download` 步骤把导出 HTML 抓下来落盘（内部把 `window.download` 换成捕获器），断言字符数 > 1000。
2. 用 Edge headless 单独打开这份 HTML，`--window-size=900,1200` 截一张 PNG，肉眼看：表头没有竖排字、没有溢出、打印按钮在右上角。
3. 导出的样例 HTML 和截图一起放进 `预览/` 交给用户，比口头描述可信。
