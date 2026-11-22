# 逐页计划与构建

计划是 UTF-8 JSON。`paper` 保存论文标识，`main_figures` 保存正文主图的 panel 清单，`slides` 保存实际页序。图片路径以 JSON 文件所在目录为基准，例如 `panels/fig1a.png` 或 `../Paper/Figures/fig1a.png`。计划与图片的实际位置均须位于项目根目录内。

每页的 `notes` 是正式中文讲稿。配有论文图的页用 `figure_refs` 保存图号，构建器将每项加上方括号，在备注首行合并显示，并从下一行开始写入讲稿。`evidence`、图片的 `source` 和 `panels` 供工作记录与覆盖检查使用。

```json
{
  "paper": {"title": "Article title", "citation": "Author et al., Journal (year)", "doi": "10.xxxx/example", "corresponding_authors": ["Author name"]},
  "main_figures": {"1": ["a", "b"]},
  "slides": [
    {"type": "cover", "title": "Article title", "byline": ["Author et al.", "Journal (year)", "Journal Club"], "notes": "今天汇报的研究关注……"},
    {"type": "content", "header": "Corresponding author", "subtitle": "Author name", "author_names": ["Author name"], "paragraphs": [{"text": "Research appointments and current institution"}], "notes": "这位通讯作者主要研究……"},
    {
      "type": "content", "header": "Corresponding author", "subtitle": "Neurotree", "author_names": ["Author name"],
      "texts": [
        {"name": "Mentor", "text": "Mentor name\nDoctoral advisor, institution", "box": [420, 200, 440, 110], "align": "center", "valign": "middle", "fill": "#F2F2F2"},
        {"name": "Trainee", "text": "Author name", "box": [490, 450, 300, 80], "align": "center", "valign": "middle", "fill": "#F2F2F2"}
      ],
      "connections": [{"from": "Mentor", "to": "Trainee"}],
      "notes": "通讯作者的博士训练经历是……"
    },
    {"type": "question", "title": "How do activity patterns vary across conditions?", "notes": "接下来提出研究问题……"},
    {
      "type": "outline", "subtitle": "Research topic",
      "items": [{"text": "Comparing activity across conditions", "level": 0}, {"label": "Activity", "text": "Activity patterns differ across conditions.", "level": 1}],
      "notes": "研究者比较两个条件……"
    },
    {
      "type": "summary", "subtitle": "Research topic",
      "items": [{"text": "Comparing activity across conditions", "level": 0, "color": "#0000FF"}],
      "notes": "首先介绍比较的设计……"
    },
    {
      "type": "content", "header": "Activity patterns differ across conditions", "subtitle": "Recording conditions",
      "images": [{"path": "panels/fig1_ab.png", "box": [170, 245, 760, 300], "alt": "Task and experiment", "source": "Fig. 1a,b", "panels": ["1a", "1b"]}],
      "figure_refs": ["Fig.1A, B"], "notes": "研究者首先检验……", "evidence": ["Fig. 1a,b"]
    },
    {
      "type": "summary", "subtitle": "Research topic",
      "items": [{"text": "Comparing activity across conditions", "level": 0, "color": "#0000FF"}, {"label": "Activity", "text": "Activity patterns differ across conditions.", "level": 1, "color": "#0000FF"}],
      "notes": "这一部分说明……"
    },
    {
      "type": "discussion", "subtitle": "Research topic",
      "items": [{"text": "Scope of the finding", "level": 0}, {"text": "The comparison covers the recorded conditions.", "level": 1}],
      "notes": "这个结果的适用范围是……"
    },
    {"type": "thanks", "title": "Thanks!", "notes": "我的汇报结束，谢谢大家。"}
  ]
}
```

## 支持字段

- `type` 可为 `cover`、`content`、`question`、`outline`、`summary`、`discussion`、`thanks`、`figure`。作者、背景、方法和结果图页用 `content`。`question.title` 填写居中的完整问题。`figure` 用于无标题栏的纯图页，只排 `images`。
- `paper.corresponding_authors` 按原文列出全部通讯作者全名。人物介绍的每页在 `author_names` 中逐字填写当页介绍的通讯作者。单人页的 `header` 为 `Corresponding author`，多人同页为 `Corresponding authors`。每位通讯作者需要有履历介绍及小标题为 `Neurotree` 的师承图。每条边的依据放在项目来源清单。
- `header` 是黑色标题栏文字，默认 Arial 24 pt。长标题经放映核对后可设置 `header_size_pt`。`subtitle` 是粗体小标题。凡实际显示的标题采用 `A | B`，另一张页面也应有主题相同、左侧 A 相同的标题。单页主题写为独立短语或陈述句。同页重复及 `items[].label` 均不计。构建器提示孤立的前缀，所有标题中的竖线使用粗斜体。已有稿需要省略方框时可用 `show_marker:false`。编号页默认用放映顺序，也可用 `page_number` 填写原稿页脚文字。
- `images[].box` 为 `[x,y,width,height]`，默认 `contain` 保持完整宽高比。作者肖像可用同宽高的框、`"geometry":"ellipse"` 和 `"fit":"cover"`。核对人脸取景。图像均嵌入 PPTX，可通过 Python `inspect` 获取像素大小。
- `texts[]` 可添加少量形状内文字，例如结构式小标题所配的一句结果正文。每项含 `name`、`text`、`box`，可选 `size_pt`、`color`、`bold`、`align`、`fill`。默认字号 18 pt、黑色、顶部对齐。
- Neurotree 用 `texts[]` 排可编辑节点，用 `connections[]` 的 `from`、`to` 引用同页唯一的节点 `name`。从上方导师节点的底部连到下方受训者节点的顶部。节点正文显示姓名与实际训练身份，树页需能读出所介绍的通讯作者全名。多条关系可分别连接到同一人。每条连接线在 PowerPoint 中均随相连节点移动。
- `citations[]` 为图旁引文。按[署名规则](style.md#可编辑文字)将第一作者及共同一作填入 `first_authors`，将全部通讯作者填入 `corresponding_authors`。同一人兼具两种身份时只保留在一作组。每项同时填写 `journal`（期刊简称）、`year` 和 `box`。例如 `{"first_authors":["Hafting","Fyhn"],"corresponding_authors":["Moser"],"journal":"Nature","year":2005,"box":[760,550,365,32]}`，显示为 Hafting, Fyhn & Moser, *Nature*, 2005。构建器生成独立的 14 pt 文本框，仅期刊简称斜体。
  - 未标明通讯作者时可省略 `corresponding_authors`。未分组的旧版 `authors` 数组仍可读取，姓名用逗号分隔。已核实作者角色的计划可改用上述两个数组。
- `items[]` 是 Outline、Summary 或 Discussion 的原生段落。`level` 取 0 或 1，使用空心方框或实心圆。可选 `label` 会在正文前加入粗斜体 `主题 | `。`color` 缺省为黑色。根据[阶段规则](style.md#放映结构)从同一组研究步骤和结果生成 Outline 与 Summary，各页只调整可见层级和颜色。避免在各页独立改写相同的条目。
- `paragraphs` 配合 `body_box` 可在 `content` 页添加通讯作者履历等多段内容。每项含 `text`，可选 `color`、`level`、`bullet`。默认单一形状、Arial 18 pt、1.5 倍行距。旧版使用 `content.paragraphs` 的 Outline 和使用 `summary.items` 的 Summary 仍可构建。
- `cover.title` 与 `byline` 支持显式换行。按语义给题名断行，将作者、期刊卷页和组会标识依次放在灰带下。`thanks.closing_label` 默认显示 `Journal Club`，可按给定模板替换。
- `figure_refs` 是该页实际展示的论文图号列表，例如 `["Fig.1A, B", "Extended Data Fig.2D"]`。panel 用大写字母，整张图可写成 `"Fig.1"`。同一图号的 panel 合并填写。背景图沿用其来源论文的编号。无论文图的页省略该字段。备注首行只在演讲者备注中显示。
- `main_figures` 与 `images[].panels` 共同用于检查主图 panel 是否覆盖。Extended Data 可用 `ED1a` 等标识，不必填入 `main_figures`。

## 操作

通过 Codex 的 `load_workspace_dependencies` 获取 Node、包目录和 Python 路径。将 `RUNTIME_NODE_MODULES` 设为返回的 Node 包目录，使用该 Node 执行构建器。构建器还可通过 `NODE_PATH` 或正常 Node 模块解析找到 Artifact Tool。

构建器默认以计划所在目录为项目根，计划放在 `Source/` 时以其上一级为项目根。使用其他目录布局时，可用 `--project-root` 指定本次项目根目录。

先输出 raw PPTX，再运行 `pptx_finish.py`，它完成原生形状、段落行距、项目符号层级和逐段颜色。`check_deck.py` 从成稿中读取标题与师承连接，检查跨页前缀、通讯作者履历及师承覆盖，同时核对包完整性、文字对象、列表、引文、图片、备注与主图覆盖。

```powershell
& $python "$skillPath/scripts/prepare_materials.py" inspect "$project/Paper/paper.pdf" --output "$project/Source/article_text.json"
& $python "$skillPath/scripts/prepare_materials.py" crop "$project/Paper/figure.png" --box 0 0 900 500 --output "$project/Source/panels/fig1_ab.png"
& $runtimeNode "$skillPath/scripts/build_deck.mjs" --project-root "$project" --plan "$project/Source/deck.json" --output "$project/Source/deck.raw.pptx"
& $python "$skillPath/scripts/pptx_finish.py" "$project/Source/deck.raw.pptx" --plan "$project/Source/deck.json" --output "$project/Presentation/journal_club.pptx"
& $python "$skillPath/scripts/check_deck.py" "$project/Presentation/journal_club.pptx" --plan "$project/Source/deck.json"
& "$skillPath/scripts/render_slides.ps1" -PresentationPath "$project/Presentation/journal_club.pptx" -OutputDirectory "$project/Source/rendered"
```

在目标机器设置 `$skillPath` 为已安装的 skill 目录，`$project` 为当前项目根目录，`$runtimeNode` 和 `$python` 为可用的解释器。按实际论文文件名和 panel 裁切框替换示例参数。用户只需提供题名，上述计划、素材准备和构建由执行 skill 的 Codex 完成。
