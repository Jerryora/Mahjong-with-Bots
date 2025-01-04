import sys
import os
import pygame
import random


def resource_path(relative_path, resource_folder='res'):
    """ 获取资源的绝对路径，适用于开发和打包后的环境 """
    if getattr(sys, 'frozen', False):
        base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    else:
        base_path = os.path.dirname(__file__)

    file_path = os.path.abspath(os.path.join(base_path, resource_folder, relative_path))
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Resource file '{relative_path}' not found at '{file_path}'")
    return file_path


# 定义“牌”父类
class Tile:
    def __init__(self):
        self.kind = 'default'  # 牌的种类：'D'（饼：Dot）、'B'（条：Bamboo）、'C'（万：Character）、'W'（风：Wind）、'Y'（箭:Dragon）
        self.text = ''  # 牌的中文描述
        self.n = 0  # 牌的数字或字牌的标识（1~9为数字牌，1~7为风牌或箭牌） # 设置字牌的number属性为特殊值0
        self.is_num = False  # 是否为数牌
        self.is_honor = False  # 是否为字牌
        self.is_middle = False  # 是否为中张
        self.is_1or9 = False  # 是否为幺九
        self.image = None  # 牌的图像
        self.rect = None  # 牌的矩形区域

    # 当将其传递给print函数时，Python会自动调用tile.__str__()方法来获取其字符串表示形式，然后将其打印出来。
    def __str__(self):
        return f"{self.n}{self.kind}"

    def __repr__(self):
        return self.text

    def __eq__(self, other):
        if isinstance(other, Tile):
            return self.kind == other.kind and self.n == other.n

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.kind, self.n))

    def __len__(self):
        return 1

    def __lt__(self, other):
        return self.n < other.n

    def __gt__(self, other):
        return self.n > other.n

    def __le__(self, other):
        return self.n <= other.n

    def __ge__(self, other):
        return self.n >= other.n


# 定义“饼”牌子类
class D(Tile):
    def __init__(self, n):
        super().__init__()  # 需要手工先调用基类的构造函数
        self.kind = 'D'  # 对象的属性在构造函数中指定
        self.n = n
        self.text = f"{n}饼"
        if 1 <= n <= 9:
            image_file = resource_path(os.path.join("pic", f"MJd{n}.gif"))
            self.image = pygame.image.load(image_file)
            self.rect = self.image.get_rect()
        else:
            self.image = None
        self.is_num = True
        if n == 1 or n == 9:
            self.is_1or9 = True
        else:
            self.is_middle = True


# 在 D, B, C 类的构造函数中，根据 n 的值设置 text 属性。

# 定义“条”牌子类
class B(Tile):
    def __init__(self, n):
        super().__init__()
        self.kind = 'B'
        self.n = n
        self.text = f"{n}条"
        if 1 <= n <= 9:
            image_file = resource_path(os.path.join("pic", f"MJb{n}.gif"))
            self.image = pygame.image.load(image_file)
            self.rect = self.image.get_rect()
        else:
            self.image = None
        self.is_num = True
        if n == 1 or n == 9:
            self.is_1or9 = True
        else:
            self.is_middle = True


# 定义“万”牌子类
class C(Tile):
    def __init__(self, n):
        super().__init__()
        self.kind = 'C'
        self.n = n
        self.text = f"{n}万"
        if 1 <= n <= 9:
            image_file = resource_path(os.path.join("pic", f"MJc{n}.gif"))
            self.image = pygame.image.load(image_file)
            self.rect = self.image.get_rect()
        else:
            self.image = None
        self.is_num = True
        if n == 1 or n == 9:
            self.is_1or9 = True
        else:
            self.is_middle = True


# 定义“风”牌子类
class W(Tile):
    def __init__(self, n):
        super().__init__()
        self.kind = 'W'
        self.n = n
        wind_text = ["东", "南", "西", "北"]   # 使用列表简化 W 类和 Y 类的 text 属性设置。
        self.text = wind_text[n - 1] if 1 <= n <= 4 else ""
        image_file = resource_path(os.path.join("pic", f"MJw{n}.gif")) if 1 <= n <= 4 else None
        self.image = pygame.image.load(image_file)
        self.rect = self.image.get_rect() if self.image else None
        self.is_honor = True
        self.is_1or9 = True


# 定义“中发白”牌子类
class Y(Tile):
    def __init__(self, n):
        super().__init__()
        self.kind = 'Y'
        self.n = n
        dragon_text = ["中", "发", "白"]
        self.text = dragon_text[n - 1] if 1 <= n <= 3 else ""
        image_file = resource_path(os.path.join("pic", f"MJy{n}.gif")) if 1 <= n <= 3 else None
        self.image = pygame.image.load(image_file)
        self.rect = self.image.get_rect() if self.image else None
        self.is_honor = True
        self.is_1or9 = True


class Table:  # 麻将桌类
    def __init__(self):
        self.__table = []

    def generate_tiles(self):
        for i in range(4):  # 每种牌有4张
            for j in range(9):
                self.__table.append(D(j + 1))
                self.__table.append(B(j + 1))
                self.__table.append(C(j + 1))
            for j in range(4):
                self.__table.append(W(j + 1))
            for j in range(3):
                self.__table.append(Y(j + 1))
        random.shuffle(self.__table)

    def pop(self):
        # 从牌墙中弹出一张牌
        if self.remaining_tiles() > 0:
            return self.__table.pop()
        else:
            print("牌堆已空，无法继续抽牌！")
            return None

    def remaining_tiles(self):
        return len(self.__table)

    def draw(self):
        return self.__table.pop()

    @property  # 函数修饰符，将下面函数作为参数
    def table(self):
        return self.__table

    def get_tiles_by_kind(self, kind):
        return [tile for tile in self.__table if tile.kind == kind]

    def get_num_tiles(self):
        return [tile for tile in self.__table if tile.is_num]


def main():
    # 创建两个 Tile 类的实例
    tile1 = Tile()
    tile1.kind = '饼'
    tile1.n = 3

    tile2 = Tile()
    tile2.kind = '饼'
    tile2.n = 3

    # 比较两个实例是否相同
    if tile1 == tile2:
        print("两个实例相同")
    else:
        print("两个实例不同")


if __name__ == "__main__":
    main()
