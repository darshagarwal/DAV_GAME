import pygame
import random
import math
import sys
from pathlib import Path

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60

# Colors
BLUE = (30, 144, 255)
DARK_BLUE = (0, 100, 200)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BROWN = (139, 69, 19)
GRAY = (128, 128, 128)
LIGHT_BLUE = (173, 216, 230)

# Sound paths
SOUND_CORRECT = Path("assets/correct.wav")
SOUND_WRONG = Path("assets/wrong.wav")
SOUND_COLLECT = Path("assets/collect.wav")

# Player Class
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 60
        self.height = 40
        self.speed = 5
        self.collected_trash = []

    def move(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x = max(0, self.x - self.speed)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x = min(SCREEN_WIDTH - self.width, self.x + self.speed)
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y = max(0, self.y - self.speed)
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y = min(SCREEN_HEIGHT - self.height, self.y + self.speed)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen):
        pygame.draw.ellipse(screen, BROWN, (self.x, self.y + 20, self.width, 20))
        pygame.draw.rect(screen, WHITE, (self.x + 10, self.y, self.width - 20, 25))
        pygame.draw.rect(screen, BROWN, (self.x + self.width // 2 - 2, self.y - 15, 4, 20))

# Trash Class (minimal placeholder)
class Trash:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = random.uniform(1, 2)
        self.sink_timer = 600
        self.type = random.choice(['plastic', 'glass', 'organic'])
        self.name = f"{self.type.title()} Item"
        self.width = 32
        self.height = 32

        # Map type to multiple image choices
        type_variants = {
            'plastic': ['plastic.png', 'plastic1.png', 'plastic2.png', 'plastic3.png', 'plastic4.png'],
            'organic': ['organic.png', 'organic1.png', 'organic2.png', 'organic3.png'],
            'glass': ['glass.png','glass1.png', 'glass2.png', 'glass3.png']
        }

        image_file = random.choice(type_variants[self.type])
        self.image = pygame.image.load(f"assets/trash/{image_file}").convert_alpha()
        self.image = pygame.transform.scale(self.image, (self.width, self.height))

    def update(self):
        self.y += self.speed
        self.sink_timer -= 1

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))

# Obstacle Class
class Obstacle:
    def __init__(self, x, y, obstacle_type):
        self.x = x
        self.y = y
        self.type = obstacle_type
        self.speed = random.uniform(1, 3)
        self.width = 40
        self.height = 30

    def update(self):
        self.y += self.speed

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen):
        pygame.draw.ellipse(screen, GRAY, (self.x, self.y, self.width, self.height))

# Recycling Bin Class
class RecyclingBin:
    def __init__(self, x, y, bin_type):
        self.x = x
        self.y = y
        self.width = 80
        self.height = 60
        self.type = bin_type
        self.colors = {'plastic': RED, 'glass': GREEN, 'organic': BROWN}

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen):
        color = self.colors[self.type]
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, BLACK, (self.x, self.y, self.width, self.height), 3)
        font = pygame.font.Font(None, 24)
        text = font.render(self.type.upper(), True, WHITE)
        text_rect = text.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
        screen.blit(text, text_rect)


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Ocean Cleanup Game")
        self.clock = pygame.time.Clock()

        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)
        self.trash_list = []
        self.obstacles = []
        self.score = 0
        self.game_time = 120 * FPS
        self.trash_spawn_timer = 0
        self.obstacle_spawn_timer = 0
        self.game_state = "playing"
        self.sorting_trash = None

        self.feedback_message = ""
        self.feedback_color = WHITE
        self.feedback_timer = 0

        self.bins = [
            RecyclingBin(50, SCREEN_HEIGHT - 100, 'plastic'),
            RecyclingBin(150, SCREEN_HEIGHT - 100, 'glass'),
            RecyclingBin(250, SCREEN_HEIGHT - 100, 'organic')
        ]

        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        self.lives = 3
        self.combo_count = 0
        self.last_sorted_type = None
        self.level = 1
        self.level_timer = 0

        pygame.mixer.init()
        self.correct_sound = pygame.mixer.Sound(str(SOUND_CORRECT)) if SOUND_CORRECT.exists() else None
        self.wrong_sound = pygame.mixer.Sound(str(SOUND_WRONG)) if SOUND_WRONG.exists() else None
        self.collect_sound = pygame.mixer.Sound(str(SOUND_COLLECT)) if SOUND_COLLECT.exists() else None

    def draw_ocean_background(self):
        for y in range(0, SCREEN_HEIGHT, 20):
            wave_offset = int(10 * math.sin((y + pygame.time.get_ticks() * 0.01) * 0.1))
            color_intensity = int(200 + 30 * math.sin(y * 0.02))
            water_color = (30, 144, min(255, color_intensity))
            pygame.draw.rect(self.screen, water_color, (wave_offset, y, SCREEN_WIDTH, 20))

    def spawn_trash(self):
        if self.trash_spawn_timer <= 0:
            x = random.randint(0, SCREEN_WIDTH - 20)
            y = random.randint(-50, -20)
            self.trash_list.append(Trash(x, y))
            self.trash_spawn_timer = max(30, 120 - self.level * 10)
        else:
            self.trash_spawn_timer -= 1

    def spawn_obstacles(self):
        if self.obstacle_spawn_timer <= 0:
            x = random.randint(0, SCREEN_WIDTH - 60)
            y = random.randint(-50, -20)
            obstacle_type = random.choice(['rock', 'shark', 'wave'])
            self.obstacles.append(Obstacle(x, y, obstacle_type))
            self.obstacle_spawn_timer = max(60, 180 - self.level * 10)
        else:
            self.obstacle_spawn_timer -= 1

    def check_collisions(self):
        player_rect = self.player.get_rect()
        for trash in self.trash_list[:]:
            if player_rect.colliderect(trash.get_rect()):
                self.player.collected_trash.append(trash)
                self.trash_list.remove(trash)
                self.score += 10
                if self.collect_sound:
                    self.collect_sound.play()

        for obstacle in self.obstacles[:]:
            if player_rect.colliderect(obstacle.get_rect()):
                self.obstacles.remove(obstacle)
                self.lives -= 1
                self.score = max(0, self.score - 5)
                if self.lives <= 0:
                    self.game_state = "game_over"

    def update_entities(self):
        for trash in self.trash_list[:]:
            trash.update()
            if trash.y > SCREEN_HEIGHT or trash.sink_timer <= 0:
                self.trash_list.remove(trash)

        for obstacle in self.obstacles[:]:
            obstacle.update()
            if obstacle.y > SCREEN_HEIGHT:
                self.obstacles.remove(obstacle)

    def handle_sorting(self, keys):
        if self.player.collected_trash and not self.sorting_trash:
            self.sorting_trash = self.player.collected_trash[0]
            self.game_state = "sorting"

        if self.game_state == "sorting" and self.sorting_trash:
            mouse_pos = pygame.mouse.get_pos()
            mouse_clicked = pygame.mouse.get_pressed()[0]

            if mouse_clicked:
                for bin in self.bins:
                    if bin.get_rect().collidepoint(mouse_pos):
                        if bin.type == self.sorting_trash.type:
                            self.score += 5
                            self.feedback_message = "Correct! +5 points"
                            self.feedback_color = GREEN
                            if self.last_sorted_type == bin.type:
                                self.combo_count += 1
                                if self.combo_count >= 3:
                                    self.score += 5
                            else:
                                self.combo_count = 1
                                self.last_sorted_type = bin.type
                            if self.correct_sound:
                                self.correct_sound.play()
                        else:
                            self.score = max(0, self.score - 3)
                            self.feedback_message = f"Wrong! {self.sorting_trash.name} goes in {self.sorting_trash.type.upper()} bin. -3 points"
                            self.feedback_color = RED
                            self.combo_count = 0
                            if self.wrong_sound:
                                self.wrong_sound.play()
                        self.feedback_timer = 120
                        self.player.collected_trash.remove(self.sorting_trash)
                        self.sorting_trash = None
                        self.game_state = "playing"
                        break

    def draw_ui(self):
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        time_left = max(0, self.game_time // FPS)
        time_text = self.font.render(f"Time: {time_left}s", True, WHITE)
        trash_text = self.small_font.render(f"Collected: {len(self.player.collected_trash)}", True, WHITE)
        lives_text = self.small_font.render(f"Lives: {self.lives}", True, RED)
        level_text = self.small_font.render(f"Level: {self.level}", True, YELLOW)

        self.screen.blit(score_text, (10, 10))
        self.screen.blit(time_text, (10, 50))
        self.screen.blit(trash_text, (10, 90))
        self.screen.blit(lives_text, (10, 120))
        self.screen.blit(level_text, (10, 150))

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        game_over_text = self.font.render("GAME OVER!", True, WHITE)
        final_score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
        restart_text = self.small_font.render("Press R to restart or Q to quit", True, WHITE)

        message = "Keep practicing - our oceans need your help!"
        if self.score >= 100:
            message = "Excellent work cleaning the ocean!"
        elif self.score >= 50:
            message = "Good job! Every piece of trash counts!"

        edu_text = self.small_font.render(message, True, WHITE)
        fact_text = self.small_font.render("Fact: 8 million tons of plastic enter our oceans yearly!", True, LIGHT_BLUE)

        texts = [game_over_text, final_score_text, edu_text, fact_text, restart_text]
        y_start = SCREEN_HEIGHT // 2 - len(texts) * 15

        for i, text in enumerate(texts):
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y_start + i * 40))
            self.screen.blit(text, text_rect)

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if self.game_state == "game_over":
                        if event.key == pygame.K_r:
                            self.__init__()
                        elif event.key == pygame.K_q:
                            running = False

            if self.game_state != "game_over":
                keys = pygame.key.get_pressed()
                if self.game_state == "playing":
                    self.player.move(keys)
                    self.spawn_trash()
                    self.spawn_obstacles()
                    self.check_collisions()
                    self.update_entities()
                    self.game_time -= 1
                    self.level_timer += 1
                    if self.level_timer > 30 * FPS:
                        self.level += 1
                        self.level_timer = 0
                    if self.game_time <= 0:
                        self.game_state = "game_over"

                self.handle_sorting(keys)

            self.draw_ocean_background()

            if self.game_state != "game_over":
                for bin in self.bins:
                    bin.draw(self.screen)
                self.player.draw(self.screen)
                for trash in self.trash_list:
                    trash.draw(self.screen)
                for obstacle in self.obstacles:
                    obstacle.draw(self.screen)
                self.draw_ui()
            else:
                self.draw_game_over()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()