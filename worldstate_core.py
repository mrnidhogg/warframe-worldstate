#!/usr/bin/env python3
"""
Warframe World State 查询核心逻辑
API: https://api.warframe.com/cdn/worldState.php
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from fissure_mapping import (
    ENTRATI_LAB_SYNDICATES,
    HEX_SYNDICATES,
    ITEM_NAME_MAP,
    MISSION_TYPE_MAP,
    NORMAL_PLANETS,
    NODE_METADATA,
    PLAINS_SYNDICATES,
    PLANET_NAME_FALLBACKS,
    RADIO_LEGION_SYNDICATES,
    SPECIAL_NODE_MAP,
    SORT_MODIFIER_TYPE_MAP,
    STANDARD_SYNDICATES,
    STEEL_PLANETS,
    SYNDICATE_NAMES,
    TIER_MAP,
    TIER_ORDER,
    ZARIMAN_SYNDICATES,
)

API_URL = "https://api.warframe.com/cdn/worldState.php"
ARBITRATION_SCHEDULE_URL = "https://browse.wf/arbys.txt"
NODE_EXPORT_URL = "https://unpkg.com/warframe-items@latest/data/json/Node.json"
USER_AGENT = "Warframe-Chaiframe/2.0"
DATA_SOURCE = "api.warframe.com"
MAX_EVENT_ITEMS = 5

BOSS_NAMES = {
    "SORTIE_BOSS_ALAD": "Alad V",
    "SORTIE_BOSS_AMBULAS": "Ambulas",
    "SORTIE_BOSS_CORRUPTED_VOR": "Corrupted Vor（缺翻译）",
    "SORTIE_BOSS_HEK": "韦•海克议员",
    "SORTIE_BOSS_HYENA": "Hyena（缺翻译）",
    "SORTIE_BOSS_KELA": "Kela De Thaym",
    "SORTIE_BOSS_LEPHANTIS": "雷凡魔像",
    "SORTIE_BOSS_NEF": "奈富安尤",
    "SORTIE_BOSS_PHORID": "Phorid",
    "SORTIE_BOSS_RAPTOR": "猛禽",
    "SORTIE_BOSS_RUK": "Ruk",
    "SORTIE_BOSS_VOR": "沃尔上尉",
    
}

# 执行官突击 Boss 映射
ARCHON_BOSS_NAMES = {
    "SORTIE_BOSS_AMAR": "Amar（炽焰执行官）",
    "SORTIE_BOSS_BOREAL": "Boreal（寒冰执行官）",
    "SORTIE_BOSS_NIRA": "Nira（毒素执行官）",
    "SORTIE_BOSS_SYNTHID": "Synthid（腐蚀执行官）",
}

NODE_FACTION_INDEX_MAP = {
    0: "克隆尼",
    1: "科普斯",
    2: "感染者",
    3: "Orokin",
    4: "Sentient",
}

NODE_MISSION_INDEX_MAP = {
    0: "刺杀",
    1: "歼灭",
    2: "生存",
    3: "捕获",
    4: "破坏",
    5: "移动防御",
    7: "间谍",
    8: "防御",
    9: "救援",
    13: "拦截",
    14: "劫持",
    15: "清巢",
    17: "挖掘",
    21: "感染清巢",
    24: "追击",
    25: "突袭",
    26: "强袭",
    27: "叛逃",
    28: "自由漫游",
    32: "中断",
}

NODE_DESCRIPTIONS = {
    "SolNode12": "韦•海克议员 控制的一个远程设施发现有受损的情报网络。已将数据块送至Elion；取得数据块并将内容上传到现场的终端当中。",
    "SolNode24": "待补充。",
    "SolNode41": "待补充。",
    "SolNode45": "待补充。",
    "SolNode64": "待补充。",
    "SolNode79": "待补充。",
    "SolNode82": "侦查Stofler的时候发现沃尔上尉在Calypso使用实验性的导管技术来藏匿偷窃来的资源，通过Little Duck的协助将这些物品取回。",
    "SolNode101": "猛禽的爪牙在Paimon的瓦解使得我们得以入侵位于Killken的资料网络。我们的资料块已经部署在该地点，找到它们并覆写终端机。",
    "SolNode108": "待补充。",
    "SolNode177": "待补充。",
    "SolNode212": "位于Paimon一座由猛禽所把持的装配工厂内部发现一组高规格能量核心原件。为了达成我们的目标前往回收它。",
    "SolNode305": "位于Stofler发现一支沃尔上尉的先锋部队。在后援抵达前歼灭这波威胁。",
}


def get_map_description(node_name: str) -> str:
    return NODE_DESCRIPTIONS.get(node_name, "")




def get_first(mapping: Optional[Dict[str, Any]], *keys: str, default: Any = None) -> Any:
    if not isinstance(mapping, dict):
        return default
    for key in keys:
        if key in mapping and mapping[key] not in (None, ""):
            return mapping[key]
    return default


def ts_to_date(value: Any) -> str:
    if isinstance(value, dict) and "$date" in value:
        date_value = value["$date"]
        if isinstance(date_value, dict) and "$numberLong" in date_value:
            value = int(date_value["$numberLong"]) / 1000
        elif isinstance(date_value, (int, float)):
            value = date_value / 1000
    elif isinstance(value, str) and value.isdigit():
        value = int(value) / 1000

    if isinstance(value, (int, float)) and value > 0:
        return datetime.fromtimestamp(value).strftime("%m-%d %H:%M")
    return "N/A"


def timestamp_to_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, dict) and "$date" in value:
        date_value = value["$date"]
        if isinstance(date_value, dict) and "$numberLong" in date_value:
            value = int(date_value["$numberLong"]) / 1000
        elif isinstance(date_value, (int, float)):
            value = date_value / 1000
    elif isinstance(value, str) and value.isdigit():
        value = int(value) / 1000

    if isinstance(value, (int, float)) and value > 0:
        return datetime.fromtimestamp(value)
    return None


def clean_item_name(item_type: Any) -> str:
    if not item_type:
        return "N/A"
    if isinstance(item_type, str) and "/" in item_type:
        return item_type.split("/")[-1]
    return str(item_type)


def translate_item_name(item_type: Any) -> str:
    raw_name = clean_item_name(item_type)
    return ITEM_NAME_MAP.get(raw_name, raw_name)


def mission_type_name(mission_type: Any) -> str:
    if not mission_type:
        return "N/A"
    mission_type = str(mission_type)
    return MISSION_TYPE_MAP.get(mission_type, mission_type.replace("MT_", ""))


def tier_name(modifier: Any) -> str:
    if not modifier:
        return "未知"
    modifier = str(modifier)
    return TIER_MAP.get(modifier, modifier)


def extract_numeric_region(node: str) -> Optional[int]:
    if not isinstance(node, str):
        return None
    if "SolNode" not in node:
        return None
    digits = "".join(ch for ch in node if ch.isdigit())
    return int(digits) if digits else None


def normalize_planet_name(node: Any, hard: bool = False) -> str:
    if not isinstance(node, str) or not node:
        return "未知区域"

    region = extract_numeric_region(node)
    mapping = STEEL_PLANETS if hard else NORMAL_PLANETS
    if region is not None and region in mapping:
        return mapping[region]

    if "/" in node:
        left = node.split("/", 1)[0].strip()
        return PLANET_NAME_FALLBACKS.get(left, left)

    return PLANET_NAME_FALLBACKS.get(node, node)


def normalize_node_name(node: Any, hard: bool = False) -> str:
    if not isinstance(node, str) or not node:
        return "N/A"

    fallback = PLANET_NAME_FALLBACKS.get(node)
    if fallback:
        return fallback

    if "/" in node:
        left, right = node.split("/", 1)
        left_cn = PLANET_NAME_FALLBACKS.get(left.strip(), left.strip())
        return f"{left_cn} / {right.strip()}"

    for prefix, cn_name in SPECIAL_NODE_MAP.items():
        if node.startswith(prefix):
            return cn_name

    region = extract_numeric_region(node)
    if region is not None:
        return normalize_planet_name(node, hard=hard)

    return node.replace("_", " ")


def format_sortie_node_label(node: Any) -> str:
    if isinstance(node, str):
        metadata = NODE_METADATA.get(node)
        if metadata:
            return f"{metadata['name']} - {metadata['planet']}"
    normalized = normalize_node_name(node)
    if " - " in normalized:
        planet, location = normalized.split(" - ", 1)
        return f"{location} - {planet}"
    return normalized


def format_fissure_node_label(node: Any) -> str:
    if isinstance(node, str):
        metadata = NODE_METADATA.get(node)
        if metadata:
            return f"{metadata['name']} - {metadata['planet']}"
    return normalize_node_name(node)


def format_node_label(node: Any) -> str:
    if isinstance(node, str):
        metadata = NODE_METADATA.get(node)
        if metadata:
            name = metadata.get("name")
            planet = metadata.get("planet")
            if name and planet and name != node and planet != "***":
                return f"{name} - {planet}"
    return normalize_node_name(node)


def format_remaining(expiry: Any) -> str:
    dt = timestamp_to_datetime(expiry)
    if not dt:
        return "N/A"
    delta = dt - datetime.now()
    total_seconds = int(delta.total_seconds())
    if total_seconds <= 0:
        return "已结束"
    minutes = total_seconds // 60
    hours, mins = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}小时{mins}分钟"
    return f"{mins}分钟"


def reward_lines(reward: Any) -> List[str]:
    lines: List[str] = []
    if isinstance(reward, dict):
        counted = reward.get("countedItems", [])
        for item in counted:
            item_name = translate_item_name(get_first(item, "ItemType", "itemType"))
            qty = get_first(item, "ItemCount", "itemCount", default=1)
            lines.append(f"{item_name} x{qty}")

        items = reward.get("items", [])
        for item in items:
            lines.append(translate_item_name(item))

        credits = reward.get("credits")
        if credits:
            lines.append(f"{credits} 现金")

        as_string = get_first(reward, "typeString", "TypeString")
        if as_string and not lines:
            lines.append(str(as_string))
    return lines


def extract_event_title(messages: Any) -> str:
    if not isinstance(messages, list):
        return "N/A"

    preferred_languages = ("zh", "tc", "en")
    for lang in preferred_languages:
        for message in messages:
            if message.get("LanguageCode") == lang and message.get("Message"):
                return str(message["Message"]).strip()

    for message in messages:
        if message.get("Message"):
            return str(message["Message"]).strip()
    return "N/A"


def event_sort_key(event: Dict[str, Any]) -> datetime:
    for key in ("EventStartDate", "EventEndDate", "Date"):
        dt = timestamp_to_datetime(event.get(key))
        if dt:
            return dt
    return datetime.min


def is_useful_event(title: str, prop: str, event: Dict[str, Any]) -> bool:
    text = f"{title} {prop}".lower()
    useful_keywords = (
        "operation",
        "devstream",
        "twitch drop",
        "twitch drops",
        "prime access",
        "prime resurgence",
        "tennocon",
    )
    if any(keyword in text for keyword in useful_keywords):
        return True

    if event.get("EventStartDate") or event.get("EventEndDate"):
        return True

    noisy_keywords = (
        "discord",
        "wiki",
        "forums",
        "forum",
        "code of conduct",
        "community updates page",
        "known bugs tracker",
        "known issues",
        "official x account",
        "bluesky",
    )
    return not any(keyword in text for keyword in noisy_keywords)


def event_topic_key(title: str, prop: str) -> str:
    text = f"{title} {prop}".lower()

    devstream_match = re.search(r"devstream[^0-9]*(\d+)", text)
    if devstream_match:
        return f"devstream-{devstream_match.group(1)}"

    if "belly of the beast" in text:
        return "operation-belly-of-the-beast"
    if "twitch drop" in text or "twitch drops" in text:
        return "community-twitch-drops"
    if "prime resurgence" in text or ("nyx prime" in text and "rhino prime" in text):
        return "prime-resurgence-nyx-rhino"
    if "voruna prime access" in text or "prime access voruna" in text:
        return "voruna-prime-access"
    if "tennocon" in text and "digital pack" in text:
        return "tennocon-digital-pack"
    if "tennocon" in text and "merch pack" in text:
        return "tennocon-merch-pack"
    return ""


def footer_lines() -> List[str]:
    return ["", f"📡 数据来源: {DATA_SOURCE}"]


def render_section(title: str, body_lines: Iterable[str], empty_line: str) -> str:
    lines = [title]
    lines.extend(body_lines)
    if len(lines) == 1:
        lines.append(empty_line)
    lines.extend(footer_lines())
    return "\n".join(lines)


def fetch_worldstate() -> Dict[str, Any]:
    try:
        req = urllib.request.Request(API_URL, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        result = subprocess.run(
            ["curl", "-s", "-L", "-H", f"User-Agent: {USER_AGENT}", API_URL],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        raise


def fetch_text(url: str) -> str:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode("utf-8")
    except Exception:
        result = subprocess.run(
            ["curl", "-s", "-L", "-H", f"User-Agent: {USER_AGENT}", url],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return result.stdout
        raise


def fetch_json(url: str) -> Any:
    return json.loads(fetch_text(url))


def node_export_entry(node_id: str) -> Dict[str, Any]:
    if not node_id:
        return {}
    try:
        nodes = fetch_json(NODE_EXPORT_URL)
    except (urllib.error.URLError, TimeoutError, ValueError):
        return {}
    if not isinstance(nodes, list):
        return {}
    for node in nodes:
        if isinstance(node, dict) and node.get("uniqueName") == node_id:
            return node
    return {}


def parse_arbitration_schedule() -> Optional[Dict[str, Any]]:
    local_file = "arbys.txt"
    raw_schedule = None

    if os.path.exists(local_file):
        try:
            with open(local_file, "r") as f:
                raw_schedule = f.read()
        except (IOError, OSError):
            pass

    if not raw_schedule:
        try:
            raw_schedule = fetch_text(ARBITRATION_SCHEDULE_URL)
        except (urllib.error.URLError, TimeoutError, ValueError):
            return None

    entries = []
    for line in raw_schedule.splitlines():
        line = line.strip()
        if not line or "," not in line:
            continue
        timestamp_text, node_id = line.split(",", 1)
        try:
            timestamp = int(timestamp_text)
        except ValueError:
            continue
        entries.append((timestamp, node_id.strip()))

    if not entries:
        return None

    entries.sort()
    now = int(time.time())
    current = None
    next_timestamp = None
    for index, (timestamp, node_id) in enumerate(entries):
        if timestamp <= now and (index + 1 == len(entries) or entries[index + 1][0] > now):
            current = (timestamp, node_id)
            next_timestamp = entries[index + 1][0] if index + 1 < len(entries) else timestamp + 3600
            break
    if not current:
        return None

    activation, node_id = current
    exported = node_export_entry(node_id)
    planet = PLANET_NAME_FALLBACKS.get(exported.get("systemName"), exported.get("systemName", "N/A"))
    node_name = exported.get("name") or node_id
    mission_type = NODE_MISSION_INDEX_MAP.get(exported.get("missionIndex"), "N/A")
    enemy = NODE_FACTION_INDEX_MAP.get(exported.get("factionIndex"), "N/A")

    source = "本地 arbys.txt" if os.path.exists(local_file) else "browse.wf/arbys.txt"
    return {
        "node": f"{node_name} - {planet}" if planet != "N/A" else node_name,
        "mission_type": mission_type,
        "enemy": enemy,
        "reward": [],
        "activation": datetime.fromtimestamp(activation).strftime("%Y-%m-%d %H:%M:%S"),
        "expiry": datetime.fromtimestamp(next_timestamp).strftime("%Y-%m-%d %H:%M:%S"),
        "source": f"{source} + warframe-items Node.json",
    }


def parse_baro(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    traders = get_first(data, "VoidTraders", default=[])
    if not traders:
        return None

    trader = traders[0]
    manifest = []
    for item in get_first(trader, "Manifest", default=[]):
        item_type = get_first(item, "ItemType", "itemType")
        manifest.append(
            {
                "name": translate_item_name(item_type),
                "prime_price": get_first(item, "PrimePrice"),
                "regular_price": get_first(item, "RegularPrice"),
                "limit": get_first(item, "Limit"),
            }
        )

    return {
        "location": normalize_node_name(get_first(trader, "Node", "Location", default="N/A")),
        "activation": ts_to_date(get_first(trader, "Activation")),
        "expiry": ts_to_date(get_first(trader, "Expiry")),
        "manifest": manifest,
    }


def parse_sortie(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    sorties = get_first(data, "Sorties", default=[])
    if not sorties:
        return None

    sortie = sorties[0]
    boss = get_first(sortie, "Boss")
    if not boss:
        return None

    variants = []
    for variant in get_first(sortie, "Variants", default=[]):
        modifier_type = get_first(variant, "modifierType", "ModifierType", default="")
        modifier_info = SORT_MODIFIER_TYPE_MAP.get(modifier_type, {})
        modifier = modifier_info.get("name", modifier_type)
        modifier_description = modifier_info.get("description", "")
        
        if not modifier:
            modifier = get_first(
                variant,
                "modifier",
                "Modifier",
                default=get_first(
                    get_first(variant, "missionReward", "MissionReward", default={}),
                    "typeString",
                    "TypeString",
                    default="",
                ),
            )
        
        node_name = get_first(variant, "node", "Node", default="N/A")
        
        node_description = ""
        if node_name:
            node_description = get_map_description(node_name)
        
        variants.append(
            {
                "node": format_sortie_node_label(node_name),
                "mission_type": mission_type_name(
                    get_first(variant, "missionType", "MissionType", default="N/A")
                ),
                "modifier": modifier,
                "node_description": node_description,
                "modifier_description": modifier_description,
            }
        )

    return {
        "boss": BOSS_NAMES.get(str(boss), str(boss).replace("SORTIE_BOSS_", "").replace("_", " ")),
        "variety": get_first(sortie, "Variety", default=""),
        "variants": variants,
    }


def parse_archon_sortie(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """解析执行官突击（LiteSorties）数据"""
    lite_sorties = get_first(data, "LiteSorties", default=[])
    if not lite_sorties:
        return None

    sortie = lite_sorties[0]
    boss = get_first(sortie, "Boss")
    if not boss:
        return None

    missions = []
    for mission in get_first(sortie, "Missions", default=[]):
        node_name = get_first(mission, "node", "Node", default="N/A")
        node_description = get_map_description(node_name) if node_name else ""

        missions.append(
            {
                "node": format_sortie_node_label(node_name),
                "mission_type": mission_type_name(
                    get_first(mission, "missionType", "MissionType", default="N/A")
                ),
                "node_description": node_description,
            }
        )

    return {
        "boss": ARCHON_BOSS_NAMES.get(
            str(boss), str(boss).replace("SORTIE_BOSS_", "").replace("_", " ")
        ),
        "seed": get_first(sortie, "Seed", default=0),
        "missions": missions,
        "activation": ts_to_date(get_first(sortie, "Activation")),
        "expiry": ts_to_date(get_first(sortie, "Expiry")),
    }


def parse_arbitration(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    arbitration = get_first(data, "Arbitration", default={})
    if not arbitration:
        return None

    reward = get_first(arbitration, "reward", "Reward", default={})
    return {
        "node": normalize_node_name(get_first(arbitration, "node", "Node", default="N/A")),
        "mission_type": mission_type_name(
            get_first(arbitration, "missionType", "MissionType", default="N/A")
        ),
        "enemy": get_first(arbitration, "enemy", "Enemy", default="N/A"),
        "reward": reward_lines(reward),
    }


def parse_fissures(data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    missions = get_first(data, "ActiveMissions", default=[])
    grouped = {"normal": [], "steel": []}

    for mission in missions:
        if get_first(mission, "isStorm", "IsStorm", default=False):
            continue

        hard = bool(get_first(mission, "Hard", "hard", default=False))
        modifier = get_first(mission, "Modifier", "modifier", default="VoidT1")
        node_id = get_first(mission, "Node", "node", default="")
        metadata = NODE_METADATA.get(node_id, {})
        parsed = {
            "planet": normalize_planet_name(node_id, hard=hard),
            "node": format_fissure_node_label(node_id),
            "mission_type": metadata.get(
                "mission",
                mission_type_name(get_first(mission, "MissionType", "missionType", default="N/A")),
            ),
            "tier": tier_name(modifier),
            "tier_order": TIER_ORDER.get(str(modifier), 99),
            "faction": metadata.get("faction", ""),
            "level": metadata.get("hardlevel" if hard else "level", ""),
            "remaining": format_remaining(get_first(mission, "Expiry")),
        }
        grouped["steel" if hard else "normal"].append(parsed)

    for bucket in grouped.values():
        bucket.sort(key=lambda item: (item["tier_order"], item["planet"], item["mission_type"], item["node"]))
    return grouped


FACTION_MAP = {
    "FC_GRINEER": "克隆尼",
    "FC_CORPUS": "科普斯",
    "FC_INFESTATION": "感染者",
    "FC_TENNO": "天诺",
    "FC_SENTIENT": "Sentient",
    "Grineer": "克隆尼",
    "Corpus": "科普斯",
    "Infestation": "感染者",
    "Infested": "感染者",
    "并合 Corpus": "并合科普斯",
}


INVASION_LOC_TAG_MAP = {
    "/Lotus/Language/Menu/CorpusInvasionGeneric": "科普斯入侵",
    "/Lotus/Language/Menu/GrineerInvasionGeneric": "克隆尼入侵",
    "/Lotus/Language/Menu/InfestedInvasionGeneric": "感染者入侵",
    "/Lotus/Language/Menu/InfestedInvasionBoss": "感染者刺杀入侵",
    "/Lotus/Language/Menu/InvasionGeneric": "入侵",
}


def faction_name(faction: Any) -> str:
    if not faction:
        return "未知"
    faction = str(faction)
    return FACTION_MAP.get(faction, faction.replace("FC_", "").title())


def invasion_type_name(loc_tag: Any) -> str:
    if not loc_tag:
        return "入侵"
    loc_tag = str(loc_tag)
    return INVASION_LOC_TAG_MAP.get(loc_tag, loc_tag.rsplit("/", 1)[-1])


def invasion_side_info(info: Any) -> Dict[str, Any]:
    if not isinstance(info, dict):
        return {"enemy_faction": "未知", "seed": None}
    return {
        "enemy_faction": faction_name(get_first(info, "faction", "Faction", default="")),
        "seed": get_first(info, "seed", "Seed"),
    }


def parse_invasions(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    invasions = []
    for invasion in get_first(data, "Invasions", default=[]):
        attacker_reward = get_first(invasion, "AttackerReward", "attackerReward", default={})
        defender_reward = get_first(invasion, "DefenderReward", "defenderReward", default={})
        count = get_first(invasion, "Count", "count", default=0) or 0
        goal = get_first(invasion, "Goal", "goal", default=0) or 0
        completed = get_first(invasion, "Completed", "completed", default=False)
        
        if completed:
            progress = 100
        elif goal:
            progress = max(0, min(100, int(abs(count) / goal * 100)))
        else:
            progress = 0
            
        node_id = get_first(invasion, "Node", "node", default="N/A")
        metadata = NODE_METADATA.get(node_id, {}) if isinstance(node_id, str) else {}
        attacker_faction = faction_name(get_first(invasion, "Faction", default=""))
        defender_faction = faction_name(get_first(invasion, "DefenderFaction", default=""))
        
        invasions.append(
            {
                "node": format_node_label(node_id),
                "node_id": node_id,
                "mission_type": metadata.get("mission", ""),
                "level": metadata.get("level", ""),
                "base_faction": faction_name(metadata.get("faction", "")),
                "invasion_type": invasion_type_name(get_first(invasion, "LocTag", "locTag", default="")),
                "attacker_faction": attacker_faction,
                "defender_faction": defender_faction,
                "attacker_mission": invasion_side_info(
                    get_first(invasion, "AttackerMissionInfo", "attackerMissionInfo", default={})
                ),
                "defender_mission": invasion_side_info(
                    get_first(invasion, "DefenderMissionInfo", "defenderMissionInfo", default={})
                ),
                "attacker": reward_lines(attacker_reward),
                "defender": reward_lines(defender_reward),
                "completed": completed,
                "progress": progress,
                "count": count,
                "goal": goal,
                "activation": ts_to_date(get_first(invasion, "Activation")),
            }
        )
    return sorted(invasions, key=lambda item: (item["completed"], item["node"]))


def parse_void_storms(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    void_storms = []
    for storm in get_first(data, "VoidStorms", default=[]):
        void_storms.append(
            {
                "node": normalize_node_name(get_first(storm, "Node", "node", default="N/A")),
                "tier": tier_name(get_first(storm, "ActiveMissionTier", "activeMissionTier", default="VoidT1")),
                "activation": ts_to_date(get_first(storm, "Activation")),
                "expiry": ts_to_date(get_first(storm, "Expiry")),
            }
        )
    return void_storms


def parse_alerts(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    alerts = []
    for alert in get_first(data, "Alerts", default=[]):
        mission_info = get_first(alert, "MissionInfo", "missionInfo", default={})
        # 尝试从多个位置获取节点信息
        node = get_first(mission_info, "Node", "node", "location", "Location", default="N/A")
        # 清理节点名称
        if node == "N / A" or node == "N/A":
            # 尝试从其他位置获取
            node = get_first(alert, "Node", "node", "location", "Location", default="N/A")
        alerts.append(
            {
                "node": normalize_node_name(node),
                "mission_type": mission_type_name(
                    get_first(mission_info, "MissionType", "missionType", default="N/A")
                ),
                "activation": ts_to_date(get_first(alert, "Activation")),
                "expiry": ts_to_date(get_first(alert, "Expiry")),
                "reward": reward_lines(get_first(mission_info, "MissionReward", "missionReward", default={})),
            }
        )
    return alerts


def parse_daily_deals(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    daily_deals = []
    for deal in get_first(data, "DailyDeals", default=[]):
        daily_deals.append(
            {
                "item": clean_item_name(get_first(deal, "StoreItem", "storeItem")),
                "original_price": get_first(deal, "OriginalPrice", "originalPrice", default=0),
                "sale_price": get_first(deal, "SalePrice", "salePrice", default=0),
                "discount": get_first(deal, "Discount", "discount", default=0),
                "expiry": ts_to_date(get_first(deal, "Expiry")),
                "total": get_first(deal, "AmountTotal", "amountTotal", default=0),
                "sold": get_first(deal, "AmountSold", "amountSold", default=0),
            }
        )
    return daily_deals


def parse_season_info(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    season_info = get_first(data, "SeasonInfo", default={})
    if not season_info:
        return None

    active_challenges = get_first(season_info, "ActiveChallenges", "activeChallenges", default=[])
    challenge_count = len(active_challenges) if isinstance(active_challenges, list) else 0

    return {
        "season": get_first(season_info, "Season", "season", default="N/A"),
        "phase": get_first(season_info, "Phase", "phase", default="N/A"),
        "activation": ts_to_date(get_first(season_info, "Activation")),
        "expiry": ts_to_date(get_first(season_info, "Expiry")),
        "affiliation_tag": get_first(season_info, "AffiliationTag", "affiliationTag", default="N/A"),
        "active_challenges": challenge_count,
    }





def parse_syndicate_missions(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    syndicate_missions = []
    for mission in get_first(data, "SyndicateMissions", default=[]):
        # 尝试从多个位置获取节点信息
        nodes = get_first(mission, "Nodes", "nodes", default=[])
        node = "N/A"

        # 优先从 Nodes 数组获取
        if nodes:
            # 尝试所有节点，找到一个有效的
            for n in nodes:
                if n and n != "N/A" and n != "N / A":
                    node = n
                    break

        # 如果还是 N/A，尝试从其他位置获取
        if node == "N/A" or node == "N / A":
            node = get_first(mission, "Node", "node", "location", "Location", default="N/A")

        # 清理节点名称
        if node == "N/A" or node == "N / A":
            # 尝试从 mission 其他字段获取
            node = get_first(mission, "MissionInfo", "missionInfo", default={}).get("Node", "N/A")

        # 如果仍然无法获取节点，根据 syndicate tag 提供默认信息
        syndicate_tag = get_first(mission, "Tag", "tag", default="N/A")
        if node == "N/A" or node == "N / A":
            # 根据不同的集团提供更友好的默认信息
            syndicate_map = {
                "ArbitersSyndicate": "仲裁者 - 特殊任务",
                "CephalonSudaSyndicate": "中枢苏达 - 特殊任务",
                "SteelMeridianSyndicate": "钢铁防线 - 特殊任务",
                "RedVeilSyndicate": "赤毒面纱 - 特殊任务",
                "NewLokaSyndicate": "新世间 - 特殊任务",
                "OstronSyndicate": "奥斯特 - 殁世幽都",
                "SolarisUnitedSyndicate": "索拉里斯联合 - 福尔图娜",
                "VoxSolarisSyndicate": "索拉里斯之声 - 福尔图娜",
                "EntratiSyndicate": "英择谛 - 魔胎之境",
                "CavaleroSyndicate": "卡瓦莱罗 - 双衍王境",
                "RadioLegionSyndicate": "广播军团 - 特殊任务",
            }
            node = syndicate_map.get(syndicate_tag, f"{syndicate_tag} - 特殊任务")

        # 翻译集团名称
        syndicate_name = SYNDICATE_NAMES.get(
            syndicate_tag, syndicate_tag
        )

        # 处理所有节点（保留原始 ID，不提前调用 normalize_node_name）
        all_nodes = [
            n for n in nodes
            if n and n != "N/A" and n != "N / A"
        ] or [node if node != "N/A" else "N/A"]

        syndicate_missions.append(
            {
                "syndicate": syndicate_tag,
                "syndicate_name": syndicate_name,
                "node": normalize_node_name(node) if node != "N/A" else node,
                "nodes": all_nodes,
                "activation": ts_to_date(get_first(mission, "Activation")),
                "expiry": ts_to_date(get_first(mission, "Expiry")),
                "seed": get_first(mission, "Seed", "seed", default=0),
            }
        )
    return syndicate_missions


def parse_events(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    events = []
    seen_keys = set()

    for event in sorted(get_first(data, "Events", default=[]), key=event_sort_key, reverse=True):
        title = extract_event_title(get_first(event, "Messages", default=[]))
        prop = str(get_first(event, "Prop", default="") or "").strip()
        image_url = str(get_first(event, "ImageUrl", default="") or "").strip()
        live_url = str(get_first(event, "EventLiveUrl", default="") or "").strip()
        start = ts_to_date(get_first(event, "EventStartDate"))
        end = ts_to_date(get_first(event, "EventEndDate"))
        topic_key = event_topic_key(title, prop)

        dedupe_key = (
            topic_key
            or live_url
            or (f"{image_url}|{start}|{end}" if image_url and (start != "N/A" or end != "N/A") else "")
            or prop
            or title.lower()
        )
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)

        if not is_useful_event(title, prop, event):
            continue

        events.append(
            {
                "title": title,
                "link": prop or "N/A",
                "posted": ts_to_date(get_first(event, "Date")),
                "start": start,
                "end": end,
                "live": live_url,
            }
        )

        if len(events) >= MAX_EVENT_ITEMS:
            break

    return events


def format_baro(data: Dict[str, Any]) -> str:
    parsed = parse_baro(data)
    if not parsed:
        return render_section("🌟 **Baro'Ki Teer (虚空商人)**", [], "   当前不在游戏中")

    lines = [
        f"   📍 位置: {parsed['location']}",
        f"   ⏰ 到达: {parsed['activation']}",
        f"   ⏰ 离开: {parsed['expiry']}",
    ]
    if parsed["manifest"]:
        lines.append("   🎒 待售物品:")
        for item in parsed["manifest"]:
            prime_price = item.get("prime_price")
            regular_price = item.get("regular_price")
            limit = item.get("limit")
            
            price_str = ""
            if prime_price is not None and prime_price > 0:
                price_str = f"💰 {prime_price}"
            if regular_price is not None and regular_price > 0:
                price_str += f" / 💵 {regular_price:,}"
            if limit:
                price_str += f" (限购{limit})"
            
            lines.append(f"      • {item['name']} {price_str}")
    else:
        lines.append("   🎒 库存: 将在到达时公布")
    return render_section("🌟 **Baro'Ki Teer (虚空商人)**", lines, "   当前不在游戏中")


def format_sortie(data: Dict[str, Any]) -> str:
    parsed = parse_sortie(data)
    if not parsed:
        return render_section("⚔️ **今日突击**", [], "   当前无任务")

    sortie_levels = ["50-60", "65-80", "80-100"]
    lines = [f"   👹 Boss: {parsed['boss']}"]
    if parsed["variety"]:
        lines.append(f"   📋 类型: {parsed['variety']}")
    if parsed["variants"]:
        lines.append("   🌍 任务节点:")
        for index, variant in enumerate(parsed["variants"], start=1):
            level = sortie_levels[index - 1] if index - 1 < len(sortie_levels) else "N/A"
            lines.append(f"      {index}. {variant['node']}")
            lines.append(f"         等级：{level}")
            lines.append(f"         任务：{variant['mission_type']}")
            lines.append(f"         状态：{variant['modifier'] or 'N/A'}")
            
            if variant.get("node_description"):
                lines.append(f"         说明：{variant['node_description']}")
            if variant.get("modifier_description"):
                lines.append(f"               {variant['modifier_description']}")
    return render_section("⚔️ **今日突击**", lines, "   当前无任务")


def format_archon_sortie(data: Dict[str, Any]) -> str:
    """格式化执行官突击（LiteSorties）显示"""
    parsed = parse_archon_sortie(data)
    if not parsed:
        return render_section("👑 **执行官突击**", [], "   当前无任务")

    # 执行官突击任务等级（参考游戏内设定）
    archon_levels = ["60-80", "80-100", "100-120"]
    lines = [f"   👹 执行官: {parsed['boss']}"]
    if parsed.get("activation"):
        lines.append(f"   ⏰ 开始: {parsed['activation']}")
    if parsed.get("expiry"):
        lines.append(f"   ⏰ 结束: {parsed['expiry']}")
    if parsed["missions"]:
        lines.append("   🌍 任务节点:")
        for index, mission in enumerate(parsed["missions"], start=1):
            level = (
                archon_levels[index - 1]
                if index - 1 < len(archon_levels)
                else "N/A"
            )
            lines.append(f"      {index}. {mission['node']}")
            lines.append(f"         等级：{level}")
            lines.append(f"         任务：{mission['mission_type']}")
            if mission.get("node_description"):
                lines.append(f"         说明：{mission['node_description']}")
    lines.append("   💎 奖励：执行官塑形石")
    return render_section("👑 **执行官突击**", lines, "   当前无任务")


def format_arbitration(data: Dict[str, Any]) -> str:
    parsed = parse_arbitration(data)
    if not parsed:
        parsed = parse_arbitration_schedule()
    if not parsed:
        return render_section(
            "🛡️ **Arbitration (仲裁)**",
            [],
            "   官方当前未返回仲裁数据；第三方排期源也暂时不可用",
        )

    lines = [
        f"   🌍 节点: {parsed['node']}",
        f"   ⚔️ 任务: {parsed['mission_type']}",
        f"   👹 敌人: {parsed['enemy']}",
    ]
    if parsed.get("expiry"):
        lines.append(f"   ⏳ 结束: {parsed['expiry']}")
    if parsed["reward"]:
        lines.append("   🏆 奖励:")
        for reward in parsed["reward"]:
            lines.append(f"      • {reward}")
    if parsed.get("source"):
        lines.append(f"   🔎 仲裁来源: {parsed['source']}")
    return render_section("🛡️ **Arbitration (仲裁)**", lines, "   官方当前未返回仲裁数据")


def format_fissure_group(title: str, items: List[Dict[str, Any]]) -> List[str]:
    lines = [title]
    if not items:
        lines.append("   当前无任务")
        return lines
    for item in items:
        lines.append(f"   • {item['node']}")
        task_line = item["mission_type"]
        if item["faction"]:
            task_line = f"{task_line} - {item['faction']}"
        lines.append(f"      等级：{item['level'] or 'N/A'}")
        lines.append(f"      任务：{task_line}")
        lines.append(f"      裂缝：{item['tier']}")
        lines.append(f"      剩余：{item['remaining']}")
    return lines


def format_fissures(data: Dict[str, Any]) -> str:
    parsed = parse_fissures(data)
    total = len(parsed["normal"]) + len(parsed["steel"])

    lines = [
        f"   📊 总数: {total}",
        f"   📗 普通: {len(parsed['normal'])} | 🛡️ 钢铁之路: {len(parsed['steel'])}",
        "",
    ]
    lines.extend(format_fissure_group("📗 普通裂缝:", parsed["normal"]))
    lines.append("")
    lines.extend(format_fissure_group("🛡️ 钢铁之路裂缝:", parsed["steel"]))
    return render_section("⚡ **虚空裂缝**", lines, "   当前无任务")


def format_invasions(data: Dict[str, Any]) -> str:
    parsed = parse_invasions(data)
    if not parsed:
        return render_section("💀 **入侵活动**", [], "   当前无任务")

    active_count = sum(1 for invasion in parsed if not invasion.get("completed"))
    completed_count = len(parsed) - active_count
    lines = [f"   📊 当前数量: {len(parsed)} | 进行中: {active_count} | 已完成待清算: {completed_count}"]
    for invasion in parsed:
        count = invasion.get("count", 0)
        goal = invasion.get("goal", 0)
        is_infested_invasion = invasion["attacker_faction"] == "感染者"
        
        if invasion.get("completed"):
            status = "✅"
            lead_faction = "已完成"
        elif count < 0:
            status = "🔴"
            lead_faction = invasion["attacker_faction"]
        elif count > 0:
            status = "🔵"
            lead_faction = invasion["defender_faction"]
        else:
            status = "⚪"
            lead_faction = ""
        
        filled_blocks = invasion["progress"] // 10
        progress_bar = "█" * filled_blocks + "░" * (10 - filled_blocks)
        
        lines.append(f"   {status} {invasion['node']}（{invasion['invasion_type']}）")
        if invasion.get("mission_type") or invasion.get("level"):
            mission_bits = []
            if invasion.get("mission_type"):
                mission_bits.append(invasion["mission_type"])
            if invasion.get("level") and invasion["level"] != "**-**":
                mission_bits.append(f"等级 {invasion['level']}")
            if invasion.get("base_faction") and invasion["base_faction"] != "未知":
                mission_bits.append(f"原驻守 {invasion['base_faction']}")
            lines.append(f"      📍 节点: {' | '.join(mission_bits)}")
        if is_infested_invasion:
            lines.append(f"      🛡️ 可支援: {invasion['defender_faction']} | 🎯 敌人: 感染者")
        else:
            lines.append(f"      ⚔️ 进攻方 {invasion['attacker_faction']} → 🛡️ 防守方 {invasion['defender_faction']}")
        lines.append(f"      📈 [{progress_bar}] {invasion['progress']}%")
        if goal > 0:
            lines.append(f"      📊 进度: {abs(count):,}/{goal:,}")
        if invasion.get("activation"):
            lines.append(f"      🕐 开始: {invasion['activation']}")
        if invasion.get("completed"):
            lines.append("      ✅ 状态: 已完成，等待官方清算")
        elif lead_faction and not is_infested_invasion:
            lines.append(f"      👑 当前领先: {lead_faction}")
        attacker_enemy = invasion.get("attacker_mission", {}).get("enemy_faction")
        defender_enemy = invasion.get("defender_mission", {}).get("enemy_faction")
        if not is_infested_invasion and (attacker_enemy or defender_enemy):
            lines.append(f"      🎯 帮进攻方打 {attacker_enemy or '未知'} | 帮防守方打 {defender_enemy or '未知'}")
        
        attacker = ", ".join(invasion["attacker"]) if invasion["attacker"] else "无特殊奖励"
        defender = ", ".join(invasion["defender"]) if invasion["defender"] else "无特殊奖励"
        if is_infested_invasion:
            lines.append(f"      🏆 防守奖励: {defender}")
        else:
            lines.append(f"      🏆 进攻奖励: {attacker}")
            lines.append(f"      🏆 防守奖励: {defender}")
        lines.append("")
    return render_section("💀 **入侵活动**", lines, "   当前无任务")


def format_void_storms(data: Dict[str, Any]) -> str:
    parsed = parse_void_storms(data)
    if not parsed:
        return render_section("🌪️ **虚空风暴**", [], "   当前无任务")

    lines = [f"   📊 当前数量: {len(parsed)}"]
    for storm in parsed:
        lines.append(f"   • {storm['tier']} @ {storm['node']}")
        lines.append(f"      开始: {storm['activation']} | 结束: {storm['expiry']}")
    return render_section("🌪️ **虚空风暴**", lines, "   当前无任务")


def format_alerts(data: Dict[str, Any]) -> str:
    parsed = parse_alerts(data)
    if not parsed:
        return render_section("⚠️ **警报任务**", [], "   当前无任务")

    lines = [f"   📊 当前数量: {len(parsed)}"]
    for alert in parsed:
        lines.append(f"   • {alert['mission_type']} @ {alert['node']}")
        lines.append(f"      开始: {alert['activation']} | 结束: {alert['expiry']}")
        if alert['reward']:
            lines.append(f"      奖励: {', '.join(alert['reward'])}")
    return render_section("⚠️ **警报任务**", lines, "   当前无任务")


def format_daily_deals(data: Dict[str, Any]) -> str:
    parsed = parse_daily_deals(data)
    if not parsed:
        return render_section("💰 **每日特惠**", [], "   当前无特惠")

    lines = [f"   📊 当前数量: {len(parsed)}"]
    for deal in parsed:
        lines.append(f"   • {deal['item']}")
        lines.append(f"      原价: {deal['original_price']} 白金 | 现价: {deal['sale_price']} 白金")
        lines.append(f"      折扣: {deal['discount']}% | 剩余: {deal['total'] - deal['sold']}/{deal['total']}")
        lines.append(f"      结束: {deal['expiry']}")
    return render_section("💰 **每日特惠**", lines, "   当前无特惠")


def format_season_info(data: Dict[str, Any]) -> str:
    parsed = parse_season_info(data)
    if not parsed:
        return render_section("🌙 **夜波/赛季**", [], "   当前无赛季信息")

    lines = [
        f"   📋 赛季: {parsed['season']}",
        f"   📊 阶段: {parsed['phase']}",
        f"   ⏰ 开始: {parsed['activation']}",
        f"   ⏰ 结束: {parsed['expiry']}",
        f"   🏷️ 阵营标签: {parsed['affiliation_tag']}",
        f"   📝 活跃挑战: {parsed['active_challenges']} 个",
    ]
    return render_section("🌙 **夜波/赛季**", lines, "   当前无赛季信息")


def _render_syndicate_group(missions: List[Dict[str, Any]]) -> List[str]:
    """渲染一组集团任务"""
    if not missions:
        return []
    lines = []
    groups = {}
    for mission in missions:
        syndicate = mission["syndicate_name"]
        if syndicate not in groups:
            groups[syndicate] = []
        groups[syndicate].append(mission)

    for syndicate_name, group_missions in groups.items():
        lines.append(f"      📋 {syndicate_name}:")
        for mission in group_missions:
            # 判断是否有真实节点（SolNode 或 SettlementNode 格式）
            has_real_nodes = any(
                n.startswith("SolNode") or n.startswith("SettlementNode")
                for n in mission["nodes"]
                if n and n not in ("N/A", "N / A")
            )
            # 判断是否需要显示 Seed（扎里曼号、解剖圣所、霍尼瓦尔）
            show_seed = mission["syndicate"] in (
                ZARIMAN_SYNDICATES | ENTRATI_LAB_SYNDICATES | HEX_SYNDICATES
            )
            if has_real_nodes:
                formatted_nodes = [
                    format_sortie_node_label(n) for n in mission["nodes"]
                ]
                nodes_text = " | ".join(formatted_nodes)
                lines.append(f"         • {nodes_text}")
            else:
                lines.append(f"         • 特殊任务")
            lines.append(f"            ⏰ {mission['activation']} ~ {mission['expiry']}")
            if show_seed and mission.get("seed"):
                lines.append(f"            🔢 Seed: {mission['seed']}")
    return lines


def format_syndicate_missions(data: Dict[str, Any]) -> str:
    parsed = parse_syndicate_missions(data)
    if not parsed:
        return render_section("🕴️ **集团任务**", [], "   当前无任务")

    lines = [f"   📊 当前任务总数: {len(parsed)}"]

    # 分类
    def filter_missions(syndicate_set):
        return [m for m in parsed if m["syndicate"] in syndicate_set]

    standard_missions = filter_missions(STANDARD_SYNDICATES)
    plains_missions = filter_missions(PLAINS_SYNDICATES)
    zariman_missions = filter_missions(ZARIMAN_SYNDICATES)
    entrati_lab_missions = filter_missions(ENTRATI_LAB_SYNDICATES)
    hex_missions = filter_missions(HEX_SYNDICATES)
    radio_legion_missions = filter_missions(RADIO_LEGION_SYNDICATES)

    # 其他（不在以上分类中的）
    all_classified = (
        STANDARD_SYNDICATES
        | PLAINS_SYNDICATES
        | ZARIMAN_SYNDICATES
        | ENTRATI_LAB_SYNDICATES
        | HEX_SYNDICATES
        | RADIO_LEGION_SYNDICATES
    )
    other_missions = [m for m in parsed if m["syndicate"] not in all_classified]

    # 1. 六大集团
    if standard_missions:
        lines.append("")
        lines.append("   ⭐ **六大集团（标准集团）**")
        lines.extend(_render_syndicate_group(standard_missions))

    # 2. 三大平原
    if plains_missions:
        lines.append("")
        lines.append("   🌾 **三大平原**")
        lines.extend(_render_syndicate_group(plains_missions))

    # 3. 扎里曼号
    if zariman_missions:
        lines.append("")
        lines.append("   🚀 **扎里曼号**")
        lines.extend(_render_syndicate_group(zariman_missions))

    # 4. 解剖圣所
    if entrati_lab_missions:
        lines.append("")
        lines.append("   🧬 **解剖圣所**")
        lines.extend(_render_syndicate_group(entrati_lab_missions))

    # 5. 霍尼瓦尔
    if hex_missions:
        lines.append("")
        lines.append("   🎸 **霍尼瓦尔**")
        lines.extend(_render_syndicate_group(hex_missions))

    # 6. 其他集团任务
    if other_missions:
        lines.append("")
        lines.append(f"   📦 **其他集团任务**（{len(other_missions)} 个）")
        other_groups = {}
        for mission in other_missions:
            syndicate = mission["syndicate_name"]
            if syndicate not in other_groups:
                other_groups[syndicate] = []
            other_groups[syndicate].append(mission)
        for syndicate_name, missions in other_groups.items():
            lines.append(f"      📋 {syndicate_name}（{len(missions)}）")

    return render_section("🕴️ **集团任务**", lines, "   当前无任务")


def format_events(data: Dict[str, Any]) -> str:
    parsed = parse_events(data)
    if not parsed:
        return render_section("📰 **公告/新闻**", [], "   当前无可展示公告")

    lines = [f"   📊 已整理: {len(parsed)} 条"]
    for item in parsed:
        lines.append(f"   • {item['title']}")
        if item["start"] != "N/A":
            lines.append(f"      开始: {item['start']}")
        if item["end"] != "N/A":
            lines.append(f"      结束: {item['end']}")
        elif item["posted"] != "N/A":
            lines.append(f"      发布时间: {item['posted']}")
        if item["live"]:
            lines.append(f"      直播: {item['live']}")
        lines.append(f"      链接: {item['link']}")
    return render_section("📰 **公告/新闻**", lines, "   当前无可展示公告")


def format_prime_vault_traders_raw(data: Dict[str, Any]) -> str:
    traders = get_first(data, "PrimeVaultTraders", default=[])
    if not traders:
        return render_section("🛒 **Prime 重生商店**", [], "   当前无数据")

    return (
        "🛒 **Prime 重生商店原始数据**\n"
        f"{json.dumps(traders, indent=2, ensure_ascii=False)}\n\n"
        f"📡 数据来源: {DATA_SOURCE}"
    )


def format_prime_vault_traders(data: Dict[str, Any]) -> str:
    traders = get_first(data, "PrimeVaultTraders", default=[])
    if not traders:
        return render_section("🛒 **Prime 重生商店**", [], "   当前无数据")

    trader = traders[0]
    lines = []

    activation = ts_to_date(trader.get("Activation"))
    expiry = ts_to_date(trader.get("Expiry"))
    remaining = format_remaining(trader.get("Expiry"))
    
    lines.append(f"⏰ 当前周期: {activation} ~ {expiry}")
    lines.append(f"🔔 剩余时间: {remaining}")
    lines.append("")

    manifest = trader.get("Manifest", [])
    if manifest:
        lines.append("🎁 当前可购买商品:")
        items_by_category = {}
        for item in manifest:
            item_type = item.get("ItemType", "")
            prime_price = item.get("PrimePrice")
            regular_price = item.get("RegularPrice")
            
            name = clean_item_name(item_type)
            if "PrimePack" in item_type or "DualPack" in item_type:
                category = "战甲包"
            elif "Prime" in name and ("Armor" in item_type or "Set" in item_type):
                category = "护甲套装"
            elif "Prime" in name and ("Skins" in item_type or "Scarf" in item_type or "Dangle" in item_type):
                category = "装饰物品"
            elif "Prime" in name and ("Weapons" in item_type or "Melee" in item_type or "LongGuns" in item_type or "ThrowingWeapons" in item_type):
                category = "Prime武器"
            elif "Prime" in name and ("Powersuits" in item_type or "Prime" == name):
                category = "Prime战甲"
            elif "BobbleHead" in item_type:
                category = "摇头娃娃"
            elif "Projection" in item_type:
                category = "虚空投射物"
            elif "Extractor" in item_type:
                category = "萃取器"
            else:
                category = "其他"
            
            if category not in items_by_category:
                items_by_category[category] = []
            
            price_str = ""
            if prime_price:
                price_str = f"💰 {prime_price} 白金"
            elif regular_price:
                price_str = f"💵 {regular_price} 白金"
            
            items_by_category[category].append(f"      └ {name} {price_str}")
        
        for category in sorted(items_by_category.keys()):
            lines.append(f"   • {category}:")
            lines.extend(items_by_category[category])
            lines.append("")

    featured_items = trader.get("FeaturedItems", [])
    if featured_items:
        lines.append("⭐ 特色商品时间表:")
        upcoming = []
        for idx, featured in enumerate(featured_items[:6], 1):
            item_name = clean_item_name(featured.get("FeaturedItem"))
            expiry_date = ts_to_date(featured.get("Expiry"))
            preview_until = ts_to_date(featured.get("PreviewHiddenUntil"))
            
            if "LastChance" in featured.get("FeaturedItem", ""):
                lines.append(f"   {idx}. 🚨 {item_name} - 截止: {expiry_date}")
            else:
                upcoming.append(f"   {idx}. {item_name} - 截止: {expiry_date}")
        
        lines.extend(upcoming)
        if len(featured_items) > 6:
            lines.append(f"   ... 还有 {len(featured_items) - 6} 个即将推出")

    lines.append(f"\n📡 数据来源: {DATA_SOURCE}")
    
    return "\n".join(lines)


def format_goals_raw(data: Dict[str, Any]) -> str:
    goals = get_first(data, "Goals", default=[])
    if not goals:
        return render_section("🎯 **活动目标**", [], "   当前无数据")

    return (
        "🎯 **活动目标原始数据**\n"
        f"{json.dumps(goals, indent=2, ensure_ascii=False)}\n\n"
        f"📡 数据来源: {DATA_SOURCE}"
    )


def format_conquests_raw(data: Dict[str, Any]) -> str:
    conquests = get_first(data, "Conquests", default=[])
    if not conquests:
        return render_section("🧪 **科研任务**", [], "   当前无数据")

    return (
        "🧪 **科研任务原始数据**\n"
        f"{json.dumps(conquests, indent=2, ensure_ascii=False)}\n\n"
        f"📡 数据来源: {DATA_SOURCE}"
    )


def format_calendar_seasons_raw(data: Dict[str, Any]) -> str:
    seasons = get_first(data, "KnownCalendarSeasons", default=[])
    if not seasons:
        return render_section("📅 **1999 日历赛季**", [], "   当前无数据")

    return (
        "📅 **1999 日历赛季原始数据**\n"
        f"{json.dumps(seasons, indent=2, ensure_ascii=False)}\n\n"
        f"📡 数据来源: {DATA_SOURCE}"
    )


def format_full_status(data: Dict[str, Any]) -> str:
    sections = [
        "=" * 50,
        "🎮 **Warframe 实时状态**",
        "=" * 50,
        f"📅 更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"📌 Build: {get_first(data, 'BuildLabel', default='N/A')}",
        "",
        format_baro(data),
        "",
        format_sortie(data),
        "",
        format_arbitration(data),
        "",
        format_fissures(data),
        "",
        format_void_storms(data),
        "",
        format_invasions(data),
        "",
        format_season_info(data),
        "",
        "=" * 50,
    ]
    return "\n".join(sections)


def format_anatomy_sanctuary_bounties(data: Dict[str, Any]) -> str:
    import random
    syndicates = get_first(data, "SyndicateMissions", default=[])
    target_syndicate = None
    for syndicate in syndicates:
        tag = get_first(syndicate, "Tag", "tag")
        if tag in ("AnatomySanctuarySyndicate", "HexSyndicate"): # HexSyndicate是1999相关集团tag
            target_syndicate = syndicate
            break
    
    if not target_syndicate:
        return render_section("🧪 **解剖圣所赏金任务**", [], "   当前无可用赏金任务")

    activation = ts_to_date(get_first(target_syndicate, "Activation"))
    expiry = ts_to_date(get_first(target_syndicate, "Expiry"))
    remaining = format_remaining(get_first(target_syndicate, "Expiry"))
    seed = get_first(target_syndicate, "Seed", "seed", default=random.randint(1, 999999))
    
    jobs = get_first(target_syndicate, "Jobs", "jobs", "Missions", "missions", default=[])
    bounties = []
    
    if jobs:
        # 优先使用API返回的真实数据
        for job in jobs[:5]:
            reward = get_first(job, "reward", "Reward", "missionReward", "MissionReward", default={})
            standing = get_first(reward, "standing", "Standing", "xp", "XP", default=0)
            level = get_first(job, "level", "Level", "tier", "Tier", "difficulty", "Difficulty", default=1)
            node = get_first(job, "node", "Node", "location", "Location", default="N/A")
            mission_type = mission_type_name(get_first(job, "missionType", "MissionType", "type", "Type", default="N/A"))
            title = extract_event_title(get_first(job, "Messages", "messages", default=[]))
            if not title or title == "N/A":
                title = get_first(job, "title", "Title", "name", "Name", default="未知赏金")
            requirements = get_first(job, "requirements", "Requirements", "prerequisite", "Prerequisite", default="")
            description = get_first(job, "description", "Description", "objective", "Objective", "goal", "Goal", default="无描述")

            bounties.append({
                "level": level,
                "standing": int(standing),
                "node": normalize_node_name(node),
                "mission_type": mission_type,
                "title": title.strip(),
                "requirements": requirements.strip(),
                "description": description.strip(),
            })
    else:
        # API无数据时使用本地随机生成，基于Seed保证同轮换周期内容一致
        rng = random.Random(seed)
        # 从NODE_METADATA获取SolNode715-721共7个节点，7选5不重复，按等级升序匹配难度
        node_ids = [f"SolNode{i}" for i in range(715, 722)]
        node_pool = []
        for nid in node_ids:
            meta = NODE_METADATA.get(nid, {})
            node_pool.append({
                "name": meta.get("name", nid),
                "mission_type": meta.get("mission", "未知"),
                "min_level": meta.get("level", [0, 0])[0],
                "max_level": meta.get("level", [0, 0])[1],
            })
        selected_nodes = sorted(rng.sample(node_pool, 5), key=lambda x: x["min_level"])
        # 按难度等级1-5分别选对应的EntratiLab类型赏金
        for level in range(1, 6):
            # 筛选对应难度的EntratiLab赏金，随机选1个
            level_bounties = [b for b in ENTRATI_LAB_BOUNTY_POOL if b["level"] == level and b["type"] == "EntratiLab"]
            bounty = rng.choice(level_bounties)
            node = selected_nodes[level-1]
            
            bounties.append({
                "level": level,
                "standing": bounty["standing"],
                "node": node["name"],
                "mission_type": node["mission_type"],
                "level_range": f"{node['min_level']}-{node['max_level']}",
                "title": bounty["title"],
                "requirements": bounty["requirements"],
                "description": bounty["description"],
            })

    lines = []
    lines.append(f"🕒 本轮更新: {activation}")
    lines.append(f"🔄 下次轮换: {expiry} | 剩余: {remaining}")
    lines.append(f"🔢 本轮换Seed: {seed}")
    lines.append("")
    
    for i, bounty in enumerate(bounties, 1):
        level_range = f" {bounty.get('level_range', '')}级" if 'level_range' in bounty else ""
        lines.append(f"🏆 赏金 {i} (难度等级 {bounty['level']}{level_range})")
        lines.append(f"   🎯 名称: {bounty['title']}")
        lines.append(f"   💰 声望奖励: {bounty['standing']:,}")
        lines.append(f"   🗺️ 地图: {bounty['node']}")
        lines.append(f"   ⚔️ 任务类型: {bounty['mission_type']}")
        if bounty['requirements']:
            lines.append(f"   📋 准入要求: {bounty['requirements']}")
        lines.append(f"   📝 任务目标: {bounty['description']}")
        lines.append("")
    
    return render_section("🧪 **解剖圣所赏金任务**", lines, "   当前无可用赏金任务")

def run_query(query: str, data: Dict[str, Any]) -> str:
    normalized = (query or "状态").lower().strip()
    if "原始突击" in normalized or "raw sortie" in normalized:
        import json
        sorties = get_first(data, "Sorties", default=[])
        return f"⚔️ **突击原始数据**\n{json.dumps(sorties, indent=2, ensure_ascii=False)}\n\n📡 数据来源: api.warframe.com"
    if (
        "执行官突击" in normalized
        or "archon" in normalized
        or normalized == "litesortie"
        or normalized == "litesorties"
    ):
        return format_archon_sortie(data)
    if "突击" in normalized or normalized == "sortie":
        return format_sortie(data)
    if "baro" in normalized or "商人" in normalized or normalized == "voidtrader":
        return format_baro(data)
    if "仲裁" in normalized or normalized == "arbitration":
        return format_arbitration(data)
    if "原始裂缝" in normalized or "raw fissure" in normalized:
        import json
        fissures = get_first(data, "ActiveMissions", default=[])
        return f"⚡ **虚空裂缝原始数据**\n{json.dumps(fissures, indent=2, ensure_ascii=False)}\n\n📡 数据来源: api.warframe.com"
    if "裂缝" in normalized or normalized == "fissure":
        return format_fissures(data)
    if "原始入侵" in normalized or "raw invasion" in normalized:
        import json
        invasions = get_first(data, "Invasions", default=[])
        return f"💀 **入侵原始数据**\n{json.dumps(invasions, indent=2, ensure_ascii=False)}\n\n📡 数据来源: api.warframe.com"
    if "入侵" in normalized or normalized == "invasion":
        return format_invasions(data)
    if "虚空风暴" in normalized or normalized == "voidstorms":
        return format_void_storms(data)
    if "警报" in normalized or normalized == "alerts":
        return format_alerts(data)
    if "每日特惠" in normalized or normalized == "dailydeals":
        return format_daily_deals(data)
    if "夜波" in normalized or normalized == "nightwave" or normalized == "season":
        return format_season_info(data)
    if "集团任务" in normalized or normalized == "syndicates":
        return format_syndicate_missions(data)
    if (
        "解剖圣所" in normalized or "anatomy" in normalized or "sanctuary" in normalized or "解剖" in normalized
    ):
        return format_anatomy_sanctuary_bounties(data)
    if (
        "primevault" in normalized
        or "prime vault" in normalized
        or "prime重生" in normalized
        or "重生商店" in normalized
        or "primevaulttraders" in normalized
    ):
        if "原始" in normalized or "raw" in normalized:
            return format_prime_vault_traders_raw(data)
        return format_prime_vault_traders(data)
    if "goals" in normalized or "活动目标" in normalized or "目标活动" in normalized:
        return format_goals_raw(data)
    if "conquests" in normalized or "科研" in normalized or "科研任务" in normalized:
        return format_conquests_raw(data)
    if (
        "calendar" in normalized
        or "日历赛季" in normalized
        or "1999日历" in normalized
        or "1999 日历" in normalized
    ):
        return format_calendar_seasons_raw(data)
    if "公告" in normalized or "新闻" in normalized or normalized == "events":
        return format_events(data)
    return format_full_status(data)


def main(argv: Optional[List[str]] = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    query = " ".join(args) if args else "状态"
    print("🔄 正在获取 Warframe 实时数据...", flush=True)
    try:
        data = fetch_worldstate()
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        print(f"❌ 获取数据失败: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover
        print(f"❌ 未知错误: {exc}")
        return 1

    print(run_query(query, data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
