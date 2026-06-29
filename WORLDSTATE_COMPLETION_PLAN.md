# Warframe 官方 Worldstate 剩余补全计划

更新时间：2026-05-18  
数据基准：`https://api.warframe.com/cdn/worldState.php` 实时抓取结果 + 游戏内人工校对样本

## 1. 当前状态

当前技能已经完成以下基础能力，不再列为待办：

- 主入口统一为 `worldstate`
- `Sorties` / `VoidTraders` / `ActiveMissions` / `Invasions` / `VoidStorms` / `DailyDeals` / `SeasonInfo` / `SyndicateMissions` 的基础解析已接通
- `Alerts` 已接通为独立模块
- `状态` 总览模式可运行
- `Baro`、`裂缝`、`入侵`、`虚空风暴`、`警报`、`每日特惠`、`夜波/赛季`、`集团任务`、`仲裁缺失提示` 均已有可用输出
- `Events` 已以轻量公告流形式模块化
- `PrimeVaultTraders` / `Goals` / `Conquests` 已完成原始数据版模块化，便于后续继续调教
- `SKILL.md` 已同步当前支持的命令集合

本文件只保留 **仍未完成** 或 **仍需改进** 的点。

## 2. 剩余核心问题

### 2.1 节点映射仍不完整

这是当前最主要的未完成项。

live 输出里仍有大量原始节点编号未翻译，例如：

- `Sortie`: `SolNode41`、`SolNode225`、`SolNode137`
- 裂缝: `SolNode27`、`SolNode70`、`SolNode220`、`SolNode743`
- 入侵: `SolNode118`、`SolNode127`、`SolNode32`、`SolNode67`
- 集团任务: `SolNode61`、`SolNode119`、`SolNode30`

要求：

- 继续补齐 `PLANET_NAME_FALLBACKS`
- 优先覆盖 live 中持续出现的 `SolNode###`
- 补齐 `SettlementNode#` 的真实中文地点
- 避免再退化为“太阳系节点”“殖民地节点”这类过泛标签

### 2.2 突击节点与 modifier 仍未完全对齐游戏内显示

当前突击已经能显示 Boss、任务类型和大部分 modifier 中文，但仍存在两类不足：

- 节点仍可能显示为 `SolNode###`
- 未覆盖的 modifier 仍会退回原始 `SORTIE_MODIFIER_*`

已知游戏内校对样本（应作为映射正确性的基准）：

- `Arval（火星）`：救援，状态 `仅限霰弹枪`
- `Suisei（水星）`：破坏，状态 `敌人护甲强化`
- `Nuovo（谷神星）`：移动防御，状态 `敌人物理强化`

要求：

- 为未知 `SORTIE_MODIFIER_*` 提供更友好的退化显示
- 持续扩充 `SORTIE_MODIFIERS`
- 将 `Sortie` 节点映射到游戏内实际地点名，而不是仅显示内部 node id

### 2.3 裂缝任务类型和节点文案仍有粗糙项

当前裂缝已基本可读，但还有以下问题：

- 仍可能出现英文或半英文任务类型
- `MT_HIVE` 目前文案为 ` hive 任务`，需要修正为空格和命名都更自然的中文
- 高编号扎里曼/双衍/特殊节点映射仍不够全

要求：

- 清理全部 live 中已出现的 mission type
- 统一任务类型翻译风格
- 修正明显粗糙文案

### 2.4 集团任务仍有大量占位式输出

当前 `SyndicateMissions` 已从纯 `N/A` 提升为“有节点就显示节点、没有就显示集团默认说明”，但仍存在以下问题：

- `KahlSyndicate - 特殊任务`
- `HexSyndicate - 特殊任务`
- `EntratiLabSyndicate - 特殊任务`
- `RadioLegionIntermissionXXSyndicate - 特殊任务`

这类兜底文案比空值更好，但仍不是最终玩家友好结果。

要求：

- 尽量从 `Nodes`、`MissionInfo`、其他上下文字段继续挖真实位置
- 对常见 syndicate tag 建立更自然的中文名和地区说明
- 将“纯技术 tag + 特殊任务”替换成玩家理解成本更低的说法

### 2.5 虚空风暴粒度仍偏粗

当前 `VoidStorms` 已能显示纪元与时间，但节点仍统一归为“航道飞机”。

要求：

- 如果官方字段无法提供更精细位置信息，则保留当前实现
- 若可从 node 结构或其他字段中进一步区分具体航道区域，应补充更细粒度描述

## 3. 官方模块补全现状

### 3.1 已模块化

以下模块已经接入为独立命令：

- `Events`
  - 当前状态：已做成轻量公告/新闻流
  - 完成度：可用，但仍需继续优化筛选与去重
- `PrimeVaultTraders`
  - 当前状态：原始数据版
  - 用途定位：Prime 重生商店
- `Goals`
  - 当前状态：原始数据版
  - 用途定位：活动目标
- `Conquests`
  - 当前状态：原始数据版
  - 用途定位：深层科研 / 时光科研

### 3.2 尚未模块化且值得继续做

以下模块仍未接入为独立命令，且仍有一定玩家价值：

- `PrimeAccessAvailability`
  - 当前判断：Prime Access 状态标记
  - 价值：低到中，信息量小，但能作为 Prime 商店辅助状态
- `PersistentEnemies`
  - 当前判断：当前 live 为空，但理论上可能承载需要追踪的常驻敌人信息
  - 价值：中，需等 live 再次出现数据后判断
- `PrimeVaultAvailabilities`
  - 当前判断：Prime 重生 / Prime Vault 槽位可用性布尔数组
  - 价值：低，但与 Prime 重生体系有关，后续可和 `PrimeVaultTraders` 联动再看

### 3.3 尚未模块化且当前价值较低

以下模块目前更偏后台配置、商城辅助或系统控制字段，暂不建议优先模块化：

- `FlashSales`
  - 当前判断：商城特价 / 上架覆盖表
  - 原因：主要是商城内部商品路径、价格覆盖和显示控制，对 worldstate 日常查询价值不高
- `InGameMarket`
  - 当前判断：商城落地页与分类配置
  - 原因：更像游戏内商城导航配置，不是时效情报
- `GlobalUpgrades`
  - 当前判断：当前 live 为空
  - 原因：无 live 样本，且暂未显示出强玩家价值
- `HubEvents`
  - 当前判断：当前 live 为空
  - 原因：无 live 样本，暂不投入

### 3.4 暂不作为独立模块优先项的系统字段

以下字段当前更像前端/系统/版本控制用辅助字段，暂不作为技能模块目标：

- `ConstructionProjects`
- `Descents`
- `EndlessXpChoices`
- `EndlessXpSchedule`
- `ExperimentRecommended`
- `FeaturedGuilds`
- `ForceLogoutVersion`
- `KnownCalendarSeasons`
- `LibraryInfo`
- `LiteSorties`
- `MobileVersion`
- `NodeOverrides`
- `PVPActiveTournaments`
- `PVPAlternativeModes`
- `PVPChallengeInstances`
- `PrimeTokenAvailability`
- `ProjectPct`
- `SkuSales`
- `Time`
- `Tmp`
- `TwitchPromos`
- `Version`
- `WorldSeed`

## 4. 文档与维护能力剩余工作

### 4.1 `SKILL.md` 仍可继续补强

虽然命令已同步，但仍建议补充：

- 哪些模块当前是“完整可用”
- 哪些模块仍依赖节点映射补全
- 哪些模块当前只是“原始数据版”
- 哪些模块在官方无数据时会显示空状态

### 4.2 仍缺少维护型调试命令

建议新增但尚未实现：

- `原始 worldstate`
- `原始 <模块名>`
- `键列表`

目的：

- 当官方字段变化时，快速人工核对
- 方便继续补映射与解析

### 4.3 仍缺少离线回归样例

当前目录已清理测试文件，但后续要真正稳定维护，仍建议补回离线验证资产：

- `samples/live_snapshot.json`
- `samples/minimal_snapshot.json`
- `samples/empty_sections_snapshot.json`

要求：

- 样例只用于维护和回归，不放入最终玩家输出流程
- 样例要覆盖当前最容易回归的模块：`Sorties`、`Alerts`、`DailyDeals`、`SyndicateMissions`

## 5. 剩余实施顺序

### Phase A：把已接入模块做细

- 补 `SolNode###` / `SettlementNode#` 映射
- 补 `Sortie` 节点名与 modifier 映射
- 修正 `MT_HIVE` 等粗糙文案
- 提高集团任务节点解释质量

### Phase B：补未接入的官方模块

- 将 `PrimeVaultTraders` 从原始数据版提升为可读摘要版
- 将 `Goals` 从原始数据版提升为可读摘要版
- 将 `Conquests` 从原始数据版提升为可读摘要版
- 评估并决定是否新增 `PrimeAccessAvailability`
- 等待 live 样本后评估 `PersistentEnemies`
- 视 `PrimeVaultAvailabilities` 与 `PrimeVaultTraders` 的联动价值决定是否补模块

### Phase C：补维护基础设施

- 新增原始调试命令
- 增加离线 snapshot
- 形成固定回归流程

## 6. 完成标准

满足以下条件才算这份剩余计划完成：

- `Sortie` 输出能稳定对应游戏内节点与状态文案
- live 常见 `SolNode###` 不再大面积裸露在用户输出中
- `SyndicateMissions` 不再大量依赖 “`<Tag> - 特殊任务`” 占位文案
- `MISSION_TYPE_MAP` 中不再存在明显粗糙翻译
- `Events` 维持低噪音轻量公告输出
- `PrimeVaultTraders`、`Goals`、`Conquests` 至少完成可读摘要版
- `PrimeAccessAvailability`、`PersistentEnemies`、`PrimeVaultAvailabilities` 的去留有明确结论
- `SKILL.md` 与实际命令集合、完成度状态保持一致

## 7. 需要人工协助的数据

目前最有价值的人工协助，不是泛泛的游戏数据，而是精确校对样本：

- `SolNodeXXX -> 游戏内真实节点名`
- 某天 `Sortie` 三关的游戏内节点名 + 状态文案
- `SyndicateMissions` 在游戏内面板中的真实地点显示
- 特殊集团 / 扎里曼 / 航道任务在游戏内的实际中文名

这类样本可直接用于提升映射质量与最终可读性。
