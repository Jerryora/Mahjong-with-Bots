from ai import *

# 全局参数设定

# 定义Button 文字颜色
WHITE = (255, 255, 255)
BLACK = (50, 50, 50)
GRAY = (200, 200, 200)
RED = (255, 0, 0)

# 偏移量常量
TILE_WIDTH = 35  # 牌的宽度
TILE_HEIGHT = 38  # 牌的高度

class Button:
    def __init__(self, x, y, width, height, text, font, text_color, button_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.text_color = text_color
        self.button_color = button_color
        self.clicked = False  # 新增的 clicked 属性，默认为 False

    def draw(self, screen):
        # 绘制按钮
        pygame.draw.rect(screen, GRAY, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)  # 边框
        font_surface = self.font.render(self.text, True, self.text_color)
        font_rect = font_surface.get_rect(center=self.rect.center)
        screen.blit(font_surface, font_rect)


class GUI:
    def __init__(self, players):
        pygame.init()
        self.screen_width = 1200
        self.screen_height = 900
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.background = pygame.image.load(resource_path(os.path.join("pic", "back.png"))).convert()
        self.font = pygame.font.Font(resource_path(os.path.join("font", "mahjong.ttf")), 28)
        self.players = players
        self.hovered_tile = None  # 用于存储当前悬停的牌
        self.reset_button = Button(1000, 760, 150, 50, "重新开始", self.font, BLACK, GRAY)
        self.score_button = Button(1000, 700, 150, 50, "分数统计", self.font, BLACK, GRAY)  # 添加分数统计按钮
        self.score_button_drawn = False  # 添加标记以跟踪是否已经绘制过分数统计
        self.quit_button = Button(1000, 820, 150, 50, "结束游戏", self.font, BLACK, GRAY)
        self.action_buttons = {
            "吃": Button(1000, 800, 50, 50, "吃", self.font, BLACK, GRAY),
            "碰": Button(1050, 800, 50, 50, "碰", self.font, BLACK, GRAY),
            "取消": Button(1100, 800, 80, 50, "取消", self.font, BLACK, GRAY)
        }

    def fill_background(self):
        for y in range(0, self.screen_height, self.background.get_height()):
            for x in range(0, self.screen_width, self.background.get_width()):
                self.screen.blit(self.background, (x, y))

    def write(self, msg="pygame is cool", color=WHITE, size=28):
        mjtext = self.font.render(msg, True, color)
        mjtext = mjtext.convert_alpha()
        return mjtext

    def show_scores(self, player, winning_tile, messages):
        self.score_button_drawn = False
        self.fill_background()

        # 绘制手牌标识
        text_surf = self.font.render("手牌：", True, WHITE)
        text_rect = text_surf.get_rect(topleft=(50, 145))
        self.screen.blit(text_surf, text_rect)

        # 绘制手牌
        x_offset = 150
        y_offset = 145

        for tile in player.hand:
            self.screen.blit(tile.image, (x_offset, y_offset))
            x_offset += tile.rect.width + 1

        # 绘制吃牌标识
        text_surf = self.font.render("吃牌：", True, WHITE)
        text_rect = text_surf.get_rect(topleft=(50, 200))
        self.screen.blit(text_surf, text_rect)

        # 绘制吃牌
        x_offset = 150
        y_offset = 200

        for tile in player.side:
            self.screen.blit(tile.image, (x_offset, y_offset))
            x_offset += tile.rect.width + 1

        # 绘制胡牌标识
        text_surf = self.font.render("胡牌：", True, WHITE)
        text_rect = text_surf.get_rect(topleft=(50, 255))
        self.screen.blit(text_surf, text_rect)

        # 绘制胡牌
        self.screen.blit(winning_tile.image, (150, 255))

        # 绘制 messages[0] 在最上面中间位置
        if messages:
            text_surf = self.font.render(messages[0], True, WHITE)
            text_rect = text_surf.get_rect(center=(self.screen_width // 2, 50))
            self.screen.blit(text_surf, text_rect)

        # 绘制messages
        message_y_offset = 350
        for message in messages[1:]:
            text_surf = self.font.render(message, True, WHITE)
            text_rect = text_surf.get_rect(topleft=(50, message_y_offset))
            self.screen.blit(text_surf, text_rect)
            message_y_offset += text_surf.get_height() + 10

        # 绘制scores
        scores = "\n".join([f"{p.name} 积分: {p.score}" for p in self.players])
        score_lines = scores.split('\n')

        y_offset = message_y_offset + 20  # 留出一些空间

        for i, line in enumerate(score_lines):
            text_surf = self.font.render(line, True, WHITE)
            text_rect = text_surf.get_rect(topleft=(50, y_offset + i * 40))
            self.screen.blit(text_surf, text_rect)

        # 绘制重新开始和结束游戏按钮
        self.reset_button.draw(self.screen)
        self.quit_button.draw(self.screen)

    def draw_remaining_tiles(self, remaining_tiles, circle):
        renum_loc = (self.screen.get_width() // 2 - 140, 10)
        remaining_tiles_text = self.write(f"第 {circle} 局   剩余牌数: {remaining_tiles}", color=(255, 255, 255))
        self.screen.blit(remaining_tiles_text, renum_loc)
        pygame.display.flip()

    def display_message(self, message, position='center'):
        # 创建一个表面以容纳文本
        text_surface = self.write(message)
        # 获取文本表面的矩形区域
        text_rect = text_surface.get_rect()

        if position == 'top':
            text_rect.center = (self.screen.get_width() // 2, self.screen.get_height() // 2 - 40)  # 用center属性，文字显示在中心
        elif position == 'center':
            text_rect.center = (self.screen.get_width() // 2, self.screen.get_height() // 2 + 50)
        else:
            raise ValueError("Unsupported position value. Use 'top' or 'center'.")

        # 将背景图绘制到屏幕上
        # 这行需要注释掉，覆盖Bot图标！！！ self.screen.blit(self.background, (0, 0))  # background是全局变量
        # 在文本区域上绘制文本
        self.screen.blit(text_surface, text_rect)

    # 显示多行文字信息
    def display_messages(self, messages, position='center'):
        y_offset = 0
        for message in messages:
            message_surface = self.font.render(message, True, WHITE)
            if position == 'center':
                message_rect = message_surface.get_rect(
                    center=(self.screen.get_width() / 2, self.screen.get_height() / 2 + y_offset))
            elif position == 'top':
                message_rect = message_surface.get_rect(midtop=(self.screen.get_width() / 2, 50 + y_offset))
            self.screen.blit(message_surface, message_rect)
            y_offset += message_surface.get_height() + 5  # Adjust spacing as needed
        pygame.display.flip()

    def display_discarded_tile(self, tile):
        # 显示打出的牌在屏幕中央
        screen_center = (self.screen.get_width() // 2, self.screen.get_height() // 2)
        tile_rect = tile.image.get_rect(center=screen_center)
        self.screen.blit(tile.image, tile_rect)
        pygame.display.flip()

    def handle_reset_button(self):
        if self.reset_button.clicked:
            # 在这里重新初始化游戏
            print("重新初始化游戏")
            self.reset_button.clicked = False

    def show_tile(self, tile, position):
        """在屏幕上的特定位置显示tile"""
        tile_rect = tile.image.get_rect(topleft=position)
        self.screen.blit(tile.image, tile_rect)

    def check_combination_click(self, combination, mouse_pos):
        """检查玩家是否点击了组合上的某张牌"""
        for t in combination:
            tile_rect = t.image.get_rect(topleft=t.position)
            if tile_rect.collidepoint(mouse_pos):
                return True
        return False

    def handle_mouse_hover(self, mouse_pos):
        for player in self.players:
            if isinstance(player, Player) and player.position == "南":
                x, y = 300, 815  # 南牌（人类牌位置）
                for tile in player.hand:
                    tile_rect = tile.rect.move(x, y)
                    if tile_rect.collidepoint(mouse_pos):  # 检查给定的鼠标位置 mouse_pos 是否在矩形区域 tile_rect 内部
                        self.hovered_tile = tile  # 设置为当前麻将牌，并立即返回。
                        return  # 如果有麻将牌与鼠标位置相交，就不再继续遍历其他瓦片，直接返回。
                    x += TILE_WIDTH  # 如果没有交集，更新下一个Tile的绘制位置，使其右移，以便继续绘制下一个麻将牌
        self.hovered_tile = None  # 如果所有瓦片都没有与鼠标位置相交，则将设置为 None

        for action_button in self.action_buttons.values():
            if action_button.clicked:
                action_button.enabled = True
            else:
                action_button.enabled = False

    def render_game_state(self, dealer, is_game_over):
        self.fill_background()

        # 定义各个玩家的位置
        mjloc = [(300, 815), (1100, 120), (250, 90), (50, 120)]  # 分布对应麻将牌布局： 南牌（人类牌位置）-右手牌-北牌位置-左手牌位置
        droploc = [(460, 685), (960, 320), (460, 220), (180, 320)]  # 根据实际情况调整初始位置
        sideloc = [(300, 750), (1025, 120), (250, 150), (120, 120)]  # 吃碰的牌
        riichi_loc = [(70, 820), (1040, 35), (745, 100), (40, 35)]  # 听的位置标志
        hostloc = [(100, 35), (120, 820), (1100, 35), (800, 100)]  # 做庄位置标志

        positions = {
            "东": mjloc[3],
            "南": mjloc[0],
            "西": mjloc[1],
            "北": mjloc[2]
        }

        droplocs = {
            "东": droploc[3],
            "南": droploc[0],
            "西": droploc[1],
            "北": droploc[2]
        }

        sidelocs = {
            "东": sideloc[3],
            "南": sideloc[0],
            "西": sideloc[1],
            "北": sideloc[2]
        }

        riichi_locs = {
            "东": riichi_loc[3],
            "南": riichi_loc[0],
            "西": riichi_loc[1],
            "北": riichi_loc[2]
        }

        # 加载背景和主机图片
        back_image = pygame.image.load(resource_path(os.path.join("pic", "mjback.gif"))).convert()
        host_image = pygame.image.load(resource_path(os.path.join("pic", "host.png"))).convert_alpha()
        riichi_image = pygame.image.load(resource_path(os.path.join("pic", "riichi.png"))).convert_alpha()  # 听牌标志图片

        # 渲染每个玩家的手牌和弃牌
        for player in self.players:
            # 排序玩家的手牌
            player.sort_hand()
            # 如果是南方玩家，把新抓到的牌移动到手牌的最后端
            if player.position == "南" and player.drawn_tile in player.hand:
                player.hand.remove(player.drawn_tile)
                player.hand.append(player.drawn_tile)

        # 渲染每个玩家的手牌和弃牌
        for player in self.players:
            x, y = positions[player.position]
            dx, dy = droplocs[player.position]  # 弃牌堆的初始位置
            sx, sy = sidelocs[player.position]  # 吃牌堆的初始位置
            cards_per_row = 8  # 每行显示的牌数
            card_count = 0  # 记录已经绘制的牌数

            # 显示玩家名字和分数
            name_surface = self.font.render(f"{player.name}", True, WHITE)
            score_surface = self.font.render(f"({player.score})", True, WHITE)
            name_rect = name_surface.get_rect()
            score_rect = score_surface.get_rect()

            if player.position == "南":
                name_rect.midtop = (225, 815)
                score_rect.midtop = (215, 845)
            elif player.position == "北":
                name_rect.midbottom = (750, 90)
                score_rect.midbottom = (815, 90)
            elif player.position == "东":
                name_rect.midleft = (40, 100)
                score_rect.midleft = (100, 100)
            elif player.position == "西":
                name_rect.midright = (1100, 100)
                score_rect.midright = (1170, 100)

            self.screen.blit(name_surface, name_rect)
            self.screen.blit(score_surface, score_rect)

            # 渲染听牌标志
            if player.riichi_flag:
                riichi_rect = riichi_image.get_rect()
                riichi_rect.topleft = riichi_locs[player.position]
                self.screen.blit(riichi_image, riichi_rect)

            # 渲染人类玩家的手牌
            if isinstance(player, Player) and player.position == "南":
                for tile in player.hand:
                    tile_rect = tile.rect.move(x, y)
                    # if self.hovered_tile == tile:  # 如果当前牌被悬停，则上移10像素 这种比较基于对象的内存地址，因此不会影响其他具有相同属性的Tile对象.
                    if tile_rect.collidepoint(pygame.mouse.get_pos()):
                        tile_rect = tile_rect.move(0, -10)
                    self.screen.blit(tile.image, tile_rect)
                    x += TILE_WIDTH

            # 渲染 AI 玩家的手牌
            else:
                for tile in player.hand:
                    back_rect = back_image.get_rect()
                    back_rect.topleft = (x, y)

                    # 根据玩家位置旋转图片
                    if player.position == "东":
                        rotated_back_image = pygame.transform.rotate(back_image, 270)
                        rotated_tile_image = pygame.transform.rotate(tile.image, 270)
                    elif player.position == "西":
                        rotated_back_image = pygame.transform.rotate(back_image, 90)
                        rotated_tile_image = pygame.transform.rotate(tile.image, 90)
                    elif player.position == "北":
                        rotated_back_image = pygame.transform.rotate(back_image, 180)
                        rotated_tile_image = pygame.transform.rotate(tile.image, 0)  # “胡”牌后方便人类看牌
                    else:
                        rotated_back_image = back_image  # 其他位置不旋转
                        rotated_tile_image = tile.image

                    if is_game_over:
                        self.screen.blit(rotated_tile_image, back_rect)  # 结束，明牌显示
                    else:
                        self.screen.blit(rotated_back_image, back_rect)
                        # self.screen.blit(rotated_tile_image, back_rect)  # 调试 明牌显示

                    if player.position in ("东", "西"):
                        y += TILE_HEIGHT
                    else:
                        x += TILE_WIDTH

            # 渲染弃牌
            for tile in player.river:
                tile_rect = tile.image.get_rect()
                tile_rect.topleft = (dx, dy)

                if player.position == "东":
                    discard_image = pygame.transform.rotate(tile.image, 270)
                elif player.position == "西":
                    discard_image = pygame.transform.rotate(tile.image, 90)
                elif player.position == "北":
                    discard_image = pygame.transform.rotate(tile.image, 0)
                else:
                    discard_image = tile.image  # 其他位置不旋转

                    # 获取旋转后的矩形大小
                rotated_rect = discard_image.get_rect()
                rotated_rect.topleft = tile_rect.topleft

                if card_count % cards_per_row == 0 and card_count != 0:
                    # 如果超过每行的牌数，折行显示
                    if player.position == "东":
                        dx += rotated_rect.width
                        dy = droplocs[player.position][1] - rotated_rect.height
                    elif player.position == "西":
                        dx -= rotated_rect.width
                        dy = droplocs[player.position][1] - rotated_rect.height
                    elif player.position == "北":
                        dx = droplocs[player.position][0] - rotated_rect.width
                        dy += rotated_rect.height
                    else:
                        dx = droplocs[player.position][0] - rotated_rect.width
                        dy -= tile_rect.height
                    card_count = 0  # 重置牌数计数

                self.screen.blit(discard_image, tile_rect)

                if player.position in ("东", "西"):
                    dy += TILE_HEIGHT
                else:
                    dx += TILE_WIDTH
                card_count += 1

                # 渲染吃牌
            for tile in player.side:
                tile_rect = tile.image.get_rect()
                tile_rect.topleft = (sx, sy)

                if player.position == "东":
                    side_image = pygame.transform.rotate(tile.image, 270)
                elif player.position == "西":
                    side_image = pygame.transform.rotate(tile.image, 90)
                elif player.position == "北":
                    side_image = pygame.transform.rotate(tile.image, 0)
                else:
                    side_image = tile.image  # 其他位置不旋转

                    # 获取旋转后的矩形大小
                rotated_rect = side_image.get_rect()
                rotated_rect.topleft = tile_rect.topleft
                self.screen.blit(side_image, tile_rect)
                if player.position in ("东", "西"):
                    sy += TILE_HEIGHT
                else:
                    sx += TILE_WIDTH

        # 显示庄家图片
        host_pos = hostloc[list(positions.keys()).index(dealer.position)]  # 获取庄家应该显示的位置。
        self.screen.blit(host_image, host_pos)
        # 刷新屏幕
        # pygame.display.flip()

