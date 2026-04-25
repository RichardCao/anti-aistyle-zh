---
name: anti-aistyle-zh
description: 中文优先的去 AI 味改写 skill。Use when the user asks to reduce AI traces, ChatGPT tone, 模型腔, 去 AI 味, AI 味重, 太像 AI 写的, 减少机器生成痕迹, 解释腔, 总结腔, 汇报腔, 课件腔, 翻译腔, or over-smooth/template-like Chinese writing in 短文, 文章, 评论, 随笔, 小说, 长文, 提纲, 总纲, 卷表, or 章节规划. Rewrites toward natural Chinese while preserving meaning, voice, genre, and factual boundaries; audits residual AI-flavored structure. Do not trigger only for requests to be more formal, more marketing-oriented, or more bureaucratic.
---

# 中文去 AI 味

这个 skill 处理统一的中文去 AI 味问题，不按题材拆入口。短段、单篇文章、中长文、小说章节、长篇主稿、总纲、卷表、章节规划都走同一个入口；题材差异只在内部判断。

## 触发后边界确认

触发后只确认一件事：用户目标是否是降低 AI 痕迹，而不是单纯要求更正式、更营销或更像公文。若只是后者，不按本 skill 默认执行。

## 主合同

主合同只保留单一入口、默认行为、分层决策、`hard fail` 和三张执行卡。详细规则统一放在 `references/`，按需读取，不在主合同双写。

固定合同：

- 默认调用只需要目标文本
- 可选控制项只有四类：`voice_sample / 样文`、`改写强度`（`rewrite_intensity`）、`目标读感`（`target_reading_feel`）、`输出模式`（`output_mode`）
- 默认改写强度：`平衡`
- 默认目标读感：`更像自然中文`
- 默认输出模式：`最终成稿`
- 对任何输入，真正的评估对象都只是去味后的最终内容
- 本 skill 不承诺绕过检测器，也不以检测分数作为最终评估对象
- 过程信息默认不前置展示；只有验证、审计、回归场景，才允许在最终成稿后附最短回执
- 输入太长时，继续分批输出最终成稿，不退化成只做诊断
- 长文允许因删除重复、解释、护栏、双面铺垫和空转论证而自然缩短；只有在主要靠压缩、摘要化、释义化完成去味，或把段落功能压扁时，才视为失败

## 工作原则

1. 先判层，再改写；上层没定案时，下层只能举证，不能抢改。
2. 先改姿态和结构，再改句子和词。
3. 所有频率判断先和原文比，再和同体裁、同长度、同运行方式的真人常态比。
4. 不做机械禁词；黑词和高频词只能举证，不能主导判断。
5. 不为去味改掉原意、立场、叙述重点或角色口吻，也不把“更口语”“更乱一点”误当成“更自然”。
6. 不把地域、阶层、社群、职业、代际差异洗成统一标准语；原文有声纹时先保声纹。
7. 正式、规范、克制、结构清楚本身不是 AI 味；只有当它们承担重复解释、统一人格、模板推进或过度收束时才处理。
8. 二改只在残留还能稳定指出时继续；如果只剩整体气口偏稳，就停手。

## 内部固定顺序

统一内部顺序固定为 `诊断 -> 改写 -> 审计`，默认不把这些过程标题前置展示。

如果输入是整部长篇，层级顺序固定为 `剧情 / 提纲层 -> 小说长篇层 -> 长文层 -> 文本层`。

## 决策树

1. 只有总纲、卷功能、章节规划、人物弧线表：直接改已有结构文件，不等正文。
2. 多份纯规划文件一起给：先做 `规划包对表`，定 authority file、冲突字段、recurring system 和 per-volume quota。
3. 提纲类文件和正文同时存在：先做 `提纲-正文偏差诊断`，再决定改哪一边。
4. 只有整部长篇原文：先抽 `影子结构`，再回写正文。
5. 只是局部摘录、单章或短段：可直接从较低层开始；若一眼能看见标准主导路线，内部先形成一句 `主导路线 / 功能链`；只有用户要求诊断、验证、审计、回归或分层输出时才外显。
6. 对长文、小说、提纲输入，默认先判结构层，再决定是否进入句级。

长度边界：

- `1500` 字以内：可直接改
- `1500-8000` 字：先看段落功能、整篇气口和主导路线
- 超过 `8000` 字、超过 `3` 个文件、或整部长篇：先抽结构再回写

## Hard Fail

完整触发条件、完成阈值和提纲专项动作以 [references/plot_outline_rules.md](./references/plot_outline_rules.md) 为唯一权威。主入口只保留三条硬约束：

- 命中结构层 `hard fail` 后，不能停在诊断或建议。
- 默认直接重构高风险卷、章节群或结构块。
- 完成必须同时降低主模板覆盖、打破长度 / 节点对称，并拆掉统一终局坡道。

## 1. 诊断卡

诊断不要写成长报告，只指出最主要的 `3-7` 个问题。先判断主要 AI 味来自哪一层：

- `姿态`：替读者解释、结尾盖章、作者像在整理答案
- `结构`：连续解释链、段首报题、长距离重复论证、篇章关系过匀、标准骨架过稳
- `伪具体`：细节像安全补丁，没有改变段落功能、scene 运行或结构重心
- `文气 / 句法`：汇报腔、课件腔、过度清楚 / 过度体面 / 控场感过强，连续句型、长短句、断句和标点过稳
- `小说`：动作后的心理翻译、情绪落锤模板、线索和证人来得太准、scene 发动方式同模
- `提纲`：功能分配过匀、升级路径准点、角色推进过于公平、揭示机制重复、规划壳话太重

附加动作：

- 文本超过 `1200` 字，内部先形成一句 `主导路线 / 功能链`；只有用户要求诊断、验证、审计、回归或分层输出时才外显
- 评论 / 方法文优先检查 `判断 -> 解释 -> 例子 -> 收束`
- 随笔 / 叙事优先检查 `现场 -> 回望 -> 领悟`
- 长文优先检查段群关系是否总在同一套因果 / 转折 / 回收关系里推进
- 小说优先检查线索、证人、物件、揭示是否按功能排队
- 提纲至少拆成 `卷级链 / 章节群链 / 单章微链`

如果有 `voice_sample`，只额外判断三件事：原稿最像样文的是什么、最偏离样文的是什么、哪些节奏和收束习惯必须保留。

## 2. 改写卡

改写固定按六步走：

0. `先判主导路线`
1. `先删`：二次解释、二次总结、二次证明、作者补的半句翻译
2. `再压`：连续解释链、同功能段落、长文回潮的大意回收、连续句法同色
3. `再换`：抽象判断换事实 / 动作 / 结果 / 后效，过稳篇章关系换局部断口，工整收束换自然停住
4. `再补`：先重排原文已有细节，再补原文已暗示的介质；小说 / 叙事新增细节只有在能改变段落功能、scene 运行或结构重心时才算有效，事实类文本按执行边界不新增无依据事实
5. `最后校正层级`

层级校正只保留这些硬判断：

- 评论 / 方法文：允许一段只停在观察；不要把删解释后的正文重新缝成更短、更稳、更像标准答案的新稿
- 随笔 / 叙事：允许一段只停在现场，不急着讲圆
- 长篇正文：先抽影子结构，再回写正文
- 提纲：直接改功能分配、人物轮转、升级路径、揭示机制；命中 `hard fail` 时必须直接改高风险块
- 强体裁 / 设计外题材：优先保体裁，不把原文洗成另一种统一解释体系

## 3. 审计卡

改完后回扫：

- `解释残留`
- `骨架 / 篇章关系残留`
- `收束残留`
- `句法 / 断句 / 标点残留`
- `姿态 / 人格残留`
- `伪具体残留`
- `压缩 / 摘要化残留`
- `转场回潮残留`
- `安全限定回潮残留`
- `虚词 / 关联词回潮残留`
- `否定骨架回潮残留`
- `连续热区残留`
- `小说残留`
- `提纲 / 规划感残留`
- `越界检查`

只有同时满足这些条件时才二改：

- 同类残留还能指出 `2` 处以上
- 问题能落到具体句法、姿态或结构
- 再改不会明显伤到口吻支点

但只要命中长文专项里的长度强审线、体裁边界，或去味主要靠压缩、摘要化、释义化完成，就必须继续回写。

## 输出方式

默认输出只有 `最终成稿`。

默认规则：

- 过程信息放在最终成稿之后，且只在用户要求、验证、审计或回归场景下附出
- 默认回答开头不得出现 `诊断`、`主导路线`、`功能链`、`manifest`、`审计`、`执行回执` 等过程标题
- 长文 / 长篇 / 多文件输入时，内部可先形成 `manifest` 和简短诊断，但默认不前置展示
- 输入是超长纯提纲时，默认输出改后的提纲正文 / 结构文本
- 命中 `hard fail` 时，输出中必须包含被重构的高风险卷 / 章节群的实际改后版本
- 输入太长时，按批次继续输出改后的最终内容
- 超长输入分批时，每批仍以改后内容为主；批首只标明本批范围，批尾最多一句说明下一批应接哪里，不把第一批退化成总诊断或建议书

不要做：

- 不要退化成只给建议书
- 不要只写“应当改成什么”，不落地改后的结构
- 不要硬贴一长串“每卷一句功能概括”

## 执行边界

优先删：解释句、总结句、盖章句、领句、动作后的半句翻译。

优先留：真能推进冲突或认知的判断句、角色口吻、必要专业词、世界内器物、地方性说法，以及能体现地域 / 阶层 / 社群 / 职业 / 代际差异的声纹。

事实类文本强边界：如果文本承担事实说明、评论分析、专业解释、政策 / 法律 / 医疗 / 技术 / 学术功能，不新增原文没有给出的事实、数据、身份、场景、时间地点、因果链或人物动机。去味只能通过删解释、压总结、重排原文材料、降低过度收束来完成。原文没有支撑的“更具体”不是去味，是越界。

不要做：

- 不要把文本改成统一碎口语
- 不要为了“像人”故意加病句
- 不要为了降低 AI 感硬加错字、口头禅、情绪噪音、无意义停顿或无支撑细节
- 不要把文本改成另一种统一 AI 腔
- 不要为了去味伤到口吻支点
- 不要擅自新增关键设定、改名词体系、改立场

## Reference Routing

只按当前任务读取必要 reference，不要整包载入：

| 场景 | 默认读取 | 不要读取 |
| --- | --- | --- |
| `1500` 字以内短中文文本 | [references/chinese_ai_markers.md](./references/chinese_ai_markers.md) | [references/novel_longform_rules.md](./references/novel_longform_rules.md)、[references/plot_outline_rules.md](./references/plot_outline_rules.md) |
| 短但强体裁：通知、FAQ、知识库、客服口径、口播、社媒脚本、审稿回复 | [references/chinese_ai_markers.md](./references/chinese_ai_markers.md)、[references/rewrite_principles.md](./references/rewrite_principles.md)；有压缩、卡片化或体裁漂移风险时加读 [references/longform_validation_rules.md](./references/longform_validation_rules.md) | 小说 / 提纲专项，除非输入本身是小说或规划 |
| 需要跨题材高层模式判断 | [references/chinese_ai_markers.md](./references/chinese_ai_markers.md)、[references/ai_markers.md](./references/ai_markers.md) | 按需 |
| 中长评论 / 方法文 | [references/chinese_ai_markers.md](./references/chinese_ai_markers.md)、[references/rewrite_principles.md](./references/rewrite_principles.md) | [references/plot_outline_rules.md](./references/plot_outline_rules.md) |
| `3000+` 长文、强体裁或压缩风险 | [references/longform_validation_rules.md](./references/longform_validation_rules.md)、[references/rewrite_principles.md](./references/rewrite_principles.md) | [references/novel_longform_rules.md](./references/novel_longform_rules.md)，除非是小说 |
| 小说章节 / 连载正文 / 长篇主稿 | [references/novel_longform_rules.md](./references/novel_longform_rules.md)、[references/rewrite_principles.md](./references/rewrite_principles.md) | [references/plot_outline_rules.md](./references/plot_outline_rules.md)，除非同时给提纲 |
| 纯提纲 / 卷表 / 章节规划 | [references/plot_outline_rules.md](./references/plot_outline_rules.md)、[references/outline_denoise_checklist.md](./references/outline_denoise_checklist.md) | [references/chinese_ai_markers.md](./references/chinese_ai_markers.md)，除非还要改句子 |
| 用户要求控制项解释 | [references/control_modes.md](./references/control_modes.md) | 其他按需 |
| 审计 / 验证 / 回归 | [references/audit_checklist.md](./references/audit_checklist.md)、[references/examples.md](./references/examples.md) | 按需 |
