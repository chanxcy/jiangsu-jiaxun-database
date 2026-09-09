# 江苏家训数据库（GitHub Pages 公开版）

这是面向历史文化与人文学科研究的静态公开检索网站。构建脚本从本地 SQLite 读取资料，生成经过检查的 UTF-8 JSON；发布后浏览器只使用 HTML、CSS、JavaScript 和静态 JSON，不需要 Python 服务器。

## 数据范围

当前公开版包含正式记录 36 条（A 级 4、B 级 27、C 级 5）、原文单元 46、人物 29、家族 21、地点 41、来源 33、主题 22、D 级待查线索 9。D 级线索不进入正式记录、原文或主题频次统计。没有已核 `text_units` 的记录依数据库状态显示“原文待复核”或“原文待补”，不从整理备注生成原文。

## 技术结构

- `scripts/export_static_data.py`：以只读方式读取本地 SQLite，导出稳定排序的公开 JSON。
- `scripts/validate_data.py`：检查数量、JSON、C/D 规则与本地路径泄露。
- `scripts/build.py`：将 `src/` 与 `public/` 合并为发布目录 `dist/`。
- `src/`：静态页面、样式和浏览器端检索逻辑。
- `public/data/`：允许提交和公开发布的生成数据；不含 SQLite。
- `.github/workflows/deploy-pages.yml`：测试、构建和 GitHub Pages 部署。

所有资源与页面链接均使用相对路径，支持 `https://USERNAME.github.io/REPOSITORY/` 形式的项目子路径。详情链接使用 `record.html?id=JX-SB-001`，直接刷新不会依赖服务器路由。

## 江苏家训地图

`map.html` 是独立的静态地图页。它使用本地 SVG 渲染江苏十三个设区市边界、市名和家训地点，无需地图服务密钥，也不请求第三方瓦片；即使地图加载失败，可访问地点列表仍可使用。

- `public/data/place_coordinates.json` 是唯一的地点坐标数据源，通过 `place_id` 与业务数据关联。原有地点保留已核结果；新增且尚无可复核坐标的地点明确标为“位置待核”，不生成地图点。
- 全站发布坐标与边界统一使用 WGS84。高德地图核定的 GCJ-02 原始点位保留在 `source_coordinate`，发布值由公开逆转算法近似转换；此转换不提高证据精度。
- `public/data/jiangsu_boundary.geojson` 以十三个设区市的 [OpenStreetMap 行政边界关系](https://www.openstreetmap.org/copyright)为内部市界来源，通过 [Nominatim](https://nominatim.openstreetmap.org/) 按“城市名，江苏省，中国”精确检索。为排除行政关系中的近海管辖范围，各市几何又与 [Natural Earth Admin 1 – States, Provinces（1:50m）](https://www.naturalearthdata.com/downloads/50m-cultural-vectors/50m-admin-1-states-provinces/) 的江苏省陆地轮廓取交集，未移动任何家训点位。OpenStreetMap 数据遵循 ODbL 1.0；Natural Earth 数据为公有领域。全部边界和点位统一为 WGS84，获取和核验日期为 2026-09-07。文件保留每个边界的 OSM relation ID、双方来源与处理方法；地图仅供文化数据库概览，不用于法定界线或测绘。
- 十三市按固定分组着色：苏南为南京、无锡、常州、苏州、镇江；苏中为南通、扬州、泰州；苏北为徐州、连云港、淮安、盐城、宿迁。
- 地图未引入第三方 JavaScript 库：当前数量与交互使用原生 SVG/DOM 更小、更容易审计，且避免 CDN 与外部瓦片的可用性和许可问题。家训点按投影后的屏幕距离分组，阈值为 26 像素；点组只合并交互，不更改、偏移或伪造坐标。

坐标核验与业务 JSON 导出分离：导出脚本以只读方式访问 SQLite，不回写原库，也不在 `places.json` 中制造第二份坐标。重新导出时会保留已核坐标，并为新地点生成无经纬度的“待核”状态。公开 JSON 不包含整理员 `entry_note`、线索内部 `note` 或本地文件路径。

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

测试覆盖数量、JSON有效性、主键唯一性、关系完整性、读书检索、地域与等级筛选数据、C/D规则、危险HTML防护、相对资源路径和发布目录安全。地图测试另外检查 41 个地点状态、WGS84 坐标范围、核验溯源、多关系保留、原文摘录规则、键盘/触摸交互、降级列表、子路径资源与私密信息扫描。

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
