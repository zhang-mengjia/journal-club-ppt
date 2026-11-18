---
name: journal-club-ppt
description: "根据论文标题、DOI、链接或 PDF 制作可直接汇报的 Journal Club／组会 PPT，采用原图拆页、少量文字、蓝色强调和中文正式讲稿。用于从论文到完整汇报的制作与同风格修订。"
---

# Journal Club PPT

交付一份可编辑、可离线使用的 `.pptx`。用户只给论文标题时，主动完成文献定位、材料获取、精读、原图拆分、排版、讲稿和放映检查，直接交付成稿。明确的用户要求优先于这里的默认值。

## 输入和材料

先查看当前目录的协作规则、已有论文材料和最新版 PPT，接续用户已经确认的内容。

1. 用正式出版社、PubMed、Crossref 等定位题名、作者、DOI、版本与通讯作者。区分正式版与同名预印本。
2. 优先取得正式 PDF、完整图注、Methods、全部主图及必要补充材料。出版社高清图优先，PDF 直接裁图也可使用。检查下载文件的实际内容，防止把登录页保存成 PDF。
3. 访问受限时，继续查找 PMC、机构库或作者公开稿。PMC 的公开全文 XML 也可用于阅读正文和 Methods，可经 NCBI Entrez 官方 `efetch` 获取。使用另一版本前核对主图和附图编号及影响结论的差异，并在项目的来源清单中记录。
4. 仍缺少正文、Methods、关键图注或清晰图片时，集中说明缺什么，并请用户提供相应 PDF／图片。此时继续做已具备材料支持的工作，待必要材料到齐再交付完整科学内容。用户提供的文件可以直接使用。

缺少汇报时长、听众或页数时，自行按完整组会精读组织内容。默认英文页面、中文正式讲稿，篇幅随实验逻辑与图的密度决定。材料足够时进入制作，不把这些可选信息变成等待条件。

材料放在任务目录的 `Paper/`，最终稿放在 `Presentation/`。使用 `Source/` 保存必要的逐页计划与裁图配置。来源 URL、版本、获取日期及可回查的 figure/panel/page 位置保存在项目清单中。

## 阅读与组织

通读正文、Methods、所有主图图注与相关补充材料，然后建立问题、实验、结果和后续问题之间的关系。逐项核对统计单位、重复测量、解码验证、分组和干预范围。

- 覆盖全部正文主图。默认逐 panel 规划，保持原始 panel 字母、坐标、单位、图例和统计标记。可把一张主图拆成多页。
- 必要 Extended Data 直接放进对应论证位置，和主图采用相同的标题与排版层级。
- 标题和阶段性 Summary 优先沿用原文简短表述。正文图页通常只需章节标题、小标题和原图。
- Authors 介绍论文的通讯作者。多位通讯作者均处理，简述核实过的教育、工作经历及实验室方向，配官方肖像或研究图片。
- Background 用少量简明结果与相关原始研究的图组合，帮助理解本文的问题和方法。优先原始研究、作者或机构资料。
- Summary 放在论证自然结束处。条目按自然行距连续排列，当前结论用蓝色，已经完成的内容用黑色，后续内容可用浅灰色。

保留相关性、预测、解码、模型和因果干预各自支持的范围。讲稿应当解释实验成立的前提及必要局限，避免把模型中的动力学机制直接归于真实脑区。

## 版式与文字

先读 [references/style.md](references/style.md)，查看 [assets/jc-reference.pptx](assets/jc-reference.pptx) 和 [assets/preview.png](assets/preview.png)。它们保存本 skill 的默认风格，用户另给模板时以用户模板为准。

- 白底、黑底白字标题栏、小型重叠方框标记。正文以论文原图为主，保留合适留白。
- 所有可编辑文字写入原生形状内部，包括标题、正文、Summary 和页码。使用矩形 AutoShape 并填充文字。
- 字体默认 Arial。强调蓝色为 `#0000FF`。正文与 Summary 默认 18 pt、1.5 倍行距、段前段后 0。
- 按同一篇论文原图中的轴字号、panel 字母和实验图大小校准缩放。整张图的像素宽度不同，不能只按像素缩放比例判断一致性。单页图少时保持适当大小。
- 图页文字保持少量。避免自行添加解释段落、角标、底部来源小字或把图放大填满页面。
- 论文图像嵌入文件。PPT 内的说明和讲稿采用离线自包含形式，来源清单保存在项目目录。

## 正式讲稿

每页备注写成可直接说出的流畅中文，专业术语保留必要英文。讲清研究问题、实验逻辑、结果与推断边界，衔接后续问题。

使用自然的科学叙述。删除“看图”“左边”“右边”“这里展示”“可以看到”等画面引导句式，以及给制作者的操作说明。备注内不写引用、URL、文件路径或检索过程。结论和数值仍需有项目来源清单支撑。

## 实现与交付

使用可用的演示文稿工具。Codex 的本地 Artifact Tool 运行时可通过 `load_workspace_dependencies` 发现，设置 `RUNTIME_NODE_MODULES` 后使用随包构建器。其他环境可按同一计划和版式用可用的 PPTX 工具完成。

按 [references/plan.md](references/plan.md) 写逐页 JSON 计划。所有素材路径相对于计划文件解析。

```text
python scripts/prepare_materials.py inspect paper.pdf --output Source/article_text.json
python scripts/prepare_materials.py crop figure.png --box 0 0 900 500 --output Source/panels/figure_a.png
node scripts/build_deck.mjs --plan Source/deck.json --output Source/deck.raw.pptx
python scripts/pptx_finish.py Source/deck.raw.pptx --plan Source/deck.json --output Presentation/journal_club.pptx
python scripts/check_deck.py Presentation/journal_club.pptx --plan Source/deck.json
```

`prepare_materials.py` 的 PDF 操作需要 PyMuPDF，图片裁切需要 Pillow。构建器使用运行时提供的 `@oai/artifact-tool`，不在 skill 中分发运行时或字体。输出路径已存在时换用新版本文件名。修改已有用户 PPT 时先读取当前文件，保留用户已保存的内容。

在 Windows 上可用 `scripts/render_slides.ps1` 调用本机 PowerPoint 逐页导出。其他平台使用可用的原生渲染器或 LibreOffice，检查与原模板的一致性。

交付前逐页查看实际渲染。检查主图覆盖、裁切、清晰度、大小、遮挡、形状文字、Summary 行距、讲稿与外链。修复发现的问题，再提供最终 PPTX。保留必要的源文件和论文原件，清理本轮无用途的中间文件。项目有 AGENTS.md 时更新实际状态与入口。
