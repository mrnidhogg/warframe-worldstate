---
name: Warframe World State 查询
description: 获取 Warframe 官方实时游戏状态数据，统一输出中文情报摘要。支持查询突击、商人、仲裁、裂缝、入侵、虚空风暴、警报、每日特惠、夜波、集团任务、公告、Prime重生等多种游戏内活动信息。
version: 1.0
author: Warframe World State Team
tags:
  - Warframe
  - 游戏状态
  - 实时数据
  - 突击
  - 虚空商人
  - 仲裁
  - 裂缝
---

# Warframe World State 查询

获取 Warframe 官方实时游戏状态数据，统一输出中文情报摘要。

## 主入口
- 可执行脚本: `worldstate`
- 共享核心: `worldstate_core.py`

## API 端点
- **World State**: `https://api.warframe.com/cdn/worldState.php`

## 支持的查询类型

| 命令 | 功能 |
|------|------|
| `状态` 或 `worldstate` | 查看完整实时状态概览 |
| `突击` 或 `sortie` | 查看今日突击任务 |
| `Baro`、`商人` 或 `voidtrader` | 查看虚空商人位置、时间与库存 |
| `仲裁` 或 `arbitration` | 查看当前仲裁任务（官方未返回时说明） |
| `裂缝` 或 `fissure` | 查看当前普通/钢铁之路虚空裂缝 |
| `入侵` 或 `invasion` | 查看当前入侵活动与奖励 |
| `虚空风暴` 或 `voidstorms` | 查看当前虚空风暴任务 |
| `警报` 或 `alerts` | 查看当前警报任务 |
| `每日特惠` 或 `dailydeals` | 查看每日特惠商品 |
| `夜波`、`nightwave` 或 `season` | 查看当前赛季/夜波信息 |
| `集团任务` 或 `syndicates` | 查看当前集团任务 |
| `公告`、`新闻` 或 `events` | 查看经过筛选的轻量公告/新闻 |
| `Prime重生`、`重生商店` 或 `primevault` | 查看 Prime 重生商店原始数据 |
| `活动目标`、`目标活动` 或 `goals` | 查看当前活动目标原始数据 |
| `科研`、`科研任务` 或 `conquests` | 查看深层科研/时光科研原始数据 |
| `1999日历`、`日历赛季` 或 `calendar` | 查看 1999 日历赛季原始数据 |

## 默认行为
- 不传参数时，默认执行 `状态`
- 单项查询返回对应模块化结果
- 输出固定包含标题、核心字段，以及数据来源说明

## 失败与空数据
- API 拉取失败时返回可读错误，不抛出 traceback
- 某类活动当前为空时，返回对应“当前无任务/未公布”提示
- 裂缝结果会统一做任务类型、纪元、区域中文映射

## 使用示例
- `./worldstate`
- `./worldstate 状态`
- `./worldstate 突击`
- `./worldstate 裂缝`
- `./worldstate 商人`
- `./worldstate 入侵`
- `./worldstate 仲裁`
- `./worldstate 虚空风暴`
- `./worldstate 警报`
- `./worldstate 每日特惠`
- `./worldstate 夜波`
- `./worldstate 集团任务`
- `./worldstate 公告`
- `./worldstate Prime重生`
- `./worldstate 活动目标`
- `./worldstate 科研`
- `./worldstate 1999日历`

## 数据来源与限制
- 官方 API: `api.warframe.com`
- 每次调用实时请求，不做持久缓存
- 输出内容依赖官方 worldstate 字段，若官方字段结构变化需要同步调整解析逻辑
