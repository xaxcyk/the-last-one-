import arcade
import random
import os
import time
from arcade.particles import FadeParticle, Emitter, EmitMaintainCount
import math

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
TILE_SIZE = 48

FLOOR_COLOR = (20, 20, 20)
WALL_COLORS = [
    (80, 60, 40),
    (70, 70, 70),
    (60, 50, 40),
]
TRAP_COLORS = [
    (150, 50, 50),  #темно-красный
    (180, 70, 70),  #красный
    (200, 100, 100),  #светло-красный
]


class Player(arcade.Sprite): #управление WASD, сбор монет, эффект ловушек
    def __init__(self):
        super().__init__()

        player_path = "assets/sprites/archaeologist.png"
        if os.path.exists(player_path):
            self.texture = arcade.load_texture(player_path)
        else:
            self.texture = arcade.make_soft_circle_texture(18, arcade.color.BLUE, 255, 255)

        self.width = 28
        self.height = 28
        self.base_speed = 4
        self.speed = self.base_speed
        self.coins_collected = 0
        self.coins_needed = 1
        self.total_coins = 5
        self.trapped = False
        self.trap_timer = 0
        self.trap_duration = 2.0
        self.start_x = 0
        self.start_y = 0

    def update_movement(self, keys): #нажатия клавиш WASD/стрелки
        self.change_x = 0
        self.change_y = 0

        if keys[arcade.key.W] or keys[arcade.key.UP]:
            self.change_y = self.speed
        if keys[arcade.key.S] or keys[arcade.key.DOWN]:
            self.change_y = -self.speed
        if keys[arcade.key.A] or keys[arcade.key.LEFT]:
            self.change_x = -self.speed
        if keys[arcade.key.D] or keys[arcade.key.RIGHT]:
            self.change_x = self.speed

    def update(self, delta_time): #обновляет таймер и скорость ловушки
        if self.trapped:
            self.trap_timer -= delta_time
            if self.trap_timer <= 0:
                self.trapped = False
                self.speed = self.base_speed
                self.color = arcade.color.WHITE

    def apply_trap(self): #замедление и смена цвета
        if not self.trapped:
            self.trapped = True
            self.trap_timer = self.trap_duration
            self.speed = self.base_speed * 0.4
            self.color = arcade.color.RED

    def return_to_start(self): #тпшка игрока на начальную позицию
        self.center_x = self.start_x
        self.center_y = self.start_y
        self.change_x = 0
        self.change_y = 0


class Ghost(arcade.Sprite): #призрак

    def __init__(self, maze_grid, maze_start_x, maze_start_y, maze_width, maze_height):
        super().__init__()

        ghost_path = "assets/sprites/Ghosts.png"
        self.width = 28
        self.height = 28

        if os.path.exists(ghost_path):
            try:
                self.texture = arcade.load_texture(ghost_path)
                if self.texture.width > self.width:
                    self.scale = self.width / self.texture.width
                else:
                    self.scale = 1.0
            except Exception:
                ghost_color = (180, 180, 255, 200)
                self.texture = arcade.make_soft_circle_texture(14, ghost_color, 255, ghost_color[3])
                self.scale = 1.0
        else:
            ghost_color = (180, 180, 255, 200)
            self.texture = arcade.make_soft_circle_texture(14, ghost_color, 255, ghost_color[3])
            self.scale = 1.0


        self.speed = random.uniform(1.5, 2.5)
        self.direction = random.choice([0, 90, 180, 270])
        self.change_direction_timer = 0
        self.direction_change_interval = random.uniform(1.5, 3.0)
        self.maze_grid = maze_grid
        self.maze_start_x = maze_start_x
        self.maze_start_y = maze_start_y
        self.maze_width = maze_width
        self.maze_height = maze_height
        self.grid_x = 0
        self.grid_y = 0
        self.pulse_speed = random.uniform(1.5, 2.5)
        self.pulse_time = random.random() * 3.14
        self.base_scale = self.scale

        #избегание застревания
        self.stuck_timer = 0
        self.stuck_threshold = 2.0
        self.last_position_x = 0
        self.last_position_y = 0
        self.position_change_threshold = 5

    def update(self, delta_time): #движение, избежание стен
        self.pulse_time += delta_time * self.pulse_speed
        pulse_factor = 0.9 + 0.1 * math.sin(self.pulse_time)

        if isinstance(self.base_scale, (int, float)):
            self.scale = self.base_scale * pulse_factor
        else:
            self.scale = 1.0 * pulse_factor

        #смена направления
        self.change_direction_timer += delta_time
        if self.change_direction_timer >= self.direction_change_interval:
            self.change_direction_timer = 0
            self.direction_change_interval = random.uniform(1.5, 3.0)
            self.direction = random.choice([0, 90, 180, 270])

        old_x, old_y = self.center_x, self.center_y
        dx = math.cos(math.radians(self.direction)) * self.speed
        dy = math.sin(math.radians(self.direction)) * self.speed
        new_x = self.center_x + dx
        new_y = self.center_y + dy

        new_grid_x = int((new_x - self.maze_start_x) // TILE_SIZE)
        new_grid_y = int((new_y - self.maze_start_y) // TILE_SIZE)

        #границы лабиринта
        if (new_grid_x < 0 or new_grid_x >= self.maze_width or
                new_grid_y < 0 or new_grid_y >= self.maze_height):
            self.direction = (self.direction + 180) % 360
        else: #проверка стен
            if (0 <= new_grid_y < len(self.maze_grid) and
                    0 <= new_grid_x < len(self.maze_grid[0])):

                if self.maze_grid[new_grid_y][new_grid_x] == 1:
                    self.find_free_direction()
                else:
                    self.center_x = new_x
                    self.center_y = new_y
                    self.grid_x = int((self.center_x - self.maze_start_x) // TILE_SIZE)
                    self.grid_y = int((self.center_y - self.maze_start_y) // TILE_SIZE)

        #проверка застревания
        position_changed = (abs(self.center_x - old_x) > self.position_change_threshold or
                            abs(self.center_y - old_y) > self.position_change_threshold)

        if position_changed:
            self.stuck_timer = 0
            self.last_position_x = self.center_x
            self.last_position_y = self.center_y
        else:
            self.stuck_timer += delta_time
            if self.stuck_timer >= self.stuck_threshold:
                self.find_free_direction()
                self.stuck_timer = 0

    def find_free_direction(self): #движение, избегая стены
        possible_directions = []

        for direction in [0, 90, 180, 270]:
            dx = math.cos(math.radians(direction)) * self.speed
            dy = math.sin(math.radians(direction)) * self.speed

            new_x = self.center_x + dx * 2
            new_y = self.center_y + dy * 2

            new_grid_x = int((new_x - self.maze_start_x) // TILE_SIZE)
            new_grid_y = int((new_y - self.maze_start_y) // TILE_SIZE)

            if (0 <= new_grid_x < self.maze_width and
                    0 <= new_grid_y < self.maze_height):

                if self.maze_grid[new_grid_y][new_grid_x] == 0:
                    possible_directions.append(direction)

        if possible_directions:
            self.direction = random.choice(possible_directions)
        else:
            self.direction = (self.direction + 180) % 360



class Coin(arcade.Sprite): #вращающаяся монета

    def __init__(self, center_x, center_y):
        super().__init__()

        coin_path = "assets/sprites/coin10.png"

        if os.path.exists(coin_path):
            try:
                self.texture = arcade.load_texture(coin_path)
                self.width = 25
                self.height = 25
                if self.texture.width > self.width:
                    self.scale = self.width / self.texture.width
                else:
                    self.scale = 1.0
            except Exception:
                self.texture = arcade.make_soft_circle_texture(8, arcade.color.GOLD, 255, 255)
                self.width = 16
                self.height = 16
                self.scale = 1.0
        else:
            self.texture = arcade.make_soft_circle_texture(8, arcade.color.GOLD, 255, 255)
            self.width = 16
            self.height = 16
            self.scale = 1.0

        self.center_x = center_x
        self.center_y = center_y
        self.angle = random.randint(0, 360)
        self.rotation_speed = random.uniform(30, 60)

    def update(self, delta_time): #вращает монету
        self.angle += delta_time * self.rotation_speed


class Trap(arcade.Sprite): #ловушка, замедляющая игрока при касании

    def __init__(self, center_x, center_y):
        super().__init__()

        trap_path = "assets/sprites/impale6.png"

        if os.path.exists(trap_path):
            try:
                self.texture = arcade.load_texture(trap_path)
                self.width = 30
                self.height = 30
                if self.texture.width > self.width:
                    self.scale = self.width / self.texture.width
                else:
                    self.scale = 1.0
            except Exception:
                self.texture = arcade.make_soft_circle_texture(8, random.choice(TRAP_COLORS), 255, 255)
                self.width = 16
                self.height = 16
                self.scale = 1.0
        else:
            self.texture = arcade.make_soft_circle_texture(8, random.choice(TRAP_COLORS), 255, 255)
            self.width = 16
            self.height = 16
            self.scale = 1.0

        self.center_x = center_x
        self.center_y = center_y
        self.angle = 0



def light_fog_mutator(p): #якобы туман
    p.change_y += 0.01
    p.change_x += random.uniform(-0.008, 0.008)

    speed_limit = 0.4
    speed = (p.change_x ** 2 + p.change_y ** 2) ** 0.5
    if speed > speed_limit:
        factor = speed_limit / speed
        p.change_x *= factor
        p.change_y *= factor


class GameView(arcade.View): #начало

    def __init__(self, level_num=1, data_manager=None):
        super().__init__()

        self.level = level_num
        self.max_levels = 3
        self.maze_size = 13
        self.data_manager = data_manager

        self.player = None
        self.scene = None
        self.physics_engine = None
        self.exit = None
        self.fog_emitters = []
        self.maze_grid = None
        self.maze_start_x = 0
        self.maze_start_y = 0
        self.maze_width = 0
        self.maze_height = 0
        self.ghosts = []

        self.background_music = None
        self.music_player = None

        #таймеры
        self.level_start_time = None
        self.current_time = 0
        self.level_completed = False
        self.level_completion_time = 0
        self.timer_running = True

        #результаты
        self.session_final_time = 0
        self.session_final_coins = 0

        #звукиииииииииииииииии
        self.coin_sound = None
        self.load_sounds()

        self.keys = {}
        self.setup_keys()

        self.coins_text = None
        self.level_text = None
        self.time_text = None
        self.session_text = None
        self.trap_status_text = None
        self.ghost_warning_text = None

        #границы
        self.boundary_left = 0
        self.boundary_right = SCREEN_WIDTH
        self.boundary_bottom = 0
        self.boundary_top = SCREEN_HEIGHT

    def on_show_view(self):
        self.play_background_music()
        if not self.player:
            self.setup()

    def on_hide_view(self): #остановка музыки
        self.stop_background_music()

    def load_sounds(self): #звуковые эффекты
        coin_sound_path = "assets/sounds/coin_pickup.wav"
        if os.path.exists(coin_sound_path):
            try:
                self.coin_sound = arcade.load_sound(coin_sound_path)
            except Exception:
                self.coin_sound = None
        else:
            self.coin_sound = None

        music_path = "assets/sounds/background.wav"
        if os.path.exists(music_path):
            try:
                self.background_music = arcade.load_sound(music_path)
            except Exception:
                self.background_music = None
        else:
            self.background_music = None

    def play_background_music(self): #фоновая музыка
        if self.background_music and not self.music_player:
            try:
                self.music_player = self.background_music.play(volume=0.3, loop=True)
            except Exception:
                pass

    def stop_background_music(self): #останавливает фоновую музыку
        if self.music_player:
            try:
                self.music_player.pause()
                self.music_player = None
            except Exception:
                pass

    def setup_keys(self):
        self.keys = {
            arcade.key.W: False,
            arcade.key.S: False,
            arcade.key.A: False,
            arcade.key.D: False,
            arcade.key.UP: False,
            arcade.key.DOWN: False,
            arcade.key.LEFT: False,
            arcade.key.RIGHT: False,
            arcade.key.R: False,
            arcade.key.ESCAPE: False,
        }

    def setup(self): #создает новый уровень
        self.scene = arcade.Scene()
        self.scene.add_sprite_list("Walls", use_spatial_hash=True)
        self.scene.add_sprite_list("Coins", use_spatial_hash=True)
        self.scene.add_sprite_list("Traps", use_spatial_hash=True)
        self.scene.add_sprite_list("Ghosts", use_spatial_hash=True)
        self.scene.add_sprite_list("Exit")

        self.player = Player()

        #настройки сложности по уровням
        if self.level == 1:
            self.player.coins_needed = 1
            self.player.total_coins = 5
        elif self.level == 2:
            self.player.coins_needed = 20
            self.player.total_coins = 30
        elif self.level == 3:
            self.player.coins_needed = 40
            self.player.total_coins = 40

        self.generate_maze()
        self.level_start_time = time.time()
        self.level_completed = False
        self.timer_running = True
        self.completion_countdown = 0.0

        self.coins_text = arcade.Text(
            f"Монеты: {self.player.coins_collected}/{self.player.coins_needed}",
            50, SCREEN_HEIGHT - 10,
            arcade.color.RED, 15
        )

        self.level_text = arcade.Text(
            f"Уровень: {self.level}/{self.max_levels}",
            10, SCREEN_HEIGHT - 5,
            arcade.color.RED, 15
        )

        self.time_text = arcade.Text(
            "Время: 0.0 сек",
            10, SCREEN_HEIGHT - 5,
            arcade.color.GREEN, 15
        )

        self.trap_status_text = arcade.Text(
            "",
            20, SCREEN_HEIGHT - 160,
            arcade.color.RED, 16
        )

    def generate_maze(self): #генерирует лабиринт
        maze_width = self.maze_size
        maze_height = self.maze_size
        self.maze_width = maze_width
        self.maze_height = maze_height

        #загружает лабиринт
        if self.level == 1:
            grid = [
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],
                [1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1],
                [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1],
                [1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
                [1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1],
                [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
                [1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1],
                [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
                [1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
            ]
            start_x, start_y = 1, 1
            exit_x, exit_y = 11, 11

        elif self.level == 2:
            grid = [
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                [1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1],
                [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
                [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
                [1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1],
                [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
                [1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1],
                [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
                [1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1],
                [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
                [1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
            ]
            start_x, start_y = 1, 1
            exit_x, exit_y = 11, 11

        else:
            grid = [
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
                [1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
                [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1],
                [1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
                [1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1],
                [1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1],
                [1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1],
                [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                [1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
            ]
            start_x, start_y = 1, 1
            exit_x, exit_y = 11, 5

        self.maze_grid = grid
        maze_center_x = SCREEN_WIDTH // 2
        maze_center_y = SCREEN_HEIGHT // 2
        maze_start_x = maze_center_x - (maze_width * TILE_SIZE) // 2
        maze_start_y = maze_center_y - (maze_height * TILE_SIZE) // 2

        self.maze_start_x = maze_start_x
        self.maze_start_y = maze_start_y

        #загружает текстурки
        wall_texture_path = "assets/sprites/wall_ruins.jpg"
        wall_texture = None
        if os.path.exists(wall_texture_path):
            try:
                wall_texture = arcade.load_texture(wall_texture_path)
            except:
                wall_texture = None

        wall_width = TILE_SIZE
        wall_height = TILE_SIZE

        #стены лабиринта
        for y in range(maze_height):
            for x in range(maze_width):
                if grid[y][x] == 1:
                    wall = arcade.Sprite()
                    if wall_texture:
                        wall.texture = wall_texture
                        wall.width = wall_width
                        wall.height = wall_height
                    else:
                        wall.color = random.choice(WALL_COLORS)
                        wall.width = wall_width
                        wall.height = wall_height

                    wall.center_x = maze_start_x + x * TILE_SIZE + TILE_SIZE // 2
                    wall.center_y = maze_start_y + y * TILE_SIZE + TILE_SIZE // 2
                    self.scene.add_sprite("Walls", wall)

        #размещает игровой контент
        self.create_coins(grid, maze_width, maze_height, maze_start_x, maze_start_y, start_x, start_y)
        self.create_traps(grid, maze_width, maze_height, maze_start_x, maze_start_y, start_x, start_y, exit_x,
                          exit_y)
        self.create_exit(exit_x, exit_y, maze_start_x, maze_start_y)
        self.create_ghosts(grid, maze_width, maze_height, maze_start_x, maze_start_y, start_x, start_y, exit_x,
                           exit_y)
        self.create_light_fog(maze_start_x, maze_start_y, maze_width, maze_height, grid)

        #стартовая позиция
        player_start_x = maze_start_x + start_x * TILE_SIZE + TILE_SIZE // 2
        player_start_y = maze_start_y + start_y * TILE_SIZE + TILE_SIZE // 2

        self.player.center_x = player_start_x
        self.player.center_y = player_start_y
        self.player.start_x = player_start_x
        self.player.start_y = player_start_y
        self.scene.add_sprite("Player", self.player)

        self.physics_engine = arcade.PhysicsEngineSimple(
            self.player, self.scene["Walls"]
        )

    def create_coins(self, grid, width, height, start_x, start_y, player_x, player_y): #размещение монет
        empty_cells = []
        for y in range(height):
            for x in range(width):
                if grid[y][x] == 0:
                    if not (x == player_x and y == player_y):
                        empty_cells.append((x, y))

        random.shuffle(empty_cells)

        if self.level == 3:
            coin_positions = empty_cells[:self.player.total_coins]
        else:
            coin_positions = empty_cells[:min(self.player.total_coins, len(empty_cells))]

        for x, y in coin_positions:
            center_x = start_x + x * TILE_SIZE + TILE_SIZE // 2
            center_y = start_y + y * TILE_SIZE + TILE_SIZE // 2
            coin = Coin(center_x, center_y)
            self.scene.add_sprite("Coins", coin)

    def create_ghosts(self, grid, width, height, start_x, start_y, player_x, player_y, exit_x, exit_y): #призраки
        if self.level == 1:
            ghost_count = 2
        elif self.level == 2:
            ghost_count = 4
        else:
            ghost_count = 6

        empty_cells = []
        for y in range(height):
            for x in range(width):
                if grid[y][x] == 0:
                    if (not (x == player_x and y == player_y) and
                            not (x == exit_x and y == exit_y) and
                            not (abs(x - player_x) <= 1 and abs(y - player_y) <= 1) and
                            not (abs(x - exit_x) <= 1 and abs(y - exit_y) <= 1)):
                        empty_cells.append((x, y))

        if len(empty_cells) < ghost_count:
            ghost_count = len(empty_cells)

        random.shuffle(empty_cells)
        ghost_positions = empty_cells[:ghost_count]

        for x, y in ghost_positions:
            ghost = Ghost(self.maze_grid, self.maze_start_x, self.maze_start_y, self.maze_width, self.maze_height)
            ghost.center_x = start_x + x * TILE_SIZE + TILE_SIZE // 2
            ghost.center_y = start_y + y * TILE_SIZE + TILE_SIZE // 2
            ghost.grid_x = x
            ghost.grid_y = y
            self.scene.add_sprite("Ghosts", ghost)
            self.ghosts.append(ghost)

    def create_light_fog(self, maze_start_x, maze_start_y, maze_width, maze_height, grid): #туман
        self.fog_emitters.clear()

        fog_colors = [
            (200, 200, 220, 80),
            (180, 180, 200, 90),
            (160, 160, 180, 70),
        ]

        fog_textures = []
        for color in fog_colors:
            for size in [25, 30, 35]:
                texture = arcade.make_soft_circle_texture(size, color, outer_alpha=color[3])
                fog_textures.append(texture)

        for y in range(maze_height):
            for x in range(maze_width):
                if grid[y][x] == 0:
                    if random.random() < 0.4:
                        center_x = maze_start_x + x * TILE_SIZE + TILE_SIZE // 2
                        center_y = maze_start_y + y * TILE_SIZE + TILE_SIZE // 2

                        particle_count = 3
                        if self.level == 2:
                            particle_count = 4
                        elif self.level == 3:
                            particle_count = 5

                        emitter = Emitter(
                            center_xy=(center_x, center_y),
                            emit_controller=EmitMaintainCount(particle_count),
                            particle_factory=lambda e: FadeParticle(
                                filename_or_texture=random.choice(fog_textures),
                                change_xy=(
                                    random.uniform(-0.1, 0.1),
                                    random.uniform(0.02, 0.05)
                                ),
                                lifetime=random.uniform(8.0, 15.0),
                                start_alpha=random.randint(60, 100),
                                end_alpha=10,
                                scale=random.uniform(0.8, 1.2),
                                mutation_callback=light_fog_mutator
                            ),
                        )
                        self.fog_emitters.append(emitter)

    def create_traps(self, grid, width, height, start_x, start_y, player_x, player_y, exit_x, exit_y): #ловушки
        if self.level == 1:
            trap_count = 3
        elif self.level == 2:
            trap_count = 6
        else:
            trap_count = 10

        empty_cells = []
        for y in range(height):
            for x in range(width):
                if grid[y][x] == 0:
                    if (not (x == player_x and y == player_y) and
                            not (x == exit_x and y == exit_y) and
                            not (abs(x - player_x) <= 1 and abs(y - player_y) <= 1) and
                            not (abs(x - exit_x) <= 1 and abs(y - exit_y) <= 1)):
                        empty_cells.append((x, y))

        if len(empty_cells) < trap_count:
            trap_count = len(empty_cells)

        random.shuffle(empty_cells)
        trap_positions = empty_cells[:trap_count]

        for x, y in trap_positions:
            center_x = start_x + x * TILE_SIZE + TILE_SIZE // 2
            center_y = start_y + y * TILE_SIZE + TILE_SIZE // 2
            trap = Trap(center_x, center_y)
            trap.rotation = 0
            self.scene.add_sprite("Traps", trap)

    def create_exit(self, x, y, start_x, start_y): #создает выход
        self.exit = arcade.Sprite()
        self.exit.color = arcade.color.GREEN
        self.exit.width = TILE_SIZE * 0.9
        self.exit.height = TILE_SIZE * 0.9

        self.exit.center_x = start_x + x * TILE_SIZE + TILE_SIZE // 2
        self.exit.center_y = start_y + y * TILE_SIZE + TILE_SIZE // 2
        self.scene.add_sprite("Exit", self.exit)

    def on_key_press(self, key, modifiers): #нажатия клавиш (R - рестарт, ESC - меню)
        if key in self.keys:
            self.keys[key] = True

        if key == arcade.key.R:
            self.setup()
        elif key == arcade.key.ESCAPE:
            self.stop_background_music()
            from main import MenuView
            menu_view = MenuView()
            self.window.show_view(menu_view)

    def on_key_release(self, key, modifiers): #отпускает клавиши движения
        if key in self.keys:
            self.keys[key] = False

    def on_update(self, delta_time):
        if not self.player:
            return

        if self.level_completed:
            self.completion_countdown = max(0, self.completion_countdown - delta_time)
            return

        self.player.update(delta_time)

        for coin in self.scene["Coins"]:
            if hasattr(coin, 'update'):
                coin.update(delta_time)

        for ghost in self.scene["Ghosts"]:
            ghost.update(delta_time)

        for emitter in self.fog_emitters:
            emitter.update(delta_time)

        #обновляет таймер уровня
        if self.level_start_time and self.timer_running:
            self.current_time = time.time() - self.level_start_time
            self.time_text.text = f"Время: {self.current_time:.1f} сек"

        self.player.update_movement(self.keys)

        if self.physics_engine:
            self.physics_engine.update()
        else:
            if len(self.scene["Walls"]) > 0:
                self.physics_engine = arcade.PhysicsEngineSimple(
                    self.player, self.scene["Walls"]
                )

        #ограничивает движение границами
        if self.player.left < self.boundary_left:
            self.player.left = self.boundary_left
        if self.player.right > self.boundary_right:
            self.player.right = self.boundary_right
        if self.player.bottom < self.boundary_bottom:
            self.player.bottom = self.boundary_bottom
        if self.player.top > self.boundary_top:
            self.player.top = self.boundary_top

        #проверяет столкновения
        traps_hit = arcade.check_for_collision_with_list(self.player, self.scene["Traps"])
        for trap in traps_hit:
            if not self.player.trapped:
                self.player.apply_trap()

        ghosts_hit = arcade.check_for_collision_with_list(self.player, self.scene["Ghosts"])
        if ghosts_hit:
            #возвращение игрока при касании призрака
            self.player.return_to_start()
            self.player.color = arcade.color.LIGHT_BLUE
            arcade.schedule(self.reset_player_color, 0.5)

        #звук при собирании монет
        coins_hit = arcade.check_for_collision_with_list(self.player, self.scene["Coins"])
        for coin in coins_hit:
            coin.remove_from_sprite_lists()
            self.player.coins_collected += 1

            if self.coin_sound:
                arcade.play_sound(self.coin_sound, volume=2)

            self.coins_text.text = f"Монеты: {self.player.coins_collected}/{self.player.coins_needed}"

        #проверка победы
        if self.player.coins_collected >= self.player.coins_needed:
            if arcade.check_for_collision(self.player, self.exit):
                self.complete_level()

    def reset_player_color(self, delta_time): #возвращение нормального цвета игрока
        arcade.unschedule(self.reset_player_color)
        self.player.color = arcade.color.WHITE

    def complete_level(self): #завершает уровень
        if not self.level_completed:
            self.level_completed = True
            self.timer_running = False
            self.level_completion_time = self.current_time

            if self.level == 3:
                self.completion_countdown = 5.0
            else:
                self.completion_countdown = 3.0

            self.time_text.text = f"Время: {self.level_completion_time:.1f} сек"

            #сохраняет результат уровня в сессию
            if self.data_manager:
                self.data_manager.add_level_result(
                    level=self.level,
                    time_taken=self.level_completion_time,
                    coins=self.player.coins_collected
                )

            if self.level == 3: #сохраняет сессию и показывает экран тк послед уровень
                self.session_final_time = self.level_completion_time
                self.session_final_coins = self.player.coins_collected

                if self.data_manager:
                    self.data_manager.complete_session()

                self.show_final_completion_screen()
            else:
                self.show_completion_screen()

    def show_final_completion_screen(self): #таймер возврата
        arcade.schedule(self.return_to_menu, 5.0)

    def show_completion_screen(self): #таймер перехода
        arcade.schedule(self.go_to_next_screen, 3.0)

    def go_to_next_screen(self, delta_time): #переход на некст левел
        arcade.unschedule(self.go_to_next_screen)

        if self.level < self.max_levels:
            next_level_view = GameView(level_num=self.level + 1, data_manager=self.data_manager)
            self.window.show_view(next_level_view)

    def return_to_menu(self, delta_time): #возвращет в главное меню после финала
        arcade.unschedule(self.return_to_menu)
        self.stop_background_music()
        from main import MenuView
        menu_view = MenuView()
        self.window.show_view(menu_view)

    def on_draw(self): #отрисовывание всего экрана
        self.clear()

        #фон экрана
        rect = arcade.rect.XYWH(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        arcade.draw_rect_filled(rect, arcade.color.BLACK)

        #пол
        rect = arcade.rect.XYWH(
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
            self.maze_size * TILE_SIZE, self.maze_size * TILE_SIZE
        )
        arcade.draw_rect_filled(rect, FLOOR_COLOR)

        #слои
        if not self.level_completed:
            self.scene.get_sprite_list("Walls").draw()
            self.scene.get_sprite_list("Exit").draw()

            #делаем туман поверх объектов
            for emitter in self.fog_emitters:
                emitter.draw()

            self.scene.get_sprite_list("Coins").draw()
            self.scene.get_sprite_list("Traps").draw()
            self.scene.get_sprite_list("Ghosts").draw()
            self.scene.get_sprite_list("Player").draw()

        #панель статистики в левом верхнем углу
        panel_width = 280
        panel_height = 180 if self.session_text else 150
        panel_x = 15
        panel_y = SCREEN_HEIGHT - 100

        rect = arcade.rect.XYWH(panel_x, panel_y - panel_height, panel_width, panel_height)
        arcade.draw_rect_filled(rect, (0, 0, 0, 180))

        if self.ghost_warning_text:
            self.ghost_warning_text.x = panel_x + 10
            self.ghost_warning_text.y = panel_y - 30
            self.ghost_warning_text.draw()

        if self.level_text:
            self.level_text.x = panel_x + 5
            self.level_text.y = panel_y - 110
            self.level_text.draw()

        if self.coins_text:
            self.coins_text.x = panel_x + 5
            self.coins_text.y = panel_y - 140
            self.coins_text.draw()

        if self.time_text:
            self.time_text.x = panel_x + 5
            self.time_text.y = panel_y - 170
            self.time_text.draw()

        #подсказка по управлению
        arcade.draw_text(
            "Управление: WASD/Стрелки | R: Рестарт | ESC: Меню",
            SCREEN_WIDTH - 20, 15,
            arcade.color.LIGHT_GRAY, 12,
            anchor_x="right"
        )

        #прогресс-линия сбора монет
        if self.player.coins_needed > 0:
            remaining = max(0, self.player.coins_needed - self.player.coins_collected)
            progress_width = 150
            progress_height = 12
            progress_x = 100
            progress_y = 30

            arcade.draw_rect_filled(
                arcade.rect.XYWH(progress_x, progress_y, progress_width, progress_height),
                (50, 50, 50)
            )

            fill_percent = min(1.0, self.player.coins_collected / self.player.coins_needed)
            if fill_percent > 0:
                arcade.draw_rect_filled(
                    arcade.rect.XYWH(progress_x, progress_y, progress_width * fill_percent, progress_height),
                    arcade.color.GOLD
                )

            txt_label = f"Еще {remaining} монет" if remaining > 0 else "Вход открыт!"
            arcade.draw_text(
                txt_label, 25, progress_y + 15,
                arcade.color.WHITE, 13, anchor_x="left", bold=True
            )

        #экраны завершения уровня
        if self.level_completed:
            rect = arcade.rect.XYWH(
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                SCREEN_WIDTH, SCREEN_HEIGHT
            )
            arcade.draw_rect_filled(rect, (0, 0, 0, 220))

            if self.level == 3: #финальный экран победы
                arcade.draw_text(
                    "ВСЕ УРОВНИ ПРОЙДЕНЫ!",
                    SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150,
                    arcade.color.DARK_RED, 50, anchor_x="center", anchor_y="center", bold=True
                )

                arcade.draw_text(
                    "ПОЗДРАВЛЯЕМ!",
                    SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80,
                    arcade.color.RED, 40, anchor_x="center", anchor_y="center"
                )

                arcade.draw_text(
                    f"Финальное время: {self.level_completion_time:.2f} секунд",
                    SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10,
                    arcade.color.GREEN, 35, anchor_x="center", anchor_y="center"
                )

                arcade.draw_text(
                    f"Монет собрано: {self.player.coins_collected}",
                    SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50,
                    arcade.color.GREY, 35, anchor_x="center", anchor_y="center"
                )

                arcade.draw_text(
                    f"Итог всей сессии: {self.level_completion_time:.2f} сек, {self.session_final_coins} монет",
                    SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 110,
                    arcade.color.GREY, 30, anchor_x="center", anchor_y="center"
                )

                arcade.draw_text(
                    f"Возврат в меню через {int(self.completion_countdown + 1)} сек...",
                    SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 180,
                    arcade.color.LIGHT_GRAY, 24, anchor_x="center", anchor_y="center"
                )
            else: #экран завершения обычного уровня
                arcade.draw_text(
                    f"УРОВЕНЬ {self.level} ПРОЙДЕН!",
                    SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100,
                    arcade.color.RED, 40, anchor_x="center", anchor_y="center", bold=True
                )

                arcade.draw_text(
                    f"Время уровня: {self.level_completion_time:.2f} секунд",
                    SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30,
                    arcade.color.GREEN, 30, anchor_x="center", anchor_y="center"
                )

                arcade.draw_text(
                    f"Монет собрано: {self.player.coins_collected}",
                    SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30,
                    arcade.color.RED, 30, anchor_x="center", anchor_y="center"
                )

                if self.level < self.max_levels:
                    arcade.draw_text(
                        f"Следующий уровень через {int(self.completion_countdown + 1)} сек...",
                        SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100,
                        arcade.color.LIGHT_GRAY, 22, anchor_x="center", anchor_y="center"
                    )
