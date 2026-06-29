# Warframe World State API 字段说明

> 数据源: `https://api.warframe.com/cdn/worldState.php`
> 本地原始数据: `worldstate_raw.json`
> 更新时间: 2026-06-17

## 顶层字段结构

### 系统信息字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `WorldSeed` | string | 世界种子（加密字符串） |
| `Version` | int | API 版本号（当前: 10） |
| `MobileVersion` | string | 移动端版本号 |
| `BuildLabel` | string | 游戏构建标签（含构建时间和哈希） |
| `Time` | int | 服务器当前时间戳（Unix 秒） |
| `ForceLogoutVersion` | int | 强制登出版本号 |

### 核心活动数据

| 字段 | 类型 | 说明 | 对应模块 |
|------|------|------|----------|
| `Events` | list | 公告/新闻/活动事件（36 条） | 公告模块 |
| `Goals` | list | 活动目标（2 条） | 活动目标模块 |
| `Alerts` | list | 警报任务（当前 0 条） | 警报模块 |
| `Sorties` | list | 突击任务（1 条） | 突击模块 |
| `LiteSorties` | list | 执行官突击（1 条） | - |
| `SyndicateMissions` | list | 集团任务（37 条） | 集团任务模块 |
| `ActiveMissions` | list | 虚空裂缝（23 条） | 裂缝模块 |
| `Invasions` | list | 入侵活动（16 条） | 入侵模块 |
| `VoidTraders` | list | 虚空商人 Baro（1 条） | 商人模块 |
| `PrimeVaultTraders` | list | Prime 重生商人（1 条） | Prime 重生模块 |
| `VoidStorms` | list | 虚空风暴（12 条） | 虚空风暴模块 |
| `DailyDeals` | list | 每日特惠（1 条） | 每日特惠模块 |
| `SeasonInfo` | dict | 夜波赛季信息 | 夜波模块 |
| `KnownCalendarSeasons` | list | 1999 日历赛季（1 条） | 1999 日历模块 |
| `Conquests` | list | 深层科研/时光科研（2 条） | 科研模块 |
| `Descents` | list | 双衍王境下降任务（5 条） | - |

### 商店与销售

| 字段 | 类型 | 说明 |
|------|------|------|
| `FlashSales` | list | 闪购商品（38 条） |
| `SkuSales` | list | SKU 销售商品 |
| `InGameMarket` | dict | 游戏内市场 |
| `PrimeAccessAvailability` | dict | Prime Access 可用性 |
| `PrimeVaultAvailabilities` | list | Prime 重生可用性（5 条） |
| `PrimeTokenAvailability` | bool | Prime Token 可用性 |
| `TwitchPromos` | list | Twitch 推广活动 |

### PVP 相关

| 字段 | 类型 | 说明 |
|------|------|------|
| `PVPChallengeInstances` | list | PVP 挑战任务（13 条） |
| `PVPAlternativeModes` | list | PVP 替代模式 |
| `PVPActiveTournaments` | list | PVP 活动锦标赛 |

### 其他系统

| 字段 | 类型 | 说明 |
|------|------|------|
| `GlobalUpgrades` | list | 全局增益（当前 0 条） |
| `HubEvents` | list | 中继站事件 |
| `NodeOverrides` | list | 节点覆盖配置（7 条） |
| `LibraryInfo` | dict | 中枢苏达图书馆信息 |
| `PersistentEnemies` | list | 持续出现的卓越者敌人 |
| `ProjectPct` | list | 项目进度百分比（3 项） |
| `ConstructionProjects` | list | 建设项目 |
| `ExperimentRecommended` | list | 实验推荐 |
| `EndlessXpChoices` | list | 无尽 XP 选择（2 条） |
| `EndlessXpSchedule` | list | 无尽 XP 时间表（1 条） |
| `FeaturedGuilds` | list | 精选氏族（8 条） |
| `Tmp` | string | 临时数据（JSON 字符串） |

---

## 主要数据结构详解

### 1. Sorties（突击任务）

```json
{
  "_id": {"$oid": "..."},
  "Activation": {"$date": {"$numberLong": "..."}},
  "Expiry": {"$date": {"$numberLong": "..."}},
  "Boss": "SORTIE_BOSS_HEK",
  "MissionCount": 3,
  "Variants": [
    {
      "bossTag": "...",
      "modifierType": "...",
      "node": "SolNode...",
      "missionType": "MT_..."
    }
  ],
  "Reward": "/Lotus/Types/..."
}
```

### 1.1 LiteSorties（执行官突击）

> 与普通突击（Sorties）不同，执行官突击每周刷新一次，挑战一位执行官 Boss，包含 3 个固定任务，无 modifier（无任务修饰符）。

```json
{
  "_id": {"$oid": "..."},
  "Activation": {"$date": {"$numberLong": "..."}},
  "Expiry": {"$date": {"$numberLong": "..."}},
  "Reward": "/Lotus/Types/Game/MissionDecks/ArchonSortieRewards",
  "Seed": 93299,
  "Boss": "SORTIE_BOSS_AMAR",
  "Missions": [
    {
      "missionType": "MT_INTEL",
      "node": "SolNode16"
    },
    {
      "missionType": "MT_EXCAVATE",
      "node": "SolNode11"
    },
    {
      "missionType": "MT_ASSASSINATION",
      "node": "SolNode99"
    }
  ]
}
```

**与 Sorties 的主要差异：**

| 字段 | Sorties（突击） | LiteSorties（执行官突击） |
|------|-----------------|--------------------------|
| `Boss` | 普通Boss（如海克、Lech Kril） | 执行官（Amar/Boreal/Nira等） |
| 任务列表字段 | `Variants` | `Missions` |
| 任务修饰符 | 有 `modifierType` | 无 |
| `MissionCount` | 有 | 无 |
| `Seed` | 无 | 有 |
| 奖励池 | 普通突击奖励 | `ArchonSortieRewards`（执行官塑形石） |
| 刷新频率 | 每日 | 每周 |

**执行官 Boss 代码映射：**
- `SORTIE_BOSS_AMAR` → Amar（炽焰）
- `SORTIE_BOSS_BOREAL` → Boreal（寒冰）
- `SORTIE_BOSS_NIRA` → Nira（毒素）
- `SORTIE_BOSS_SYNTHID` → Synthid（腐蚀）

### 2. VoidTraders（虚空商人）

```json
{
  "_id": {"$oid": "..."},
  "Activation": {"$date": {"$numberLong": "..."}},
  "Expiry": {"$date": {"$numberLong": "..."}},
  "Character": "Baro'Ki Teel",
  "Node": "MercuryHUB",
  "Manifest": [
    {
      "ItemType": "/Lotus/StoreItems/...",
      "PrimePrice": 450,
      "RegularPrice": 300000,
      "Limit": 1
    }
  ]
}
```

### 3. PrimeVaultTraders（Prime 重生商人）

```json
{
  "_id": {"$oid": "..."},
  "Activation": {"$date": {"$numberLong": "..."}},
  "InitialStartDate": {"$date": {"$numberLong": "..."}},
  "Node": "TradeHUB1",
  "Manifest": [
    {
      "ItemType": "/Lotus/Types/StoreItems/...",
      "PrimePrice": 6
    }
  ],
  "Expiry": {"$date": {"$numberLong": "..."}},
  "FeaturedItems": [
    {
      "Expiry": {"$date": {"$numberLong": "..."}},
      "PreviewHiddenUntil": {"$date": {"$numberLong": "..."}},
      "FeaturedItem": "/Lotus/Types/StoreItems/..."
    }
  ]
}
```

### 4. Invasions（入侵活动）

```json
{
  "_id": {"$oid": "..."},
  "Faction": "FC_CORPUS",
  "DefenderFaction": "FC_GRINEER",
  "Node": "SolNode96",
  "Count": -32280,
  "Goal": 100000,
  "LocTag": "/Lotus/Language/Menu/CorpusInvasionGeneric",
  "Completed": false,
  "ChainID": {"$oid": "..."},
  "AttackerReward": {
    "countedItems": [
      {
        "ItemType": "/Lotus/Types/Recipes/...",
        "ItemCount": 1
      }
    ]
  },
  "DefenderReward": {
    "countedItems": [
      {
        "ItemType": "/Lotus/Types/Recipes/...",
        "ItemCount": 1
      }
    ]
  },
  "Activation": {"$date": {"$numberLong": "..."}}
}
```

**阵营代码映射：**
- `FC_GRINEER` → 克隆尼
- `FC_CORPUS` → 科普斯
- `FC_INFESTATION` → 感染者
- `FC_TENNO` → 天诺
- `FC_SENTIENT` → Sentient

### 5. ActiveMissions（虚空裂缝）

```json
{
  "_id": {"$oid": "..."},
  "Activation": {"$date": {"$numberLong": "..."}},
  "Expiry": {"$date": {"$numberLong": "..."}},
  "Node": "SolNode...",
  "MissionType": "MT_...",
  "Modifier": "VoidT1",
  "Hard": false,
  "isStorm": false,
  "Faction": "FC_..."
}
```

**裂缝纪元（Modifier）：**
- `VoidT1` → 古纪
- `VoidT2` → 前纪
- `VoidT3` → 中纪
- `VoidT4` → 后纪
- `VoidT5` → 安魂
- `VoidT6` → 全能
- `VoidT7` → 特殊

### 6. DailyDeals（每日特惠）

```json
{
  "_id": {"$oid": "..."},
  "Activation": {"$date": {"$numberLong": "..."}},
  "Expiry": {"$date": {"$numberLong": "..."}},
  "StoreItem": "/Lotus/StoreItems/...",
  "OriginalPrice": 200,
  "SalePrice": 100,
  "Total": 10,
  "Sold": 3
}
```

### 7. SeasonInfo（夜波赛季）

```json
{
  "_id": {"$oid": "..."},
  "Activation": {"$date": {"$numberLong": "..."}},
  "Expiry": {"$date": {"$numberLong": "..."}},
  "Season": 14,
  "Phase": "...",
  "Params": {
    "ChallengeTypes": [...],
    "AffiliationTag": "..."
  },
  "ActiveChallenges": [
    {
      "_id": {"$oid": "..."},
      "Daily": true,
      "Activation": {"$date": {"$numberLong": "..."}},
      "Expiry": {"$date": {"$numberLong": "..."}},
      "Challenge": "/Lotus/Types/..."
    }
  ]
}
```

### 8. SyndicateMissions（集团任务）

```json
{
  "_id": {"$oid": "..."},
  "Activation": {"$date": {"$numberLong": "..."}},
  "Expiry": {"$date": {"$numberLong": "..."}},
  "Tag": "ArbitersSyndicate",
  "Seed": 12345,
  "Nodes": ["SolNode1", "SolNode2", "..."]
}
```

**集团代码映射：**
- `ArbitersSyndicate` → 仲裁者
- `CephalonSudaSyndicate` → 中枢苏达
- `SteelMeridianSyndicate` → 钢铁防线
- `RedVeilSyndicate` → 赤毒面纱
- `NewLokaSyndicate` → 新世间
- `OstronSyndicate` → 奥斯特（殁世幽都）
- `SolarisUnitedSyndicate` → 索拉里斯联合（福尔图娜）
- `VoxSolarisSyndicate` → 索拉里斯之声
- `EntratiSyndicate` → 英择谛（魔胎之境）
- `CavaleroSyndicate` → 卡瓦莱罗（双衍王境）
- 等级2:12～17
- 等级3:20～25
- 等级4:25～30
- 等级5:30～35

### 9. VoidStorms（虚空风暴）

```json
{
  "_id": {"$oid": "..."},
  "Activation": {"$date": {"$numberLong": "..."}},
  "Expiry": {"$date": {"$numberLong": "..."}},
  "Node": "SolNode...",
  "ActiveMissionTier": "VoidT1",
  "MissionType": "MT_...",
  "Faction": "FC_..."
}
```

### 10. Conquests（科研任务）

```json
{
  "_id": {"$oid": "..."},
  "Activation": {"$date": {"$numberLong": "..."}},
  "Expiry": {"$date": {"$numberLong": "..."}},
  "QuestItem": "...",
  "Tasks": [...],
  "Reward": "..."
}
```

---

## 通用字段说明

### 时间戳格式

所有时间字段使用 MongoDB 风格的日期格式：

```json
{"$date": {"$numberLong": "1781659710000"}}
```

- `$numberLong` 为 Unix 毫秒时间戳的字符串形式
- 转换为可读时间: `datetime.fromtimestamp(int(numberLong) / 1000)`

### ID 格式

所有 `_id` 字段使用 MongoDB ObjectId 格式：

```json
{"$oid": "5d1e07a0a17c9a0d5b8ce5b2"}
```

### 物品路径

物品类型使用游戏内路径标识：

```
/Lotus/Types/StoreItems/Weapons/Corpus/LongGuns/CrpShockRifle/QuantaVandal
```

- 最后一段为物品英文名（如 `QuantaVandal`）
- 通过 `ITEM_NAME_MAP` 映射为中文名

---

## 数据获取方式

### Python 直接请求

```python
import urllib.request
import json

req = urllib.request.Request(
    "https://api.warframe.com/cdn/worldState.php",
    headers={"User-Agent": "Warframe-Chaiframe/2.0"}
)
with urllib.request.urlopen(req, timeout=15) as response:
    data = json.loads(response.read().decode("utf-8"))
```

### 使用 curl（备用方案）

```bash
curl -s -o worldstate_raw.json "https://api.warframe.com/cdn/worldState.php"
```

### 本地缓存

- 原始数据文件: `worldstate_raw.json`
- 缓存策略: 每次调用实时请求，不做持久缓存
- 缓存有效期: 官方建议 60 秒内不重复请求

---

## 注意事项

1. **字段变化**: 官方可能随时调整字段结构，需同步更新解析逻辑
2. **空数据处理**: 部分字段可能为空数组（如 `Alerts`），需做空值判断
3. **时区处理**: 时间戳为 UTC，显示时需转换为本地时区
4. **编码处理**: 数据使用 UTF-8 编码，包含多语言文本
5. **数据量**: 完整数据约 137KB，包含约 60+ 个顶层字段
