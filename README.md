# biomedical-figure-style

`0.1.0-rc1` 是可离线运行的医学综述图设计核心：通用指南、四组配色、公共综述参考查询，以及图计划的结构和语义比较。它不是图片生成器，也不自动判断医学正确性。

包内有 **763 条公共综述图参考记录、237 张公开设计卡投影、11 类通用布局**。763 条记录来自 **609 篇独立综述（按 DOI 去重）**，不能把图参考数当作论文数。按 2026-10-28 筛选，首次在线日期窗口为 2023-10-28 至 2026-10-28；原库的 12 条超窗记录与 61 条个人原始案例均未导出，原库保持原样。图片、检索历史、私人测试、外部 PPTX 生成依赖均未打包。来源信息和既有学习状态未在本次发布时重新联网核验。

## 安装

需要 Python 3.9 或更高版本。核心脚本仅使用标准库；按运行日筛选需要系统可用的 IANA 时区数据。若系统没有时区数据，显式传入 `--as-of YYYY-MM-DD`。无需 Node、绘图服务或网络连接。

把整个 `biomedical-figure-style` 文件夹复制到技能目录，例如 `$CODEX_HOME/skills/biomedical-figure-style`，保留 `scripts`、`references`、`assets`、`agents` 的相对位置。已有同名个人完整版时，先保留它，勿直接覆盖；可把本文件夹放在任意独立位置并直接运行其中脚本。

以下示例均从本文件夹运行；也可用脚本绝对路径从任意目录运行。重命名外层文件夹不影响脚本找数据。

## 三种调用

**1. 找布局参考，然后查看一张公开卡：**

```sh
python3 scripts/query_references.py --query 分类 --summary-only --limit 5 --as-of 2026-10-28
python3 scripts/query_references.py --id B2212-01 --as-of 2026-10-28
```

可用 `--layout L06`、`--require-design-card`、`--content-status text_aligned` 等筛选。`--query` 中空格分开的词必须全部匹配。`--limit` 为 1–30。摘要模式只检索显示的有限字段；它仍会在本地解析整个已精简目录。普通模式返回命中的完整**公开投影**卡。到期或待核实来源默认不返回，必要时使用 `--include-historical` 并阅读其资格原因。

**2. 读取通用图文逻辑、布局及配色：**

```sh
python3 scripts/read_guidance.py --topic all
```

也可单独选择 `logic`、`layouts`、`style`。选段通过 SHA256 校验；编辑指南后须同步更新 `references/guidance_sections.json`。公开版没有历史案例附录，`--list-cases` 返回 0 条。

**3. 检查图计划与一次纯配色修改：**

```sh
python3 scripts/validate_figure_logic.py examples/panel.json
python3 scripts/validate_figure_logic.py examples/panel_recolored.json --compare examples/panel.json
```

示例完全合成，不包含生物学主张。检查器使用 `semantics.entities/relations` 及可选 `visual.nodes/edges`；实体、关系均需稳定 ID。它能发现部分缺字段、端点错误与语义属性变化；不检查实际图像，不是任意 JSON 的容错验证器。设计卡语义摘要不保证符合此图计划合约，不能直接把卡片当作待校验图计划。

## 数据及状态

`references/catalog.json` 保留公共综述的元数据和精简设计笔记。`design_cards.json` 逐层使用白名单，只保留 source、task、design、semantics、rules、status 中允许的字段。没有复制原始卡的完整对象、图注、长摘要、论文正文或验证记录。少数内容被截短并带提示，本地路径和明确私人验证引用改为“本地验证记录未随包发布”；所有投影规则和计数见 `references/release_projection.json`。

七个状态轴独立：image_range、clarity、access、saved、license、content、rule。公开包 `saved` 统一为 `link_only`；其余状态来自既有记录。查询器中卡片状态覆盖目录状态，同一记录的 `status` 覆盖 `status_axes`。状态不是本次发布的重新验证，也不能据此断言图像许可、医学正确性或任意任务性能。卡内规则 ID 可能只引用个人库注册表；该注册表未随包发布。

默认三年窗口以首次在线日期和随包筛选策略判定；它是选例范围，不代表科学证据等级。`refresh_review_scope.py` 是查询器的本地依赖；直接运行它会改写目录和索引，日常查询无需运行它。

## 版本与许可

这是可安装的 `0.1.0-rc1` 测试版。源码许可证未指定，不宣称已按某种开源许可证授权。第三方资料的来源和权利边界见 [SOURCES_AND_RIGHTS.md](SOURCES_AND_RIGHTS.md)，版本说明见 [RELEASE_NOTES.md](RELEASE_NOTES.md)，实际检查与限制见 [VALIDATION.md](VALIDATION.md)。
