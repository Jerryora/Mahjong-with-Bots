from tile import *
from ruleengine import *


class Score:
    def __init__(self, initial_points=100):
        self._points = initial_points  # 使用私有属性

    def add_points(self, points):
        if points < 0:
            raise ValueError("分数不能为负数.")
        self._points += points

    def subtract_points(self, points):
        if points < 0:
            raise ValueError("分数不能为负数.")
        # if self._points - points < 0:
        #     raise ValueError("Cannot have negative points.")
        self._points -= points

    def __str__(self):
        return str(self._points)


class Player:
    def __init__(self, name, position):
        self.name = name
        self.position = position
        self.hand = []  # 手牌
        self.side = []  # 吃碰手牌
        self.river = []  # 河牌
        self.fangchong = False  # 放铳状态
        self.win = False  # 赢家
        self.riichi_flag = False  # 听 标志
        self.riichi_list = []  # 听 哪些牌
        self.drawn_tile = None  # 刚抓的一张牌, 每个玩家都有自己的 drawn_tile 属性
        self.score = Score()  # 计分系统

    def sort_hand(self):
        # 定义种类的排序顺序
        # kind_order字典将牌的种类映射到它们的排序优先级
        kind_order = {'D': 0, 'B': 1, 'C': 2, 'W': 3, 'Y': 4}
        # 先按照种类分组
        grouped_hand = {}  # 初始化一个空字典
        for tile in self.hand:  # 遍历手牌 self.hand，根据每张牌的种类将它们分组。
            kind = tile.kind
            if kind not in grouped_hand:
                grouped_hand[kind] = []  # 如果当前种类在 grouped_hand 中不存在，则创建一个新的列表。
            grouped_hand[kind].append(tile)  # 将牌添加到相应种类的列表中

        # 对每个分组内的牌进行排序
        for kind, tiles in grouped_hand.items():
            tiles.sort()  # 使用默认的排序方法，Tile类实现了__lt__方法

        sorted_hand = []  # 初始化一个空列表
        # lambda k: kind_order[k]是一个匿名函数（lambda函数），接收一个种类 k 作为输入，返回该种类在 kind_order 中的优先级。
        # sorted 函数根据 kind_order 中定义的优先级对种类进行排序
        for kind in sorted(grouped_hand.keys(), key=lambda k: kind_order[k]):
            sorted_hand.extend(grouped_hand[kind])  # 按顺序将分组内的牌添加到sorted_hand中

        # 将排序后的牌重新放回手牌中
        self.hand = sorted_hand

    def sort_side(self):
        """整理手牌旁"""
        self.side.sort()

    def reset(self):
        """重置玩家状态"""
        self.hand.clear()
        self.side.clear()
        self.river.clear()
        self.riichi_list.clear()
        self.fangchong = False
        self.win = False
        self.riichi_flag = False

    def __str__(self):
        # return f"Player {self.name}: Hand: {self.hand}, Side: {self.side}, River: {self.river}"
        return f"Player {self.name}: Hand: {self.hand}, Side: {self.side}"

    def pong(self, current_tile):
        """碰牌"""
        # 创建一个空列表，用于存储需要移除的牌
        tiles_to_remove = []
        # 检查玩家手中是否有两张与要碰的牌相同的牌
        # 由于 check_pong 已经确保玩家手中有两张相同的牌，这里不再需要进一步检查
        # 遍历手牌，将两张与 current_tile 相同的牌添加到 tiles_to_remove 列表中
        for tile in self.hand:
            if tile.kind == current_tile.kind and tile.n == current_tile.n:
                # 将符合条件的牌添加到需要移除的列表中
                tiles_to_remove.append(tile)
        # 循环结束后统一移除需要移除的牌
        for tile in tiles_to_remove:
            self.hand.remove(tile)
            self.side.append(tile)
        self.side.append(current_tile)
        print(f" {self.name} 碰了 {current_tile.text}")

    def kong(self, tile):
        """处理杠牌操作"""
        # 正常“碰”杠
        if self.hand.count(tile) == 3:
            for _ in range(3):
                self.hand.remove(tile)
            self.side.extend([tile] * 4)
            print(f" {self.name} 明杠了 {tile.text}")
        # 处理暗杠（从手牌中杠）
        elif self.hand.count(tile) == 4:
            for _ in range(4):
                self.hand.remove(tile)
            self.side.extend([tile] * 4)
            print(f" {self.name} 暗杠了 {tile.text}")
        # 处理明杠（从副露中杠）
        elif self.side.count(tile) == 3 and self.hand.count(tile) == 1:
            for _ in range(3):
                self.side.remove(tile)
            self.side.extend([tile] * 4)
            self.hand.remove(tile)
            print(f" {self.name} 加杠了 {tile.text}")

    def has_consecutive_tiles(self, tile):
        """检查手牌中是否存在与给定牌连续的三张牌"""
        kind_tiles = [t for t in self.hand if t.kind == tile.kind]  # 过滤同花色的牌：首先从手牌中过滤出与tile同花色的所有牌。
        kind_numbers = [t.n for t in kind_tiles]  # 获取这些牌的数字值并排序，以便后续的顺子检查。

        # 检查当前牌及其后续两张牌是否组成顺子 tile, tile+1, tile+2 的顺子
        if tile.n in kind_numbers and tile.n + 1 in kind_numbers and tile.n + 2 in kind_numbers:
            return True
        # 检查当前牌及其前两张牌是否组成顺子 tile, tile-1, tile-2 的顺子
        if tile.n - 2 in kind_numbers and tile.n - 1 in kind_numbers and tile.n in kind_numbers:
            return True
        # 检查当前牌及其前后一张牌是否组成顺子 tile-1, tile, tile+1 的顺子
        if tile.n - 1 in kind_numbers and tile.n in kind_numbers and tile.n + 1 in kind_numbers:
            return True

        return False

    def check_chow(self, tile):
        """检查是否可以吃牌"""
        if not tile.is_num:
            # 不是数牌不能吃
            return False

        # 获取手牌中与打出的牌同一花色的所有牌
        certain_kind_tiles = [t for t in self.hand if t.kind == tile.kind]
        certain_kind_numbers = [t.n for t in certain_kind_tiles]

        # 检查手牌里该Tile是否已经形成顺子
        if self.has_consecutive_tiles(tile):  # 此行注释会导致吃牌时，如果某个player的hand手牌里3条4条5条，上家打出了4条。chow时会导致多remove掉一张4条。
            return False
        # 检查吃前面的牌
        if tile.n - 2 in certain_kind_numbers and tile.n - 1 in certain_kind_numbers:
            return True
        # 检查吃中间的牌
        if tile.n - 1 in certain_kind_numbers and tile.n + 1 in certain_kind_numbers:
            return True
        # 检查吃后面的牌
        if tile.n + 1 in certain_kind_numbers and tile.n + 2 in certain_kind_numbers:
            return True

        return False

    def chow(self, tile, combination):
        """吃牌"""
        # 将吃的牌添加到手牌旁
        self.side.extend(combination)  # extend 是将一个可迭代对象（如列表、元组等）中的所有元素添加到原列表中； append是将一个对象作为单个元素添加到列表的末尾。

        # 从手牌中移除吃的牌
        # for chow_tile in combination:
        #     if chow_tile in self.hand:
        #         self.hand.remove(chow_tile)
        # 从手牌中移除吃的牌，逐个匹配和移除
        for chow_tile in combination:
            if chow_tile != tile and chow_tile in self.hand:  # 在移除时跳过了与 tile 本身相同的牌，因为 tile 是当前被吃的牌，不需要从手牌中移除
                self.hand.remove(
                    chow_tile)  # 假设手牌里有1条2条2条3条，如果上家打出4条，那么应该移除1张2条1张3条，而不是2张2条都被移除。因为chow_tile在combination里只迭代一次。

        print(f" {self.name} 吃牌成功: {[t.n for t in combination]}")

    def check_kong(self, current_tile):
        # 判断是否可以杠牌的逻辑
        # 如果满足杠牌条件，返回 True，否则返回 False
        if self.hand.count(current_tile) == 3:
            print(f" {self.name} 可以杠 {current_tile}")
            return True
        else:
            return False

    def check_pong(self, current_tile):
        # 判断是否可以碰牌的逻辑
        # 如果满足碰牌条件，返回 True，否则返回 False

        count = 0
        for tile in self.hand:
            if tile.kind == current_tile.kind and tile.n == current_tile.n:
                count += 1
        return count == 2

    def check_riichi(self):
        # 调用之前打印手牌，确认手牌是否被篡改
        print(f"调用check_riichi之前的手牌: {self.hand}")

        converted_hand = convert_hand_to_wintile_format(self.hand)
        # print("转换后的手牌格式:", converted_hand)  # 添加调试信息，检查手牌格式
        self.riichi_list = wintile(converted_hand)
        print("听牌列表:", self.riichi_list)  # 输出生成的听牌列表
        if not self.riichi_list:
            return False
        return True

    def check_win(self, discard_tile):
        """检查是否可以胡牌"""
        # 如果打出的牌在听牌列表中，返回 True，否则返回 False
        if isinstance(discard_tile, Tile):
            discard_tile_str = discard_tile.text
        else:
            discard_tile_str = discard_tile

        if discard_tile_str in self.riichi_list:
            return True
        else:
            return False

    def is_win(self, tiles):
        # 检查玩家手牌是否符合胡牌条件
        converted_hand = convert_hand_to_wintile_format(tiles)
        return checkwin(converted_hand)

    def get_chow_combinations(self, tile):
        """获取所有可能的吃牌组合"""
        chow_combinations = []

        # 获取手牌中与打出的牌同一花色的所有牌
        certain_kind_tiles = [t for t in self.hand if t.kind == tile.kind]
        certain_kind_numbers = sorted(set(t.n for t in certain_kind_tiles + [tile]))  # 包括tile的数字n， 去重并排序
        # 使用 len(combination) 判断是为了确保每个顺子（即每个组合）中的牌是唯一的，并且按正确的顺序添加到组合中。这样可以避免重复添加相同的牌对象
        # 添加第一张牌：当 t.n == tile.n - 1 且 combination 为空时，添加第一张牌。
        # 添加第二张牌：当 t.n == tile.n 且 combination 长度为1时，添加第二张牌（即传入的 tile）。
        # 添加第三张牌：当 t.n == tile.n + 1 且 combination 长度为2时，添加第三张牌，并终止循环。

        # 检查吃前面的牌
        if tile.n - 1 in certain_kind_numbers and tile.n - 2 in certain_kind_numbers:
            combination = []  # 初始化组合，将tile放入组合中
            seen_tiles = set()  # 记录已经添加到组合中的牌的值
            for t in self.hand:
                if t.kind == tile.kind and t.n in {tile.n - 2, tile.n - 1} and t.n not in seen_tiles:
                    combination.append(t)  # 添加手牌到组合中，这样保证Tile组合显示是从小到大
                    seen_tiles.add(t.n)  # 标记这个牌值已被添加
                    if len(combination) == 2:  # 如果组合中有3张牌，结束循环
                        break
            combination.append(tile)  # 由于for循环始终是由小到大顺序，所以后添加tile，保证顺序一致。
            if len(combination) == 3:
                chow_combinations.append(combination)  # 添加到吃牌组合列表

        # 检查吃中间的牌
        if tile.n - 1 in certain_kind_numbers and tile.n + 1 in certain_kind_numbers:
            combination = [tile]  # 初始化组合，将tile放入组合中
            seen_tiles = set()  # 记录已经添加到组合中的牌的值
            for t in self.hand:
                if t.kind == tile.kind and t.n in {tile.n - 1, tile.n + 1} and t.n not in seen_tiles:
                    if t.n < tile.n:
                        combination.insert(0, t)  # 如果t的值比tile小，插入组合前面
                    else:
                        combination.append(t)  # 如果t的值比tile大，插入组合后面
                    seen_tiles.add(t.n)  # 标记这个牌值已被添加
                    if len(combination) == 3:  # 如果组合中有3张牌，结束循环
                        break
            if len(combination) == 3:
                chow_combinations.append(combination)  # 添加到吃牌组合列表

        # 检查吃后面的牌
        if tile.n + 1 in certain_kind_numbers and tile.n + 2 in certain_kind_numbers:
            combination = [tile]  # 初始化组合，将tile放入组合中
            seen_tiles = set()  # 记录已经添加到组合中的牌的值
            for t in self.hand:
                if t.kind == tile.kind and t.n in {tile.n + 1, tile.n + 2} and t.n not in seen_tiles:
                    combination.append(t)  # 添加手牌到组合中
                    seen_tiles.add(t.n)  # 标记这个牌值已被添加
                    if len(combination) == 3:  # 如果组合中有3张牌，结束循环
                        break
            if len(combination) == 3:
                chow_combinations.append(combination)  # 添加到吃牌组合列表

        return chow_combinations  # 返回所有可能的吃牌组合

