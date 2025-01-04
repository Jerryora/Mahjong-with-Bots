import time
import sys
from collections import Counter
from gui import *


class Game:
    def __init__(self, gui):
        self.players = gui.players
        self.current_player_index = 0  # 当前玩家的索引
        self.wall = Table()  # 使用 Table 类来生成牌墙
        self.discard_pile = []  # 打出来的牌，可能是别“吃”“碰”在side中，也可能在river里，总之是“明牌”。为后面ai判断出牌准备
        self.dealer = None  # 庄家属性
        self.winner = None
        self.winning_tile = None  # "胡"那张牌
        self.remaining_tiles = 136
        self.is_game_over = False
        self.gui = gui
        self.circle = 1  # 局数
        self.mouse_clicked = False  # 轮到人类玩家出牌，设置允许鼠标点击
        self.win_type = None  # 表示赢牌的类型：自摸还是点炮

    def current_player(self):
        return self.players[self.current_player_index]

    def determine_dealer(self):
        if self.circle == 1:
            # 第一局随机选择庄家
            self.dealer = random.choice(self.players)
        else:
            # 从第二局开始，判断上一局的赢家
            if self.winner == self.dealer:
                # 赢家是上一局的庄家，继续连庄
                self.dealer = self.winner
            else:
                # 按顺序轮流坐庄
                current_dealer_index = self.players.index(self.dealer)
                self.dealer = self.players[(current_dealer_index + 1) % len(self.players)]
            # 完成“庄家”设定后复位None值
            self.winner = None

        self.current_player_index = self.players.index(self.dealer)

        msg = f"庄家是 {self.dealer.name}"
        print(msg)

    def start_game(self):
        # 初始化牌墙
        self.init_wall()
        # 随机选择庄家
        self.determine_dealer()
        # 设置庄家为当前玩家
        self.current_player_index = self.players.index(self.dealer)
        # 庄家抓牌
        self.deal_tiles(self.current_player(), 14)
        # 其余玩家抓牌
        for player in self.players:
            if player != self.current_player():
                self.deal_tiles(player, 13)
        # 对每个玩家的手牌进行排序
        for player in self.players:
            player.sort_hand()
        # 打印游戏状态
        self.print_game_state()

    def determine_and_display_discarded_tile(self):
        # 检查是否有玩家胡牌
        if self.winner:
            return
        # 检查牌墙是否为空
        if self.wall.remaining_tiles() == 0:
            print("牌墙已空，流局！")
            # 这里可以添加流局的处理逻辑，比如统计各个玩家的得分情况等
            self.circle += 1
            self.is_game_over = True  # 触发While True 循环中将判断执行reset_game()
            return
        current_player = self.current_player()
        # 如果玩家已经立直，则不考虑杠，只考虑胡牌和打出这张牌
        if current_player.riichi_flag:
            # 如果当前玩家已经听牌，则判断抓到的牌是否是听的牌
            if current_player.drawn_tile.text in current_player.riichi_list:
                # 如果抓到的牌是听的牌，则判定胡牌
                self.win_type = 'self_drawn'
                current_player.hand.remove(current_player.drawn_tile)  # 避免show_scores时 显示多一张牌。因为自摸时这张胡牌已经加入到手牌。
                # current_player.hand.pop()  # 移除手牌中的最后一个成员，也就是刚抓上来的那张牌，这样避免对倒时移除掉中间的同张牌。
                self.handle_win(current_player.drawn_tile, current_player)
            else:
                # 如果抓到的牌不是听的牌，则直接打出这张牌
                self.discard_tile(current_player, current_player.drawn_tile)
            return  # 返回，避免执行kong后再remove掉tile时报错

        if isinstance(current_player, Bot):
            # 如果是 Bot 类玩家，AI算法打牌
            tile_to_discard = current_player.make_decision(self.discard_pile)
            # 测试流局，随机出牌
            # tile_to_discard = random.choice(current_player.hand)
            self.discard_tile(current_player, tile_to_discard)
        else:
            # 如果是人类玩家，由MouseButtonDown事件处理
            # self.gui.render_player_hand(current_player)
            self.mouse_clicked = True

    def next_turn(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        print(f"当前玩家索引: {self.current_player_index}")

    def draw_end(self):
        # 在游戏结束且流局时，渲染流局图片
        if self.is_game_over and self.remaining_tiles == 0:
            # 调用 render_game_state 方法，渲染当前游戏状态
            self.gui.render_game_state(self.dealer, self.is_game_over)

            # 加载流局图片
            draw_pic = pygame.image.load( resource_path(os.path.join("pic", "end.png"))).convert_alpha()
            # 获取屏幕中心坐标
            screen_center = (self.gui.screen.get_width() // 2, self.gui.screen.get_height() // 2)
            # 获取流局图片的位置
            draw_rect = draw_pic.get_rect(center=screen_center)
            # 在屏幕中心绘制流局图片
            self.gui.screen.blit(draw_pic, draw_rect)

            self.gui.display_message("牌墙已空，无人胡牌！")
            # 输出文本 加上之后“重新开始”按钮不停地闪烁
            # self.gui.draw_remaining_tiles(self.wall.remaining_tiles(), self.circle)

    def draw_tile(self):
        # 摸牌
        current_player = self.current_player()
        tile = self.wall.pop()
        current_player.hand.append(tile)
        # 为了给人类显示新抓到牌
        # if current_player.position == "南":
        current_player.drawn_tile = tile

        print(f"{current_player.name} 摸了一张牌: {tile.text}")
        if len(current_player.riichi_list) > 0:
            print(f"{current_player.name} 听牌: {current_player.riichi_list}")

        # 更新剩余牌数
        self.remaining_tiles -= 1

        # 检查是否摸到了杠牌，如果已经上听不能再杠，否则破坏了现有牌型导致听牌失效
        if not current_player.riichi_flag:
            if current_player.hand.count(tile) == 4 or current_player.side.count(tile) == 3:
                # 检查是否摸到了杠牌
                self.handle_kong(current_player, tile)
                self.draw_tile()  # 如果杠了牌，继续摸一张牌

    def init_wall(self):
        # 初始化麻将牌墙，一共 136 张牌，包括万、条、筒和字牌
        self.wall.generate_tiles()

    def deal_tiles(self, player, count):
        # 给玩家发牌
        for _ in range(count):
            tile = self.wall.pop()
            self.remaining_tiles -= 1
            player.hand.append(tile)

    def discard_tile(self, player, tile):
        if tile in player.hand:
            player.hand.remove(tile)
            self.discard_pile.append(tile)
            msg = f"{player.name} 打出了 {tile.text}"
            # 显示信息
            self.gui.display_message(msg)
            # 打印调试信息
            print(msg)
            # 在屏幕中央显示这张牌
            self.gui.display_discarded_tile(tile)
            self.gui.draw_remaining_tiles(self.wall.remaining_tiles(),self.circle)
            time.sleep(1)  # 影响人类玩家出牌时间和鼠标点击
            self.handle_discard(player, tile)
        else:
            # 添加调试输出
            print(f"Error: Tried to remove tile {tile} that is not in player {player.name}'s hand")
            print(f"Player {player.name}'s hand: {player.hand}")
            print(f"Tile to remove: {tile}")
            raise ValueError(f"Cannot discard tile {tile}: not in hand")

    def handle_discard(self, discard_player, tile):
        """处理玩家打出一张牌后的吃碰杠胡操作判断"""
        # 检查是否有玩家可以胡牌
        for other_player in self.players:
            if other_player != discard_player and other_player.check_win(tile):
                self.win_type = 'discarded'
                self.handle_win(tile, other_player, discard_player)
                discard_player.fangchong = True
                return

        # 检查当前玩家是否可以宣告听牌
        if discard_player.check_riichi():
            discard_player.riichi_flag = True

        discard_player.drawn_tile = None  # drawn_tile如果不重置，下次发生“吃”“碰”时，会再次把上次的drawn_tile牌移到最后

        # 检查其他玩家是否可以碰牌
        for other_player in self.players:
            if other_player != discard_player and not other_player.riichi_flag:
                if other_player.check_pong(tile):  # 检查是否可以碰牌
                    if isinstance(other_player, Player) and other_player.position == "南":
                        # 如果是人类玩家，则显示按钮并等待点击
                        self.gui.action_buttons["碰"].draw(self.gui.screen)
                        self.gui.action_buttons["取消"].draw(self.gui.screen)
                        pygame.display.flip()
                        # 等待玩家点击按钮
                        waiting_for_click = True
                        while waiting_for_click:  # 使用布尔变量控制循环
                            for event in pygame.event.get():
                                if event.type == pygame.MOUSEBUTTONDOWN:
                                    mouse_pos = pygame.mouse.get_pos()
                                    if self.gui.action_buttons["碰"].rect.collidepoint(mouse_pos):  # 标记修改点
                                        self.handle_pong(other_player, tile)  # 处理碰牌操作
                                        return
                                    elif self.gui.action_buttons["取消"].rect.collidepoint(mouse_pos):  # 标记修改点
                                        waiting_for_click = False  # 设置为 False 以退出循环
                                        break  # 取消吃牌，直接进入下一轮
                    else:
                        # 如果是 AI 玩家，则直接处理碰牌操作
                        self.handle_pong(other_player, tile)  # 处理碰牌操作
                        return

                # 检查是否可以杠牌
                if other_player.check_kong(tile):
                    self.handle_kong(other_player, tile)  # 处理杠牌操作
                    self.draw_tile()
                    return

        # 检查其他玩家是否可以吃牌
        # “吃”的优先级比较低, 而且只能是下家吃
        next_player_index = (self.current_player_index + 1) % len(self.players)
        next_player = self.players[next_player_index]
        if not next_player.riichi_flag and next_player.check_chow(tile):
            chow_combinations = next_player.get_chow_combinations(tile)
            # 即便Player是Bot玩家，这行表达式会返回 True，因为Bot类是从Player类继承而来的，
            # 所以Bot的实例也是Player类的实例（所以必须加条件“南”）或者给Player加一个属性：self.type = "human" / "bot"
            if isinstance(next_player, Player) and next_player.position == "南":  # 是人类玩家
                if len(chow_combinations) == 1:
                    # 如果是人类玩家，则显示按钮并等待点击
                    self.gui.action_buttons["吃"].draw(self.gui.screen)
                    self.gui.action_buttons["取消"].draw(self.gui.screen)
                    pygame.display.flip()
                    # 等待玩家点击按钮
                    waiting_for_click = True
                    while waiting_for_click:  # 使用布尔变量控制循环
                        for event in pygame.event.get():
                            if event.type == pygame.MOUSEBUTTONDOWN:
                                mouse_pos = pygame.mouse.get_pos()
                                if self.gui.action_buttons["吃"].rect.collidepoint(mouse_pos):  # 标记修改点
                                    self.handle_chow(next_player, tile, chow_combinations[0])  # 标记修改点
                                    return
                                elif self.gui.action_buttons["取消"].rect.collidepoint(mouse_pos):  # 标记修改点
                                    waiting_for_click = False  # 设置为 False 以退出循环
                                    break  # 取消吃牌，直接进入下一轮
                else:
                    combination_rects = self.show_chow_combinations(next_player, tile)
                    if combination_rects:
                        self.gui.action_buttons["取消"].draw(self.gui.screen)
                        pygame.display.flip()
                        waiting_for_click = True
                        selected_combination = None
                        while waiting_for_click:
                            for event in pygame.event.get():
                                if event.type == pygame.MOUSEBUTTONDOWN:
                                    mouse_pos = pygame.mouse.get_pos()
                                    for rect, combination in combination_rects:
                                        if rect.collidepoint(mouse_pos):  # 检查点击的是否为某个组合
                                            selected_combination = combination
                                            break
                                    if selected_combination:
                                        self.handle_chow(next_player, tile, selected_combination)  # 处理吃牌并传入选择的组合
                                        return
                                    elif self.gui.action_buttons["取消"].rect.collidepoint(mouse_pos):
                                        waiting_for_click = False  # 取消吃牌，直接进入下一轮
                                        break
            else:
                # 如果是 AI 玩家，则直接处理吃牌操作
                self.handle_chow(next_player, tile, chow_combinations[0])
                return

        # 如果没有任何玩家吃碰杠胡，则进入下一个玩家的回合
        discard_player.river.append(tile)
        self.next_turn()
        self.draw_tile()

    def show_chow_combinations(self, player, tile):
        """显示吃牌组合"""
        chow_combinations = player.get_chow_combinations(tile)
        if len(chow_combinations) > 1:
            combination_rects = []  # 用于存储每个组合的矩形区域及其对应的组合

            screen_width = self.gui.screen.get_width()
            tile_width = chow_combinations[0][0].image.get_width()
            total_width = (tile_width * 3 + 10) * len(chow_combinations) - 10  # 每个组合之间的间距为10像素

            x_start = (screen_width - total_width) // 2  # 计算起始X位置，使所有组合居中

            # 显示所有吃牌组合
            for i, combination in enumerate(chow_combinations):
                x_offset = x_start + (tile_width * 3 + 10) * i  # 计算每个组合的X位置
                for j, t in enumerate(combination):
                    position = (x_offset + j * tile_width, 360)  # 每张牌的X位置相差tile_width像素，Y位置固定
                    self.gui.show_tile(t, position)  # 显示每个组合中的Tile
                    if j == 0:  # 只需要记录每个组合的第一个Tile的rect即可
                        rect = pygame.Rect(position[0], position[1], tile_width * 3, t.image.get_height())
                        combination_rects.append((rect, combination))

            self.gui.action_buttons["取消"].draw(self.gui.screen)
            pygame.display.flip()

            return combination_rects  # 返回包含组合矩形区域及其对应组合的列表

        return []

    def play_sound(self, sound_file):
        """播放音频文件"""
        pygame.mixer.music.load(sound_file)
        pygame.mixer.music.play()

    def handle_pong(self, pong_player, tile):
        """处理碰牌操作"""
        pong_player.pong(tile)
        self.play_sound(resource_path(os.path.join("sound", "pong.mp3")))  # 播放音频文件
        self.current_player_index = self.players.index(pong_player)

    def handle_kong(self, kong_player, tile):
        """处理杠牌操作"""
        # 正常“碰”杠
        # if kong_player.hand.count(tile) == 3:
        kong_player.kong(tile)
        self.play_sound(resource_path(os.path.join("sound", "kong.mp3")))  # 播放音频文件
        self.current_player_index = self.players.index(kong_player)

    def handle_chow(self, chow_player, tile, combination):
        """处理吃牌操作"""
        # 调用Player类的chow方法，传递具体的组合
        chow_player.chow(tile, combination)
        self.play_sound(resource_path(os.path.join("sound", "chow.mp3")))  # 播放音频文件
        # 进行下一轮操作
        self.next_turn()

    def handle_win(self, tile, win_player, discard_player=None):
        """处理胡牌操作"""
        self.winner = win_player
        # self.winner.hand.append(tile) # 胡牌加入手牌，以正确计算番数，否则杠牌缺杠
        self.is_game_over = True  # 触发While True 循环中将判断执行reset_game()
        self.gui.score_button_drawn = True  # 显示统计分数按钮

        if self.win_type == 'discarded':
            msg = f"{discard_player.name} 放炮 {tile.text}，{win_player.name} 胡牌！"
            self.play_sound(resource_path(os.path.join("sound", "win.mp3")))  # 播放音频文件
        elif self.win_type == 'self_drawn':
            msg = f"{win_player.name} 自摸 {tile.text} 胡牌！"
            self.play_sound(resource_path(os.path.join("sound", "selfwin.mp3")))  # 播放音频文件

        self.winning_tile = tile
        self.gui.render_game_state(self.dealer, self.is_game_over)  # 赢了，明牌显示player手牌，以确认胡牌牌型

        self.gui.display_message(msg, 'top')
        print(msg)
        self.print_game_state()  # 此时game_over == true, 没有输出剩余牌信息
        # 计算分数
        fan, messages = self.calculate_fan(win_player)
        self.calculate_score(win_player, discard_player, fan, self.win_type)

    def is_ponponhu(self, tiles):
        """检查是否有4个刻子"""
        # 统计每个牌的数量
        tile_counts = Counter(tiles)
        triplet_count = 0
        pair_count = 0

        # 统计每种牌的数量
        for count in tile_counts.values():
            if count == 3:
                triplet_count += 1
            elif count == 2:
                pair_count += 1

        # 如果有4个刻子并且有1个对子
        return triplet_count == 4 and pair_count == 1

    def calculate_fan(self, player):
        messages = [f"第 {self.circle} 局", f"赢家： {self.winner.name} "]  # 存储每个规则的解释消息

        def add_message(reason, points):
            messages.append(f"{reason}  加 {points} 番")

        # 计算赢牌玩家的番数
        fan = 0
        # “庄”加一番
        if self.winner == self.dealer:
            fan += 1
            add_message("庄家赢: ", 1)

        if self.dealer.fangchong:
            fan += 1
            add_message("庄点炮: ", 1)

        if len(self.winner.riichi_list) == 1:
            fan += 2
            add_message("胡单张: ", 2)
        else:
            fan += 1
            add_message("平胡：", 1)

        # 手把一加一番
        if len(self.winner.hand) == 1:
            fan += 1
            add_message("手把一：", 1)

        # 不求人加一番
        if len(self.winner.side) == 0:
            fan += 1
            add_message("门前清: ", 1)

        # 如果 hand 或 side 牌里有中发白刻子，加一番
        # 判断中发白刻子
        zfb_tiles = [Y(1), Y(2), Y(3), ]  # 中、发、白的牌对象
        for zfb_tile in zfb_tiles:
            if player.hand.count(zfb_tile) >= 3 or player.side.count(zfb_tile) >= 3:  # 如果只是等于就会把中发白杠牌时漏掉
                fan += 1
                add_message("中发白: ", 1)

        # 如果所有手牌里有4个相同的牌（也可能“碰”一副刻子+手里一副顺子也可以算“杠”），加一番
        tiles = self.winner.side + self.winner.hand
        tiles.append(self.winning_tile)  # wining_tile不在手牌里，需要加上再判断，否则杠数缺牌少计算一番
        # 使用一个集合 counted_tiles 记录已经统计过的 Tile（相当于SQL语句里 distinct tile），确保每种 Tile 只统计一次。从而避免重复增加番数
        counted_tiles = set()  # 记录已经统计过的牌
        for tile in tiles:
            # 遍历 tiles，如果某种 Tile 数量为4且未统计过，则增加番数，并将该 Tile 添加到 counted_tiles。
            if tile not in counted_tiles and tiles.count(tile) == 4:
                fan += 1
                add_message("杠牌: ", 1)
                counted_tiles.add(tile)  # 将该牌添加到已统计集合中

        # 如果是“碰碰胡”
        if self.is_ponponhu(tiles):
            fan += 3
            add_message("碰碰胡: ", 3)

        # 如果是"请一色"
        kinds = {tile.kind for tile in tiles}
        if len(kinds) == 1:
            fan += 5
            add_message("清一色: ", 5)

        num_kinds = {tile.kind for tile in tiles if tile.is_num}
        honor_kinds = {tile.kind for tile in tiles if tile.is_honor}
        if len(kinds) == 2 and len(num_kinds) == 1 and len(honor_kinds) > 0:
            fan += 3
            add_message("混一色: ", 3)

        return fan, messages

    def calculate_score(self, winner, loser, fan, win_type):
        base_score = 2  # 基础分数
        score = base_score * (2 ** fan)
        total_score = 0
        score_msgs = []  # 成绩显示

        if win_type == 'self_drawn':
            # 自摸的情况，所有其他玩家都要支付分数
            for player in self.players:
                if player != winner:
                    if player == self.dealer:
                        player.score.subtract_points(score * 2)  # 庄家支付双倍点数
                        winner.score.add_points(score * 2)
                        total_score += score * 2
                        msg = f"{player.name}（庄家）失去了 {score * 2} 分"
                    else:
                        player.score.subtract_points(score)
                        winner.score.add_points(score)
                        total_score += score
                        msg = f"{player.name} 失去了 {score} 分"
                    score_msgs.append(msg)

        else:
            # 放铳的情况，放铳玩家支付分数
            loser.score.subtract_points(score)
            winner.score.add_points(score)
            msg = f"{loser.name} 失去了 {score} 分"
            score_msgs.append(msg)
            total_score = score

        msg = f"{winner.name} 赢得了 {total_score} 分"
        score_msgs.append(msg)
        self.gui.display_messages(score_msgs, 'center')

    def print_game_state(self):
        self.gui.draw_remaining_tiles(self.wall.remaining_tiles(),self.circle)
        # 打印当前游戏状态，包括玩家手牌和弃牌堆
        msg = "当前游戏状态："
        for player in self.players:
            msg += f"\n{player.name} 手牌: {player.hand}"
        msg += f"\n弃牌堆: {self.discard_pile}"
        # self.display_message(msg)
        # print(msg)

    def reset_game(self):
        # 游戏重新初始化的逻辑，包括重置所有游戏状态
        self.is_game_over = False  # 重置游戏结束的标志
        self.current_player_index = 0
        self.discard_pile = []
        self.wall = Table()
        # self.dealer = None
        # self.winner = None
        self.winning_tile = None
        self.remaining_tiles = 136
        for player in self.players:
            player.reset()
        # 重新初始化牌墙等游戏状态
        self.start_game()

    def handle_mouse_button_down(self):
        if self.mouse_clicked:  # 只有当鼠标未点击时才处理
            print('Mouse down')
            mouse_pos = pygame.mouse.get_pos()
            for player in self.players:
                if isinstance(player, Player) and player.position == "南":
                    x, y = 300, 815
                    for tile in player.hand:
                        tile_rect = tile.rect.move(x, y)
                        if tile_rect.collidepoint(mouse_pos):
                            self.discard_tile(player, tile)
                            self.mouse_clicked = False  # 设置鼠标点击标志为False
                            return
                        x += 35

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.MOUSEMOTION:
                self.gui.handle_mouse_hover(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.is_game_over:
                    if self.gui.reset_button.rect.collidepoint(event.pos):
                        self.circle += 1  # 游戏次数增加1轮
                        self.reset_game()
                    elif self.gui.score_button.rect.collidepoint(event.pos):
                        # 计算分数
                        fan, messages = self.calculate_fan(self.winner)
                        self.gui.show_scores(self.winner, self.winning_tile, messages)
                    elif self.gui.quit_button.rect.collidepoint(event.pos):
                        pygame.quit()
                        sys.exit()
                else:
                    self.handle_mouse_button_down()
        return True

    # 在 handle_mouse_button_down 方法中，通过 pygame.mouse.get_pos() 获取到了鼠标的位置mouse_pos。
    # 然后，方法进入了一个循环，遍历了所有的玩家，找到了当前玩家的手牌，然后检查鼠标是否在这些手牌的区域内点击了下去。 在内部循环中，x 和 y
    # 变量被初始化为手牌的起始坐标，然后逐个将每张手牌的矩形区域向右移动，并检查鼠标点击位置是否在这个矩形区域内。这个 x 和 y 的作用就是用来确定每张手牌的位置的偏移量。

    def update(self):
        # 更新游戏状态
        if not self.is_game_over:
            # 在每次循环迭代时更新游戏状态并渲染新的帧
            self.gui.render_game_state(self.dealer, self.is_game_over)
            self.determine_and_display_discarded_tile()

    def render(self):
        # 只有在游戏未结束时才渲染按钮
        if self.is_game_over:
            self.draw_end()
            if self.remaining_tiles == 0:
                self.gui.reset_button.draw(self.gui.screen)
            if self.gui.score_button_drawn:
                self.gui.score_button.draw(self.gui.screen)
        else:
            # 显示游戏状态信息
            self.print_game_state()
        pygame.display.flip()


# 主函数
def main():
    # 创建玩家
    player1 = Bot("Bot1", "东")  # 位置 东 表示左方玩家
    player2 = Player("Player", "南")  # 位置 南 表示下方玩家
    player3 = Bot("Bot2", "西")  # 位置 西 表示右方玩家
    player4 = Bot("Bot3", "北")  # 位置 北 表示上方玩家

    # 打开日志文件，准备写入
    log_file = open("game.log", "w")
    # 重定向标准输出流到日志文件
    sys.stdout = log_file
    # 初始化游戏
    gui = GUI([player1, player2, player3, player4])
    game = Game(gui)
    game.start_game()

    # 游戏循环
    running = True
    while running:
        running = game.handle_events()
        game.update()
        game.render()
    # 退出 Pygame
    pygame.quit()
    # 记得在程序结束时关闭日志文件
    #log_file.close()
    sys.exit()


if __name__ == "__main__":
    main()

# main() --> 初始化玩家和GUI --> 开始游戏 (game.start_game())
#         |--> 游戏循环开始 (while running)
#             |--> 处理事件 (game.handle_events())
#             |     |--> 如果有退出事件，设置 running 为 False
#             |     |--> 如果有鼠标点击事件，处理玩家出牌 (game.handle_mouse_button_down())
#             |--> 更新游戏状态 (game.update())
#             |     |--> 检查游戏是否结束 (game.is_game_over)
#             |     |--> 如果游戏未结束，更新当前玩家状态 (game.determine_and_display_discarded_tile())
#             |--> 渲染游戏状态 (game.render())
#                   |--> 显示当前游戏状态 (game.print_game_state())
#                   |--> 如果游戏结束，显示流局图片 (game.draw_end())
#
# game.start_game() --> 初始化牌墙 (game.init_wall())
#                   --> 确定庄家 (game.determine_dealer())
#                   --> 给庄家发14张牌 (game.deal_tiles())
#                   --> 给其他玩家发13张牌 (game.deal_tiles())
#                   --> 排序玩家手牌 (player.sort_hand())
#                   --> 打印游戏状态 (game.print_game_state())
#
# 摸牌 (game.draw_tile()) --> 从牌墙取一张牌并添加到当前玩家手牌
#                         --> 如果是庄家，显示牌
#                         --> 检查是否胡牌、杠、碰
#                         --> 如果没有胡牌、杠、碰，打出这张牌 (game.discard_tile())
#
# 打出牌 (game.discard_tile()) --> 移动牌到弃牌堆
#                             --> 检查其他玩家是否可以吃、碰、杠、胡 (game.handle_discard())
#                             --> 如果没有玩家可以操作，进入下一个玩家回合 (game.next_turn())
#                             --> 当前玩家摸牌 (game.draw_tile())

# Game 类功能概述
# 属性：
#
#     players: 玩家列表
#     current_player_index: 当前玩家的索引
#     wall: 牌墙对象，生成牌墙
#     discard_pile: 打出来的牌，为 AI 判断出牌准备
#     dealer: 庄家属性
#     winner: 胜利者
#     winning_tile: "胡"的那张牌
#     remaining_tiles: 剩余牌数
#     is_game_over: 游戏是否结束
#     gui: GUI 对象
#     circle: 局数
#     mouse_clicked: 人类玩家出牌时允许鼠标点击
#     win_type: 表示赢牌的类型（自摸或点炮）
#
# 方法：
#
#     __init__: 初始化游戏类
#     current_player: 获取当前玩家
#     determine_dealer: 随机选择庄家
#     start_game: 开始游戏，初始化牌墙，分发牌并打印游戏状态
#     determine_and_display_discarded_tile: 确定并展示打出的牌，处理立直玩家的出牌逻辑
#     next_turn: 进入下一个玩家的回合
#     draw_end: 游戏结束且流局时渲染流局图片
#     draw_tile: 摸牌逻辑
#     init_wall: 初始化麻将牌墙
#     deal_tiles: 给玩家发牌
#     discard_tile: 玩家打牌逻辑
#     handle_discard: 处理打牌后的吃碰杠胡操作判断
#     show_chow_combinations: 显示吃牌组合
#     handle_pong: 处理碰牌操作
#     handle_kong: 处理杠牌操作
#     handle_chow: 处理吃牌操作
#     handle_win: 处理胡牌操作
#     is_ponponhu: 检查是否有4个刻子+1对子
#     calculate_fan: 计算赢家的番数
#     calculate_score: 计算分数
#
# 代码逻辑总结
#
#     初始化和开始游戏：
#         初始化牌墙并分发牌。
#         随机选择庄家并设置当前玩家为庄家。
#         庄家抓14张牌，其他玩家抓13张牌。
#         对每个玩家的手牌进行排序并打印游戏状态。
#
#     游戏进行：
#         当前玩家摸牌。
#         判断玩家是否能胡牌或是否已经听牌。
#         处理玩家的杠牌、碰牌和吃牌操作。
#         更新当前玩家索引并进入下一轮。
#
#     游戏结束：
#         检查是否有玩家胡牌或牌墙已空。
#         根据玩家赢牌类型（自摸或点炮）计算分数并更新各玩家的分数。
#         渲染流局图片或游戏结束状态。
