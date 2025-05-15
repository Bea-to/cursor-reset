import pygame
import random
import sys
import json
import os
from typing import List, Tuple, Dict

# 初始化pygame和混音器
pygame.init()
pygame.mixer.init()

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
YELLOW = (255, 255, 0)

# 游戏设置
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
GRID_SIZE = 20
GRID_WIDTH = WINDOW_WIDTH // GRID_SIZE
GRID_HEIGHT = WINDOW_HEIGHT // GRID_SIZE

# 难度设置
DIFFICULTY = {
    "简单": {"speed": 8, "score_multiplier": 1},
    "中等": {"speed": 12, "score_multiplier": 2},
    "困难": {"speed": 16, "score_multiplier": 3}
}

# 加载音效
def load_sound(filename: str) -> pygame.mixer.Sound:
    try:
        return pygame.mixer.Sound(os.path.join("sounds", filename))
    except:
        print(f"无法加载音效: {filename}")
        return None

# 创建音效目录
if not os.path.exists("sounds"):
    os.makedirs("sounds")

class GameState:
    def __init__(self):
        self.current_difficulty = "中等"
        self.high_scores = self.load_high_scores()
        self.paused = False
        self.game_over = False
        self.mute_sound = False  # 添加静音状态跟踪
        self.sounds = {
            "eat": load_sound("eat.wav"),
            "crash": load_sound("game_over.wav"),
            "move": load_sound("move.wav")
        }
        # 加载并播放背景音乐
        try:
            pygame.mixer.music.load(os.path.join("sounds", "snake_bgm_soft.wav"))
            pygame.mixer.music.set_volume(0.5)  # 设置音量为50%
            pygame.mixer.music.play(-1)  # -1表示循环播放
        except:
            print("无法加载背景音乐")

    def load_high_scores(self) -> Dict[str, int]:
        try:
            with open("high_scores.json", "r") as f:
                return json.load(f)
        except:
            return {"简单": 0, "中等": 0, "困难": 0}

    def save_high_scores(self) -> None:
        with open("high_scores.json", "w") as f:
            json.dump(self.high_scores, f)

    def update_high_score(self, score: int) -> None:
        if score > self.high_scores[self.current_difficulty]:
            self.high_scores[self.current_difficulty] = score
            self.save_high_scores()

    def toggle_pause(self):
        """切换游戏暂停状态"""
        self.paused = not self.paused
        if self.paused:
            pygame.mixer.music.pause()  # 暂停背景音乐
        else:
            pygame.mixer.music.unpause()  # 恢复背景音乐
            
    def toggle_sound(self):
        """切换声音开关状态"""
        self.mute_sound = not self.mute_sound
        if self.mute_sound:
            pygame.mixer.music.set_volume(0)  # 将背景音乐音量设为0
        else:
            pygame.mixer.music.set_volume(0.5)  # 恢复背景音乐音量

class Snake:
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.reset()

    def reset(self) -> None:
        self.length = 1
        self.positions = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = random.choice([UP, DOWN, LEFT, RIGHT])
        self.color = GREEN
        self.score = 0
        self.last_move_time = pygame.time.get_ticks()
        self.move_delay = 1000 // DIFFICULTY[self.game_state.current_difficulty]["speed"]

    def get_head_position(self) -> Tuple[int, int]:
        return self.positions[0]

    def update(self) -> bool:
        current_time = pygame.time.get_ticks()
        if current_time - self.last_move_time < self.move_delay:
            return True

        self.last_move_time = current_time
        cur = self.get_head_position()
        x, y = self.direction
        new = ((cur[0] + x) % GRID_WIDTH, (cur[1] + y) % GRID_HEIGHT)
        
        if new in self.positions[3:]:
            if self.game_state.sounds["crash"] and not self.game_state.mute_sound:
                self.game_state.sounds["crash"].play()
            return False

        self.positions.insert(0, new)
        if len(self.positions) > self.length:
            self.positions.pop()
            if self.game_state.sounds["move"] and not self.game_state.mute_sound:
                self.game_state.sounds["move"].play()
        return True

    def render(self, surface) -> None:
        for i, p in enumerate(self.positions):
            # 蛇头用不同颜色
            color = YELLOW if i == 0 else self.color
            # 绘制圆角矩形
            rect = pygame.Rect(p[0] * GRID_SIZE, p[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            pygame.draw.rect(surface, color, rect, border_radius=5)

class Food:
    def __init__(self):
        self.position = (0, 0)
        self.color = RED
        self.randomize_position()

    def randomize_position(self) -> None:
        self.position = (random.randint(0, GRID_WIDTH-1),
                        random.randint(0, GRID_HEIGHT-1))

    def render(self, surface) -> None:
        # 绘制圆形食物
        center = (self.position[0] * GRID_SIZE + GRID_SIZE//2,
                 self.position[1] * GRID_SIZE + GRID_SIZE//2)
        pygame.draw.circle(surface, self.color, center, GRID_SIZE//2)

# 方向定义
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

def draw_text(surface, text: str, pos: Tuple[int, int], color: Tuple[int, int, int], 
             font_size: int = 36, center: bool = False) -> None:
    font = pygame.font.Font(None, font_size)
    text_surface = font.render(text, True, color)
    if center:
        pos = (pos[0] - text_surface.get_width()//2, pos[1])
    surface.blit(text_surface, pos)

def main():
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption('贪吃蛇')
    clock = pygame.time.Clock()
    
    game_state = GameState()
    snake = Snake(game_state)
    food = Food()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.mixer.music.fadeout(1000)  # 淡出背景音乐
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.mixer.music.fadeout(1000)  # 淡出背景音乐
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_p:  # 暂停
                    game_state.toggle_pause()  # 使用新的暂停方法
                elif event.key == pygame.K_m:  # 静音开关
                    game_state.toggle_sound()  # 使用新的声音开关方法
                elif event.key == pygame.K_r:  # 重新开始
                    snake.reset()
                    food.randomize_position()
                    game_state.game_over = False
                elif event.key == pygame.K_1:  # 切换难度
                    difficulties = list(DIFFICULTY.keys())
                    current_index = difficulties.index(game_state.current_difficulty)
                    game_state.current_difficulty = difficulties[(current_index + 1) % len(difficulties)]
                    snake.reset()
                elif not game_state.paused and not game_state.game_over:
                    if event.key == pygame.K_UP and snake.direction != DOWN:
                        snake.direction = UP
                    elif event.key == pygame.K_DOWN and snake.direction != UP:
                        snake.direction = DOWN
                    elif event.key == pygame.K_LEFT and snake.direction != RIGHT:
                        snake.direction = LEFT
                    elif event.key == pygame.K_RIGHT and snake.direction != LEFT:
                        snake.direction = RIGHT

        if not game_state.paused and not game_state.game_over:
            # 更新蛇的位置
            if not snake.update():
                game_state.game_over = True
                game_state.update_high_score(snake.score)

            # 检查是否吃到食物
            if snake.get_head_position() == food.position:
                snake.length += 1
                score_increase = 10 * DIFFICULTY[game_state.current_difficulty]["score_multiplier"]
                snake.score += score_increase
                if game_state.sounds["eat"] and not game_state.mute_sound:
                    game_state.sounds["eat"].play()
                food.randomize_position()
                while food.position in snake.positions:
                    food.randomize_position()

        # 绘制
        screen.fill(BLACK)
        
        # 绘制网格线
        for x in range(0, WINDOW_WIDTH, GRID_SIZE):
            pygame.draw.line(screen, GRAY, (x, 0), (x, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, GRID_SIZE):
            pygame.draw.line(screen, GRAY, (0, y), (WINDOW_WIDTH, y))

        snake.render(screen)
        food.render(screen)
        
        # 显示分数和最高分
        draw_text(screen, f'得分: {snake.score}', (10, 10), WHITE)
        draw_text(screen, f'最高分: {game_state.high_scores[game_state.current_difficulty]}', 
                 (10, 50), WHITE)
        draw_text(screen, f'难度: {game_state.current_difficulty}', 
                 (WINDOW_WIDTH - 150, 10), WHITE)
        
        # 显示操作说明
        help_text = [
            "方向键: 移动",
            "P: 暂停",
            "M: 声音开关",
            "R: 重新开始",
            "1: 切换难度",
            "ESC: 退出"
        ]
        for i, text in enumerate(help_text):
            draw_text(screen, text, (WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT - 150 + i*30), WHITE)

        # 显示暂停或游戏结束
        if game_state.paused:
            draw_text(screen, "游戏暂停", (WINDOW_WIDTH//2, WINDOW_HEIGHT//2), YELLOW, 48, True)
        elif game_state.game_over:
            draw_text(screen, "游戏结束", (WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 30), RED, 48, True)
            draw_text(screen, f"最终得分: {snake.score}", 
                     (WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 30), WHITE, 36, True)
            draw_text(screen, "按R键重新开始", 
                     (WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 80), WHITE, 36, True)

        pygame.display.update()
        clock.tick(60)

if __name__ == '__main__':
    main() 