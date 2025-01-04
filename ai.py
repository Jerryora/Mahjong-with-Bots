from player import *


class Bot(Player):

    def __init__(self, name, position):
        super().__init__(name, position)

    def is_isolated(self, tile):  # 定义了判断孤张的方法，确保牌不连续且数量较少的牌被视为孤张
        kind_tiles = [t for t in self.hand if t.kind == tile.kind]
        kind_numbers = [t.n for t in kind_tiles]
        kind_numbers.sort()

        if len(kind_numbers) == 1:
            return True

        tile_index = kind_numbers.index(tile.n)
        if tile_index == 0:
            return kind_numbers[1] > tile.n + 2
        elif tile_index == len(kind_numbers) - 1:
            return kind_numbers[-2] < tile.n - 2
        else:
            return kind_numbers[tile_index - 1] < tile.n - 2 and kind_numbers[tile_index + 1] > tile.n + 2

    def evaluate_tile(self, tile, discard_pile):
        score = 0

        # 孤张评分：孤张的评分较低（例如，-10）。
        if self.is_isolated(tile):
            score -= 10

        # 连牌和搭子评分：牌是否与其他牌能组成顺子或刻子，如果能，评分较高（例如，+5或+3）
        kind_tiles = [t for t in self.hand if t.kind == tile.kind]
        kind_numbers = [t.n for t in kind_tiles]
        kind_numbers.sort()

        if tile.n - 1 in kind_numbers or tile.n + 1 in kind_numbers:
            score += 5
        if tile.n - 2 in kind_numbers or tile.n + 2 in kind_numbers:
            score += 3

        # 幺九牌和中张牌评分：幺九牌评分较低（例如，-5），中张牌评分较高（例如，+2）。
        if tile.n == 1 or tile.n == 9:
            score -= 5
        elif 2 <= tile.n <= 8:
            score += 2

        # 字牌评分较低（例如，-2）
        if tile.kind in ['W', 'Y']:
            score -= 2

        # 优先选择在 discard_pile 中的牌，降低其评分
        for discarded_tile in discard_pile:
            if discarded_tile.kind == tile.kind and discarded_tile.n == tile.n:
                score -= 5
                break

        return score

    def make_decision(self, discard_pile):
        tile_values = {tile: self.evaluate_tile(tile, discard_pile) for tile in self.hand}
        discard_tile = min(tile_values, key=tile_values.get)  # 返回最低价值的牌
        return discard_tile  # 选择最低价值的牌作为弃牌

    def count_sets_and_pairs(self, hand):
        # 按照牌的类别分组
        groups = {}
        for tile in hand:
            if tile.kind not in groups:
                groups[tile.kind] = []
            groups[tile.kind].append(tile.n)  # 依据牌的数字进行分组

        sets = 0  # 面子数量
        pairs = 0  # 对子数量

        # 对每个类别的牌进行排序，并检查面子和对子
        for kind, numbers in groups.items():
            numbers.sort()  # 先对每种花色的牌排序

            i = 0
            while i < len(numbers):
                # 检查刻子（AAA）
                if i + 2 < len(numbers) and numbers[i] == numbers[i + 1] == numbers[i + 2]:
                    sets += 1
                    i += 3
                # 检查顺子（ABC）
                elif i + 2 < len(numbers) and numbers[i] + 1 == numbers[i + 1] and numbers[i] + 2 == numbers[i + 2]:
                    sets += 1
                    i += 3
                # 检查对子（AA）
                elif i + 1 < len(numbers) and numbers[i] == numbers[i + 1]:
                    pairs += 1
                    i += 2
                else:
                    i += 1

        return sets, pairs

    def simulate_steps_to_riichi(self, max_depth=2):
        best_tile = None  # 最优出牌
        min_steps = float('inf')  # 初始化为一个很大的数，表示最小步数

        # 遍历手牌中的每一张牌，模拟打出每张牌
        for tile in self.hand:
            # 调用递归函数，计算打出该牌后的最少步数
            steps = self.simulate_steps_to_riichi_recursive(tile, max_depth)

            # 如果找到步数更少的选择，更新最优出牌
            if steps < min_steps:
                min_steps = steps
                best_tile = tile

        # 返回最优的出牌和最少步数
        return best_tile, min_steps

    def simulate_steps_to_riichi_recursive(self, tile, max_depth):
        # 模拟打出这张牌
        simulated_hand = self.hand.copy()  # 复制当前手牌
        simulated_hand.remove(tile)  # 移除当前模拟打出的牌

        # 保存原始手牌并替换为模拟手牌
        original_hand = self.hand
        self.hand = simulated_hand

        # 计算面子和对子数量
        sets, pairs = self.count_sets_and_pairs(self.hand)

        # 检查是否已经接近听牌状态
        remaining_sets = 4 - sets  # 还需要几个面子
        remaining_pairs = 1 - pairs  # 还需要几个对子

        # 如果已经形成4个面子和1对对子，则表示已经上听
        if remaining_sets == 0 and remaining_pairs == 0:
            self.hand = original_hand  # 恢复原手牌
            return 0  # 已经上听，返回0步

        # 如果没有更多步数可以递归，则返回剩余步数
        if max_depth == 0:
            self.hand = original_hand  # 恢复原手牌
            return remaining_sets + remaining_pairs  # 返回剩余的步数

        # 尝试模拟打出其余的牌，递归计算步数
        min_steps = max_depth
        for next_tile in simulated_hand:
            # 递归计算打出 next_tile 后的步数，并比较得出最小步数
            steps = self.simulate_steps_to_riichi_recursive(next_tile, max_depth - 1)
            min_steps = min(min_steps, steps + 1)  # 递归后步数+1

        # 恢复原手牌
        self.hand = original_hand
        return min_steps


def test_simulate_steps_to_riichi():
    # # # 示例代码片段，展示如何创建手牌并进行决策
    bot = Bot(name="AI_Player", position=0)
    bot.hand = [
        C(1), C(2), C(3),  # 万子 1, 2, 3
        C(4), C(5), C(6),  # 万子 4, 5, 6
        C(7),  # 万子 7
        D(2), D(2),  # 条子 2, 2
        D(3), D(4),  # 条子 3, 4
        W(1), W(1)  # 字牌 1, 1 (东风)
    ]

    # 打印当前手牌
    print("当前手牌：", [str(tile) for tile in bot.hand])

    # 调用 simulate_steps_to_riichi 方法计算最优出牌
    best_tile, min_steps = bot.simulate_steps_to_riichi(max_depth=2)

    # 打印最优出牌和最少步数
    print(f"最优出牌: {best_tile}, 最少步数: {min_steps}")


# 运行测试
# test_simulate_steps_to_riichi()

