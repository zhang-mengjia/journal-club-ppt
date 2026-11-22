# Journal Club PPT

从论文标题、DOI、链接或 PDF 制作完整的组会 Journal Club PowerPoint。默认英文页面、中文正式讲稿，正文以论文原图为主，采用黑色标题栏、蓝色强调与紧凑的阶段性 Summary。

## 使用

安装后向 Codex 发送论文标题即可，例如

> 使用 $journal-club-ppt，为《论文标题》制作完整的组会 JC PPT，保存到我指定的文件夹。

正式汇报从论文标题页开始。人物介绍只展示论文的通讯作者，单人页以 `Corresponding author` 为标题，合页用 `Corresponding authors`。每位通讯作者都有可编辑的 `Neurotree`，按可核实的资料标出导师和训练关系。随后用背景原图引出研究问题、结果提纲和分组汇报。

结果大标题优先取自论文 Results 小节或图题，同一发现可以连续讲多页。只有同一主题出现在多页标题中时，才写成 `A | B`；单页主题直接写名称或结果句。默认覆盖全部主图，必要附图就近插入。图片嵌入 PPTX，正文和讲稿可编辑。详见[样式规范](references/style.md)与 [Bowler 现稿逐页对照](references/bowler-slide-map.md)。

![默认版式预览](assets/preview.png)

## 安装

将这段提示词发送给目标电脑上的 Codex

> 从 https://github.com/zhang-mengjia/journal-club-ppt 安装 journal-club-ppt skill。仓库根目录就是 skill，将整个仓库安装到 CODEX_HOME/skills，未设置 CODEX_HOME 时使用用户主目录的 .codex/skills。保留 scripts、references、assets 的相对结构。先检查同名目录与本地修改，安装后验证 SKILL.md 和内部引用，并检查可用的 PPTX 运行时、PyMuPDF、Pillow 与渲染工具。

也可以使用 Git 克隆到 Codex 的 skills 目录，目录名保持 `journal-club-ppt`。安装后重新打开 Codex 会话。

## 运行环境

仓库随包提供通用 PPTX 模板、预览、版式规范与脚本，资源通过包内相对路径引用。每次制作所需的论文、图像和用户指定的模板放在当前项目中，逐页计划使用项目内的相对路径。

skill 的检索、精读和内容组织由 Codex 完成。随包构建器使用 Codex Artifact Tool JavaScript 运行时，通过 `load_workspace_dependencies` 查找，再设置 `RUNTIME_NODE_MODULES`。Python 的 PDF 与图片准备工具分别使用 PyMuPDF 和 Pillow。字体默认 Arial，字体文件和运行时由目标机器提供。

Windows 可用已安装的 PowerPoint 逐页渲染。其他平台可使用可用的演示文稿渲染器或 LibreOffice，并逐页检查排版。可在用户指定的其他 PPTX 工具中按同一版式制作。

| 文件 | 用途 |
| --- | --- |
| [SKILL.md](SKILL.md) | Codex 工作流与默认要求 |
| [assets/jc-reference.pptx](assets/jc-reference.pptx) | 可分发的空白样式参考 |
| [references/plan.md](references/plan.md) | 逐页计划格式和构建方法 |
| [scripts/](scripts/) | 素材处理、PPTX 构建、原生文字整理、检查和渲染 |

仓库分发通用版式、说明和代码。实际论文、论文图片、作者肖像和用户项目资料保存在执行任务的本地项目中，遵循各自来源的使用条件。

《Subspace communication in the hippocampal–retrosplenial axis》用作本机实测。结果部分覆盖 5 张主图的全部 28 个 panel，按论证顺序插入必要附图。正文依据公开作者稿，图像取自出版社正式版，图号对应关系随本地项目保存。

代码与通用模板采用 MIT 许可证。
