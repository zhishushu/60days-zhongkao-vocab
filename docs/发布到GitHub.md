# 发布到 GitHub（3 分钟）

这个目录**已经是初始化好的 git 仓库**，`main` 分支上有一个提交，作者是 `Elaine-Wu Yi`。
直接推到你的 GitHub 仓库即可。

## 1. 在 GitHub 上建仓库

- 仓库名建议：`60days-zhongkao-vocab`
- 描述（About）建议：
  `把一本中考词汇书变成手机可用的单文件 HTML 词汇训练器：先学后玩的三款游戏、听写、真题、艾宾浩斯复习、错题本、排行榜`
- 可见性：Public
- **不要**勾选 Add a README / .gitignore / license（本地已经有了）
- Topics 建议：`education` `vocabulary` `english-learning` `zhongkao` `single-file-html` `ocr` `ai-skill`

## 2. 推送

```bash
cd 60days-zhongkao-vocab        # 本目录
git remote add origin https://github.com/<你的用户名>/60days-zhongkao-vocab.git
git push -u origin main
```

如果仓库已经建好且带了一个初始提交，先合并再推：

```bash
git pull --rebase origin main
git push -u origin main
```

## 3. 打一个 Release（可选，推荐）

仓库里没有语音包（11 MB，用脚本本地生成），适合放在 Release 附件里：

```bash
git tag -a v1.7.0 -m "v1.7.0 首个公开版本"
git push origin v1.7.0
```

在 GitHub → Releases → Draft a new release：
- Tag 选 `v1.7.0`
- 标题：`v1.7.0 · 首个公开版本`
- 附件：把桌面上 `60天搞定中考词汇-离线语音版.zip` 拖进去（学生下载解压即用）

## 4. 之后要改内容

```bash
# 改完词表/模板后重新生成示例
python3 scripts/generate.py assets/sample-wordlist.json demo/示例-2天.html

git add -A
git commit -m "docs: 更新示例"
git push
```

## 检查清单（发布前）

- [ ] `README.md` 顶部的作者名是 **Elaine-Wu Yi**
- [ ] `LICENSE` 里 copyright 是 **2026 Elaine-Wu Yi**
- [ ] 没有把教材 PDF、完整 `wordlist.json`、`audio/` 提交上去（`.gitignore` 已排除）
- [ ] `demo/示例-2天.html` 能双击打开、能登录、能做题
