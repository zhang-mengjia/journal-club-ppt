# 逐页计划与构建

计划是 UTF-8 JSON。`paper` 保存论文标识，`main_figures` 保存正文主图的 panel 清单，`slides` 保存实际页序。路径相对 JSON 文件所在目录解析。

每页的 `notes` 是正式中文讲稿。`evidence`、图片的 `source` 和 `panels` 供工作记录与覆盖检查使用，构建器只把显示字段和讲稿写入 PPT。

```json
{
  "paper": {"title": "Article title", "citation": "Author et al., Journal (year)", "doi": "10.xxxx/example"},
  "main_figures": {"1": ["a", "b", "c"], "2": ["a", "b"]},
  "slides": [
    {"type": "cover", "title": "Article title", "byline": ["Author et al.", "Journal (year)", "Journal Club"], "notes": "今天汇报的研究关注……"},
    {
      "type": "content", "header": "Results", "subtitle": "Original result heading",
      "images": [{"path": "panels/fig1_ab.png", "box": [170, 245, 760, 300], "alt": "Task and experiment", "source": "Fig. 1a,b", "panels": ["1a", "1b"]}],
      "notes": "研究者首先检验……", "evidence": ["Fig. 1a,b"]
    },
    {
      "type": "summary", "subtitle": "Original research topic",
      "items": [{"text": "Main result", "level": 0}, {"text": "Current conclusion", "level": 1, "color": "#0000FF"}],
      "notes": "这一部分说明……"
    },
    {"type": "thanks", "title": "Thanks!", "notes": "我的汇报结束，谢谢大家。"}
  ]
}
```

## 支持字段

- `type` 可为 `cover`、`content`、`summary`、`thanks`。背景、作者、问题、方法和图页均使用 `content`。
- `header` 是黑色标题栏文字。`subtitle` 是其下的小标题。
- `images[].box` 为 `[x,y,width,height]`。构建器以 contain 保持宽高比，图片字节嵌入 PPTX。通过 Python `inspect` 获取真实像素大小，在计划阶段自行保持相近缩放。
- `texts[]` 可添加少量形状内文字，每项含 `name`、`text`、`box`，可选 `size_pt`、`color`、`bold`、`align`、`fill`。默认字号 18 pt、黑色、顶部对齐。
- `items[]` 是 Summary 段落，`level` 为 0 或 1，`color` 可取黑色、蓝色或浅灰色。默认蓝色只给当前结论。
- `paragraphs` 配合 `body_box` 可在正文页添加紧凑的多段内容，例如通讯作者履历或 Outline。每项含 `text`，可选 `color`、`level`、`bullet`。默认单一形状、Arial 18 pt、1.5 倍行距。
- `cover.title` 与 `byline` 支持显式换行。长标题应在制作时按语义合理断行。
- `main_figures` 与 `images[].panels` 共同用于检查主图 panel 是否覆盖。Extended Data 可用 `ED1a` 等标识，不必填入 `main_figures`。

## 操作

通过 Codex 的 `load_workspace_dependencies` 获取 Node、包目录和 Python 路径。将 `RUNTIME_NODE_MODULES` 设为返回的 Node 包目录，使用该 Node 执行构建器。构建器还可通过 `NODE_PATH` 或正常 Node 模块解析找到 Artifact Tool。

先输出 raw PPTX，再运行 `pptx_finish.py`，它完成原生形状、段落行距、bullet 层级和逐段颜色的格式化。`check_deck.py` 检查包完整性、外部关系、文字对象、备注与主图覆盖。

```powershell
& $runtimeNode "$skillPath/scripts/build_deck.mjs" --plan "$project/Source/deck.json" --output "$project/Source/deck.raw.pptx"
& $python "$skillPath/scripts/pptx_finish.py" "$project/Source/deck.raw.pptx" --plan "$project/Source/deck.json" --output "$project/Presentation/journal_club.pptx"
& $python "$skillPath/scripts/check_deck.py" "$project/Presentation/journal_club.pptx" --plan "$project/Source/deck.json"
& "$skillPath/scripts/render_slides.ps1" -PresentationPath "$project/Presentation/journal_club.pptx" -OutputDirectory "$project/Source/rendered"
```

变量需要使用目标机器实际路径。用户只需提供题名，上述计划、素材准备和构建由执行 skill 的 Codex 完成。
