# 江苏家训数据库（GitHub Pages 公开版）

这是面向历史文化与人文学科研究的静态公开检索网站。构建脚本从本地 SQLite 读取资料，生成经过检查的 UTF-8 JSON；发布后浏览器只使用 HTML、CSS、JavaScript 和静态 JSON，不需要 Python 服务器。

## 数据范围

当前公开版包含正式记录 9 条（A 级 4、B 级 3、C 级 2）、原文单元 27、人物 17、家族 5、地点 14、来源 11、主题 22、D 级待查线索 5。D 级线索不进入正式记录、原文或主题频次统计。C 级记录没有核验原文时明确显示“元数据已核，原文待补”。

## 技术结构

- `scripts/export_static_data.py`：以只读方式读取本地 SQLite，导出稳定排序的公开 JSON。
- `scripts/validate_data.py`：检查数量、JSON、C/D 规则与本地路径泄露。
- `scripts/build.py`：将 `src/` 与 `public/` 合并为发布目录 `dist/`。
- `src/`：静态页面、样式和浏览器端检索逻辑。
- `public/data/`：允许提交和公开发布的生成数据；不含 SQLite。
- `.github/workflows/deploy-pages.yml`：测试、构建和 GitHub Pages 部署。

所有资源与页面链接均使用相对路径，支持 `https://USERNAME.github.io/REPOSITORY/` 形式的项目子路径。详情链接使用 `record.html?id=JX-SB-001`，直接刷新不会依赖服务器路由。

## 本地预览

```bash
cd jiangsu-jiaxun-pages
python3 -m http.server 4173 --directory dist
```

打开 `http://127.0.0.1:4173/`。要模拟 GitHub Pages 子路径，可在上级目录运行服务器，再访问 `http://127.0.0.1:4173/jiangsu-jiaxun-pages/dist/`。

## 更新数据与生成 JSON

原始 SQLite 永远保留在本地且不得提交。更新本地数据库后运行：

```bash
python3 scripts/export_static_data.py --database "../local-data/jiangsu_jiaxun.sqlite"
python3 scripts/validate_data.py
python3 scripts/build.py
```

随后检查 `public/data/*.json` 的 Git 差异，确认没有隐私数据、本地路径或不应公开的材料，再提交更新。脚本不会修改 SQLite；空值导出为 `null`，中文不转义，ID及关系保留，URL仅接受有效的 HTTP/HTTPS 地址。

## 自动测试

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

测试覆盖数量、JSON有效性、主键唯一性、关系完整性、读书检索、地域与等级筛选数据、C/D规则、危险HTML防护、相对资源路径和发布目录安全。

## 创建仓库并推送

```bash
git init
git branch -M main
git status --short
git check-ignore -v example.sqlite example.xlsx .env
git add .github src public/data scripts tests .gitignore .nojekyll requirements.txt README.md LICENSE
git diff --cached --name-only
git commit -m "发布江苏家训数据库静态检索网站"
git remote add origin git@github.com:USERNAME/jiangsu-jiaxun-database.git
git push -u origin main
```

不要未经检查直接执行 `git add .`。提交前确认清单中没有 SQLite、Excel、ZIP、密码、密钥和本地绝对路径。

## 开启 GitHub Pages

在仓库的 **Settings → Pages → Build and deployment** 中，将 Source 选择为 **GitHub Actions**。推送到 `main` 后，在 **Actions** 页查看“部署江苏家训数据库”工作流。成功后网址通常为：

`https://USERNAME.github.io/jiangsu-jiaxun-database/`

工作流把测试与构建、部署拆成依赖任务，只上传 `dist/`，并输出实际 Pages 地址。

## 自定义域名与 HTTPS

在仓库 **Settings → Pages** 填写 Custom domain，根据 GitHub 提示在 DNS 服务商配置记录，等待验证后启用 **Enforce HTTPS**。未提供域名前，本项目不会虚构域名或创建 `CNAME`。

## 静态版限制

**GitHub Pages版本是公开只读数据库。它不支持在线后台编辑。数据更新需要先更新本地数据库，重新生成静态JSON，再提交到GitHub。**

静态版也不提供服务器端权限控制、在线数据库写入或动态 API。当前数据量适合浏览器端包含搜索；数据显著扩大后，应考虑预生成分片索引或使用专门的检索服务。
