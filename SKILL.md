---
name: biomedical-figure-style
description: Design biomedical review figures from article claims using general layout, palette and figure–text guidance; query public review metadata and inspect semantic-plan structure. Use for 文章驱动作图、医学综述图排版配色、原图精修方案和图文逻辑检查。Public offline core; no image generator or private library included.
---

# 医学综述图排版与配色 · 公开核心版

版本 `0.1.0-rc1`。根据用户稿件、机制清单或原图，先确定一句主张和阅读顺序，再选择布局与配色。未提供会改变图意的必要材料时明确缺口；尺寸和一般配色可自行选择。所有脚本路径相对于本技能目录。

## 使用流程

1. 新图、机制改动或图文核查：运行 `python3 scripts/read_guidance.py --topic logic`。区分实体、关系、条件、区室与证据；保留未知项，不用参考图补写科学结论。
2. 选择布局与视觉规范：分别运行 `python3 scripts/read_guidance.py --topic layouts`、`python3 scripts/read_guidance.py --topic style`；一次读取可用 `--topic all`。通用规则见 [图文逻辑](references/figure_logic_CN.md)、[版式](references/layouts_CN.md)、[视觉规范](references/visual_style_CN.md)；程序化配色见 [设计令牌](assets/style_tokens.json)。
3. 找参考：`python3 scripts/query_references.py --query 分类 --limit 5 --summary-only`。可增加 `--layout L06` 或 `--require-design-card`，再按精确 ID 读取公开投影卡。关键词检索是文字匹配，排序不是医学证据或期刊质量排名。默认按运行日的三年窗口筛选；固定日期用 `--as-of YYYY-MM-DD`。
4. 正式绘图使用当前环境可用工具。先布局，再画对象，最后放关系线与文字；修改原图前实际看图。仅改颜色、字体或位置时保留稳定 ID，将语义与视觉属性分开。
5. 对使用本包 JSON 合约的新图，运行 `python3 scripts/validate_figure_logic.py examples/panel.json`；比较视觉修改前后用 `python3 scripts/validate_figure_logic.py examples/panel_recolored.json --compare examples/panel.json`。这是结构与语义属性比较，不判断医学正确性。
6. 实际渲染后检查读图顺序、标签、关系起终点、区室、颜色含义和最终尺寸可读性；修复后交付实际生成的预览与源文件。可编辑连接是否随节点移动，需要在目标软件实际操作验证。

## 能力及资料边界

公开包含来自 609 篇独立综述的 763 条图参考元数据与 237 张公开设计卡白名单投影。按 2026-10-28 核对的首次在线日期窗口为 2023-10-28 至 2026-10-28，12 条超窗记录未导出。它们是既有记录的导出，发布时没有重新联网核实。仅保存官方来源链接与精简笔记，不附第三方图片、论文全文、61 条个人原始案例、历史检索档案或私人测试答案。查询整卡指公开投影中的完整卡，不能据此恢复个人完整版。

状态字段彼此独立。`saved=link_only` 描述本包没有原图；`viewed`、`text_aligned` 或 `tested` 沿用既有记录，不证明当前使用者已看图、科学结论正确或通用能力经过验证。本包不包含原生 PPTX 生成器、持续采集或任何外部绘图服务。实际绘图与文献核查仍按用户任务和当前工具执行。

来源与使用范围见 [SOURCES_AND_RIGHTS.md](SOURCES_AND_RIGHTS.md)，安装与示例见 [README.md](README.md)。本版为可安装测试版，源码许可证未指定，不宣称已获得某种开源许可证授权。
