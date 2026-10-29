# 图文逻辑与内容驱动设计

用于文章驱动作图、改变图意的精修、图文检查和新的综述案例学习。沿用原审美、布局、绘制和导出流程；默认配色仍为 P01。

## 从文章到图，再返回文章

1. **确定任务。** 阅读摘要、完整图注、对应完整正文段落，保留页码/小节/段落定位。识别问题、一句核心主张、背景与重点、实测结果与作者综合/假说。只读取图注不能标为机制核验；有冲突时再查必要上下文或关键原始研究。
2. **独立看图。** 实际查看完整 Figure，关键端点、标签或区室另看局部。先写 A：可见对象、位置、连接；再写 B：图例/图注定义；最后写 C：正文主张。保存文件、OCR、读 SVG 源码均不能替代视觉查看。看不清的局部写无法判定。 多图任务逐张绑定文件路径和图号，当前图的 A 记录保存后再切换；涉及删除节点或连线的建议，重新打开对应图确认对象确实存在。
3. **整理语义。** 给实体和关系稳定 ID。实体注明状态、区室、体系；关系注明起止点、类型、方向、条件、体系、证据性质及图文位置。表达量、活性、修饰和定位分别建状态；不把跨物种、疾病或阶段的关系拼成确定机制。
4. **双向核对。** 图→文检查关键关系是否有支持；文→图检查承诺表达的主张有无遗漏或失去限定。逐关系用 `match / partial / missing / conflict / uncertain`。主动省略背景与遗漏核心条件分开记录。综述中的表述与原始证据验证分开；已发表的图也可能有冲突。
5. **决定怎样画。** 每幅图先定主张与阅读顺序，再选布局。并行步骤保留分支与真实汇合；分类树使用无方向分类连线，只有有谱系证据才画祖先→后代；没有实际时间证据不用定量时间轴；受区室影响的机制保留区室。数据图保留变量、坐标、单位和比较对象，不从相关曲线补因果。 方法能力重叠且原文只给通常偏好时，用共同约束＋并列路线并就地保留例外；不把偏好转换为排他YES/NO门。方法内的步骤顺序与方法间分类分别编码。
   当用途取决于两个分别定义的判据时，可用双判据表或二维情景保留其组合、无效情景与前提；分别定义不代表统计独立。不要压成单一优劣或时间链；没有第二判据时不补造轴。


6. **实际制作和复查。** 原创绘制或在用户授权范围内编辑；语义与视觉属性分层，改变坐标/颜色后比较语义不变。渲染查看整图、必要局部及目标尺寸，逐一核对关键端点和对应标签。发现问题后修复并重新看图；不能只检查源码。

## 公开设计卡

公开版保留 source、task、design、semantics、rules、status 的白名单字段。卡片是原库的有界投影，不含原始图片、完整正文、私人验证、观察记录和历史附录。规则 ID 可能只是既有卡片中的引用；公开包不包含个人规则注册表，不能据此推断规则内容或验证能力。

## 状态轴

| 字段 | 值 |
|---|---|
| image_range | full_figure / panel / crop / unknown |
| clarity | original_or_high / clear / low_preview / unknown |
| access | viewed / caption_only / metadata_only / blocked / unknown |
| saved | archived / link_only / pending / missing |
| license | verified_with_exceptions / restricted / unverified |
| content | image_read / text_aligned / key_evidence_checked / conflict_or_insufficient / unknown |
| rule | candidate / integrated / tested / restricted_use / unknown |

状态来自既有记录，发布时未重新核验；本包没有原图，saved 统一为 link_only。没有新证据不批量推断新状态；`link_only` 可以已看完整图，`archived` 也不代表允许改编。整体清晰但端点不可读时在卡片局部边界记录限制。

## 语义与视觉文件

新图或需要保持语义的精修可用同一 JSON：

```json
{
  "semantics": {
    "entities": [{"id":"n1","label":"Signal X","state":"active","compartment":"cytoplasm","system":"model A"}, {"id":"n2","label":"Response Y","state":"activity","compartment":"cytoplasm","system":"model A"}],
    "relations": [{"id":"r1","source":"n1","target":"n2","type":"inhibition","condition":"stimulus present","system":"model A","evidence":"source-supported schematic; verify source in actual work","source_location":"section and paragraph","figure_location":"panel a","alignment":"match"}]
  },
  "visual": {"nodes":{"n1":{"x":100,"y":100},"n2":{"x":350,"y":100}},"edges":{"r1":{"end":"bar"}},"palette":"P01"}
}
```

示例仅为虚构结构。关系类型可用 activation、inhibition、association、transport、contains、adjacent、sequence、parallel、and、or、classification、lineage、other；分类/并行/包含不能默认渲染为因果箭头。`other` 需要自述。缺失条件用显式 unknown 并限制图意，不补常识。模型不能以校验器通过代替图文对齐。

实际尖头或抑制端线的方位决定图中方向；不能仅凭节点标签反推。结构检查通过不替代实际读图。
