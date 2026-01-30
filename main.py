import arcade
import time
from game import GameView
from data_manager import DataManager

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
SCREEN_TITLE = "Сокровища Чёрного храма"


class MenuView(arcade.View): #главное окно
    def __init__(self):
        super().__init__()
        self.data_manager = DataManager()
        self.sound_player = None

        self.logo_list = arcade.SpriteList()
        try:
            self.logo_sprite = arcade.Sprite("assets/sprites/nazaglavku.jpg")
            target_height = 360
            self.logo_sprite.scale = target_height / self.logo_sprite.height
            self.logo_sprite.center_x = SCREEN_WIDTH / 2
            self.logo_sprite.center_y = SCREEN_HEIGHT / 2 - 47
            self.logo_list.append(self.logo_sprite)
        except Exception:
            pass

    def on_show_view(self):
        self.window.background_color = arcade.color.BLACK

        try:
            self.sound = arcade.load_sound("assets/sounds/scary_sound.wav")
            self.sound_player = self.sound.play(volume=0.3, loop=True)
        except Exception:
            pass

    def on_hide_view(self):
        if self.sound_player:
            try:
                self.sound_player.pause()
            except AttributeError:
                pass

    def on_draw(self):
        self.clear()

        arcade.draw_text("Сокровища", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 200,
                         (250, 137, 137), font_size=30, anchor_x="center")
        arcade.draw_text("Чёрного храма", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 150,
                         arcade.color.DARK_RED, font_size=50, anchor_x="center", bold=True)

        if self.logo_list:
            self.logo_list.draw()

        best_sessions = self.data_manager.get_best_full_sessions(3)

        arcade.draw_text("Нажмите ENTER для старта", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 250,
                         arcade.color.WHITE, font_size=20, anchor_x="center")

        arcade.draw_text("S - Полная статистика   |   ESC - Выход", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 280,
                         arcade.color.GRAY, font_size=18, anchor_x="center")

    def on_key_press(self, key, modifiers): #нажатия клавиш в главном меню
        if key == arcade.key.ENTER:
            if self.sound_player:
                try:
                    self.sound_player.pause()
                except:
                    pass
            self.data_manager.start_session()
            game_view = GameView(level_num=1, data_manager=self.data_manager)
            self.window.show_view(game_view)
        elif key == arcade.key.S:
            if self.sound_player:
                try:
                    self.sound_player.pause()
                except:
                    pass
            stats_view = StatisticsView(self.data_manager)
            self.window.show_view(stats_view)
        elif key == arcade.key.ESCAPE:
            self.window.close()


class StatisticsView(arcade.View):
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.show_full_sessions = True

    def on_show_view(self):
        self.window.background_color = arcade.color.BLACK

    def on_draw(self):
        self.clear()

        arcade.draw_text("ПОЛНАЯ СТАТИСТИКА", SCREEN_WIDTH / 2, SCREEN_HEIGHT - 50,
                         arcade.color.RED, font_size=40, anchor_x="center", bold=True)

        if self.show_full_sessions:
            self.draw_full_sessions()
        else:
            self.draw_level_stats()

        arcade.draw_text("F - Полные сессии | L - По уровням | ESC - Меню",
                         SCREEN_WIDTH / 2, 40,
                         arcade.color.GRAY, font_size=18, anchor_x="center")

    def draw_full_sessions(self): #отображение таблиц
        arcade.draw_text("Полные прохождения всех 3 уровней:",
                         SCREEN_WIDTH / 2, SCREEN_HEIGHT - 100,
                         arcade.color.WHITE, font_size=24, anchor_x="center")

        full_sessions = self.data_manager.get_full_sessions(10)

        if full_sessions:
            arcade.draw_text("Дата", 50, SCREEN_HEIGHT - 140, arcade.color.RED, font_size=18)
            arcade.draw_text("Время", 250, SCREEN_HEIGHT - 140, arcade.color.RED, font_size=18)
            arcade.draw_text("Монеты", 400, SCREEN_HEIGHT - 140, arcade.color.RED, font_size=18)
            arcade.draw_text("Уровни", 500, SCREEN_HEIGHT - 140, arcade.color.RED, font_size=18)

            y_offset = 170
            for session_date, total_time, total_coins, levels_data in full_sessions:
                date_str = session_date.split()[0]
                time_str = session_date.split()[1][:5]

                arcade.draw_text(f"{date_str} {time_str}", 50, SCREEN_HEIGHT - y_offset,
                                 arcade.color.WHITE, font_size=16)
                arcade.draw_text(f"{total_time:.1f} сек", 250, SCREEN_HEIGHT - y_offset,
                                 arcade.color.GREEN, font_size=16)
                arcade.draw_text(f"{total_coins}", 400, SCREEN_HEIGHT - y_offset,
                                 arcade.color.WHITE, font_size=16)

                levels_info = levels_data.split(';')
                level_display = ""
                for level_info in levels_info:
                    parts = level_info.split(':')
                    if len(parts) >= 3:
                        level_num = parts[0][1:]
                        level_time = float(parts[1][:-1])
                        level_coins = parts[2][:-1]
                        level_display += f"У{level_num}:{level_time:.0f}s "

                arcade.draw_text(level_display[:30], 500, SCREEN_HEIGHT - y_offset,
                                 arcade.color.LIGHT_BLUE, font_size=14)

                y_offset += 35
                if y_offset > SCREEN_HEIGHT - 50:
                    break
        else:
            arcade.draw_text("Нет данных о полных прохождениях",
                             SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                             arcade.color.GRAY, font_size=24, anchor_x="center")
            arcade.draw_text("Пройдите все 3 уровня подряд для сохранения результата!",
                             SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50,
                             arcade.color.LIGHT_GRAY, font_size=18, anchor_x="center")

    def draw_level_stats(self): #таблицы лучших результатов по каждому уровнб
        arcade.draw_text("Статистика по отдельным уровням:",
                         SCREEN_WIDTH / 2, SCREEN_HEIGHT - 100,
                         arcade.color.WHITE, font_size=24, anchor_x="center")

        stats = self.data_manager.get_level_stats()

        if stats:
            arcade.draw_text("Уровень", 100, SCREEN_HEIGHT - 140, arcade.color.RED, font_size=18)
            arcade.draw_text("Лучшее время", 250, SCREEN_HEIGHT - 140, arcade.color.RED, font_size=18)
            arcade.draw_text("Монет", 450, SCREEN_HEIGHT - 140, arcade.color.RED, font_size=18)
            arcade.draw_text("Попыток", 550, SCREEN_HEIGHT - 140, arcade.color.RED, font_size=18)

            y_offset = 170
            for level, best_time, max_coins, attempts in stats:
                arcade.draw_text(f"{level}", 100, SCREEN_HEIGHT - y_offset,
                                 arcade.color.WHITE, font_size=18)
                arcade.draw_text(f"{best_time:.2f} сек", 250, SCREEN_HEIGHT - y_offset,
                                 arcade.color.GREEN, font_size=18)
                arcade.draw_text(f"{max_coins}", 450, SCREEN_HEIGHT - y_offset,
                                 arcade.color.WHITE, font_size=18)
                arcade.draw_text(f"{attempts}", 550, SCREEN_HEIGHT - y_offset,
                                 arcade.color.WHITE, font_size=18)
                y_offset += 40

    def on_key_press(self, key, modifiers): #переключение, возвращение в меню
        if key == arcade.key.ESCAPE:
            menu_view = MenuView()
            self.window.show_view(menu_view)
        elif key == arcade.key.F:
            self.show_full_sessions = True
        elif key == arcade.key.L:
            self.show_full_sessions = False


def main(): #запускает главное окно игры и меню
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    menu_view = MenuView()
    window.show_view(menu_view)
    arcade.run()


if __name__ == "__main__":
    main()
