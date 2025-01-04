import pickle
from pathlib import Path
import re

SUITS = "条饼万东南西北中发白"
NUMS = "123456789"

TILES_TEXT = [
    ["1条", "2条", "3条", "4条", "5条", "6条", "7条", "8条", "9条"],  # 条
    ["1饼", "2饼", "3饼", "4饼", "5饼", "6饼", "7饼", "8饼", "9饼"],  # 饼
    ["1万", "2万", "3万", "4万", "5万", "6万", "7万", "8万", "9万"],  # 万
    ["东", "南", "西", "北", "中", "发", "白"]  # 东南西北中发白
]


def hand_count(hand):
    # 计算手牌总数
    return sum(sum(s) for s in hand)


def parse_hand(hand_str):
    # 解析输入的手牌字符串
    tiles = re.split(r"\s+", hand_str.strip())
    hand = [[0] * 9 for _ in range(4)]
    for tile in tiles:
        if len(tile) == 1:
            hand[3][SUITS.index(tile) - 3] += 1
        else:
            s = SUITS.index(tile[1])
            n = NUMS.index(tile[0])
            hand[s][n] += 1
    return hand


# parse_tile 函数的作用是将单张牌的字符串表示解析为对应的索引
def parse_tile(tile_str):
    # 解析单张牌
    if len(tile_str) == 1:
        return 3, SUITS.index(tile_str) - 3
    else:
        return SUITS.index(tile_str[1]), NUMS.index(tile_str[0])


def init_tables():
    # 初始化胡牌组合表
    def gen_combinations(a, level, table):
        if level > 4:
            return
        total_count = sum(a)  # 计算当前手牌的总数
        for i in range(9):
            if a[i] + 3 > 4 or total_count + 3 > 14:
                continue
            b = a.copy()
            b[i] += 3
            table.add(tuple(b))
            gen_combinations(b, level + 1, table)
        for i in range(7):
            if (a[i] + 1 > 4) or (a[i + 1] + 1 > 4) or (a[i + 2] + 1 > 4) or total_count + 3 > 14:
                continue
            b = a.copy()
            b[i] += 1
            b[i + 1] += 1
            b[i + 2] += 1
            table.add(tuple(b))
            gen_combinations(b, level + 1, table)

    def gen_pairs(table):
        for i in range(9):
            a = [0] * 9
            a[i] += 2
            # print(f"Generated pair: {a}")  # 打印生成的对子组合
            table.add(tuple(a))
            gen_combinations(a, 1, table)

    global TAB3N, TAB3N2
    path = Path(__file__).parent / "win.table"
    if path.exists():
        with open(path, "rb") as f:
            TAB3N, TAB3N2 = pickle.load(f)
    else:
        TAB3N = set()
        TAB3N2 = set()
        TAB3N.add((0,) * 9)
        gen_combinations([0] * 9, 1, TAB3N)
        gen_pairs(TAB3N2)
        with open(path, "wb") as f:
            pickle.dump((TAB3N, TAB3N2), f)


def checkwin(hand):
    # 检查手牌是否胡牌
    total_count = hand_count(hand)
    if total_count % 3 != 2:
        return False  # 胡牌需要总牌数为 14 张（即 3n+2）

    have3n2 = False  # 初始化标志，记录是否找到 3n+2 组合

    for s in range(3):  # 数牌
        a = tuple(hand[s])
        if a in TAB3N2:  # 如果当前花色的牌组成一个 3n+2 的组合
            if have3n2:  # 检查是否已经找到一个 3n+2 的组合
                return False  # 如果已经找到，则返回 False，说明手牌不合法
            have3n2 = True  # 记录已经找到一个 3n+2 的组合
        elif a not in TAB3N:  # 如果当前花色的牌既不在 3n+2 表中，也不在 3n 表中
            return False  # 返回 False，说明手牌不合法

    # 字牌特殊处理
    # 检查字牌（东、南、西、北、中、发、白）
    honors = hand[3]

    # 统计单张、对、刻子、杠子的数量
    single_count = 0
    pair_count = 0
    triplet_count = 0

    for i in range(7):
        if honors[i] == 1:
            single_count += 1
        elif honors[i] == 2:
            pair_count += 1
        elif honors[i] == 3:
            triplet_count += 1

    # 判断字牌是否符合胡牌条件
    if single_count > 0:
        return False  # 有单张字牌不可能胡牌
    if pair_count > 1:
        return False  # 超过一个对子不可能胡牌
    if pair_count == 1:
        if have3n2:
            return False  # 如果已经有一个 3n+2 的组合，返回 False
        have3n2 = True

    # 如果 have3n2 依旧是 False，说明没有形成 3n+2 的组合
    return have3n2


def convert_hand_to_wintile_format(hand):
    # for tile in hand:
    #     print(f"Tile: {tile}, Text: {tile.text}")  # 检查 tile.text 是否正确
    converted_hand_str = ' '.join(tile.text for tile in hand)
    converted_hand = parse_hand(converted_hand_str)
    return converted_hand


def wintile(hand):
    # 判断听牌并返回可胡的牌
    total_count = hand_count(hand)
    if total_count % 3 != 1:
        return []
    tiles = []
    for s in range(3):
        for rank in range(9):
            if hand[s][rank] >= 4:
                continue
            hand[s][rank] += 1
            if checkwin(hand):
                tiles.append(TILES_TEXT[s][rank])
            hand[s][rank] -= 1
    for rank in range(7):  # 字牌
        if hand[3][rank] >= 4:
            continue
        hand[3][rank] += 1
        if checkwin(hand):
            tiles.append(TILES_TEXT[3][rank])
        hand[3][rank] -= 1
    return tiles


# 初始化胡牌表
init_tables()
