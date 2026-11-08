# NOTICE ｜ 数据来源与许可说明

本项目（60天搞定中考词汇 ｜ 中考词汇训练网页生成器）由 **Elaine-Wu Yi** 维护。

## 1. 代码

`scripts/`、`assets/coach-template.html`、`SKILL.md`、`README.md`、`references/` 下的全部内容
均为本项目自有作品，以 [MIT License](LICENSE) 发布，© 2026 Elaine-Wu Yi。

## 2. 真题库 `assets/exercises-答案册.json`

- 内容：334 道句子填空真题的**题干、标准答案、解析要点**（含 Day 编号与题号）。
- 来源：作者自有的纸质《词汇答案册》，经扫描 OCR 后人工逐题校对；题干与教材/词册中的练习同步。
- 用途：仅供本项目生成学习页面时判分与展示解析使用。
- 说明：不包含任何教材或答案册的原书扫描图、完整页面；如相关权利人认为这部分整理内容使用不当，
  请在 Issue 中告知，作者会立即移除。

## 3. 词表数据

仓库**不包含**完整词表（1428 词的 `wordlist.json`）。词表由使用者从自己合法获得的纸质书 / PDF
通过 `scripts/ocr_pdf.py` + `scripts/parse_pdf.py` 提取。仓库内只提供 2 天的示例数据
`assets/sample-wordlist.json` 供跑通流程。

## 4. 离线语音包 `audio/`

- 不随仓库分发，由 `scripts/fetch_audio.py` 在本地按需生成。
- 生成时调用公开词典发音接口：
  - 主用：有道词典发音 `https://dict.youdao.com/dictvoice?audio=<word>&type=2`（美音）
  - 备用：百度语音合成 `https://fanyi.baidu.com/gettts?lan=en&text=<word>&spd=3&source=web`
- 生成的音频仅用于**个人学习与课堂教学**，不得再分发、打包出售或用于商业产品；
  音频权利归各接口提供方所有。
- 如需完全自主可控的发音，请改用本地 TTS（例如安装 Windows 离线英语语音包，或用
  `edge-tts` / Piper 等工具自行合成后按 `audio/<slug>.mp3` 命名覆盖）。

## 5. 运行时依赖

- OCR：PyMuPDF、RapidOCR（onnxruntime）、OpenCV、Shapely、pyclipper、PyYAML
- 音频转码：imageio-ffmpeg（内置 ffmpeg 二进制）
- 以上均为独立第三方项目，遵循各自的许可证；本项目仅调用，不修改、不再分发其源码。
