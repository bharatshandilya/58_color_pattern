import random
import array
import pygame
from game.color_button import ColorButton


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        pad_size = 130
        gap = 24
        start_x = width // 2 - pad_size - (gap // 2)
        start_y = 150

        self.buttons = [
            ColorButton(0, pygame.Rect(start_x, start_y, pad_size, pad_size), (110, 20, 20), (255, 50, 50)),
            ColorButton(1, pygame.Rect(start_x + pad_size + gap, start_y, pad_size, pad_size), (15, 60, 150), (40, 170, 255)),
            ColorButton(2, pygame.Rect(start_x, start_y + pad_size + gap, pad_size, pad_size), (15, 100, 30), (50, 255, 90)),
            ColorButton(3, pygame.Rect(start_x + pad_size + gap, start_y + pad_size + gap, pad_size, pad_size), (140, 110, 10), (255, 235, 40)),
        ]

        self.sequence = []
        self.player_input = []
        self.score = 0

        self.state = "WATCH"
        self.showing_step = 0
        self.step_start_time = 0
        self.flash_duration = 450
        self.pause_duration = 200
        self.is_flashing = False

        self.player_lit_button = None
        self.player_lit_start = 0
        self.player_flash_duration = 150

        self.font_title = pygame.font.SysFont(None, 40)
        self.font_medium = pygame.font.SysFont(None, 28)

        # TASK 4: Initialize timer variables
        self.turn_time_limit = 0
        self.turn_start_time = 0

        # TASK 3: Initialize Pygame mixer and generated tones BEFORE starting the round
        pygame.mixer.init(44100, -16, 2, 512)
        self.tones = {
            0: self.create_tone(261), # Red
            1: self.create_tone(329), # Blue
            2: self.create_tone(392), # Green
            3: self.create_tone(523)  # Yellow
        }

        self.start_next_round()

    def start_next_round(self):
        new_color = random.randint(0, 3)
        
        # TASK 1: Append single color
        self.sequence.append(new_color)
        
        # TASK 2: Dynamic acceleration based on score
        self.flash_duration = max(180, 450 - (self.score * 25))
        self.pause_duration = max(80, 200 - (self.score * 10))
        
        self.player_input.clear()
        self.state = "WATCH"
        self.showing_step = 0
        self.step_start_time = pygame.time.get_ticks()
        self.is_flashing = True
        self.buttons[self.sequence[0]].is_lit = True
        
        # TASK 3: Play sound for the very first step of the round
        self.tones[self.sequence[0]].play(maxtime=int(self.flash_duration))

    def update(self):
        now = pygame.time.get_ticks()

        # Handle the delay for resetting the player's button flash
        if self.player_lit_button is not None:
            if now - self.player_lit_start >= self.player_flash_duration:
                self.player_lit_button.is_lit = False
                self.player_lit_button = None

        if self.state == "WATCH":
            current_btn_id = self.sequence[self.showing_step]

            if self.is_flashing:
                # Turn off the light when the flash duration expires
                if now - self.step_start_time >= self.flash_duration:
                    self.buttons[current_btn_id].is_lit = False
                    self.is_flashing = False
                    self.step_start_time = now
            else:
                # Move to the next button when the pause duration expires
                if now - self.step_start_time >= self.pause_duration:
                    self.showing_step += 1
                    if self.showing_step < len(self.sequence):
                        next_id = self.sequence[self.showing_step]
                        self.buttons[next_id].is_lit = True
                        self.is_flashing = True
                        self.step_start_time = now
                        
                        # TASK 3: Play sound for the next step in the sequence
                        self.tones[next_id].play(maxtime=int(self.flash_duration))
                    else:
                        self.state = "PLAYER_TURN"
                        
                        # TASK 4: Initialize the countdown timer for the player's turn
                        self.turn_time_limit = 3000 + (len(self.sequence) * 1000)
                        self.turn_start_time = now

        # TASK 4: Check if the countdown timer expired
        if self.state == "PLAYER_TURN":
            if now - self.turn_start_time >= self.turn_time_limit:
                self.state = "GAME_OVER"

    def handle_event(self, event):
        if self.state == "GAME_OVER":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset()
            return

        if self.state == "PLAYER_TURN" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self.buttons:
                if btn.contains(event.pos):
                    btn.is_lit = True
                    self.player_lit_button = btn
                    self.player_lit_start = pygame.time.get_ticks()

                    self.register_player_click(btn.color_id)
                    break

    def register_player_click(self, color_id):
        self.player_input.append(color_id)
        current_idx = len(self.player_input) - 1

        if self.player_input[current_idx] != self.sequence[current_idx]:
            self.state = "GAME_OVER"
            return

        if len(self.player_input) == len(self.sequence):
            self.score += 1
            self.start_next_round()

    def reset(self):
        self.sequence.clear()
        self.player_input.clear()
        self.score = 0
        for btn in self.buttons:
            btn.is_lit = False
        self.player_lit_button = None
        self.start_next_round()

    def render(self, screen):
        screen.fill((22, 24, 30))

        # Render Header text
        title_surf = self.font_title.render("Memory Pattern Arena", True, (245, 245, 245))
        screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 20))

        score_surf = self.font_medium.render(f"Score: {self.score}", True, (255, 220, 80))
        screen.blit(score_surf, (self.width // 2 - score_surf.get_width() // 2, 60))

        status_text = "Watch the pattern..." if self.state == "WATCH" else "Your turn: Click the pattern!"
        status_color = (190, 195, 205) if self.state == "WATCH" else (80, 240, 130)
        status_surf = self.font_medium.render(status_text, True, status_color)
        screen.blit(status_surf, (self.width // 2 - status_surf.get_width() // 2, 95))

        # TASK 4: Render the dynamic countdown timer bar
        if self.state == "PLAYER_TURN":
            elapsed = pygame.time.get_ticks() - self.turn_start_time
            remaining = max(0, self.turn_time_limit - elapsed)
            ratio = remaining / self.turn_time_limit if self.turn_time_limit > 0 else 0
            
            bar_width = 300
            bar_height = 12
            bar_x = self.width // 2 - bar_width // 2
            bar_y = 125
            
            # Draw background track
            pygame.draw.rect(screen, (50, 55, 65), (bar_x, bar_y, bar_width, bar_height), border_radius=6)
            
            # Draw dynamic fill color (shifts from green to red)
            r = min(255, int(255 * (1 - ratio) * 2))
            g = min(255, int(255 * ratio * 2))
            
            if ratio > 0:
                pygame.draw.rect(screen, (r, g, 50), (bar_x, bar_y, int(bar_width * ratio), bar_height), border_radius=6)

        # Render all buttons
        for btn in self.buttons:
            btn.render(screen)

        # Render Game Over overlay
        if self.state == "GAME_OVER":
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))

            over_surf = self.font_title.render("GAME OVER", True, (240, 70, 70))
            screen.blit(over_surf, (self.width // 2 - over_surf.get_width() // 2, self.height // 2 - 40))

            final_score_surf = self.font_medium.render(f"Final Score: {self.score}", True, (255, 255, 255))
            screen.blit(final_score_surf, (self.width // 2 - final_score_surf.get_width() // 2, self.height // 2 + 10))

            restart_surf = self.font_medium.render("Press [R] to Play Again", True, (200, 200, 200))
            screen.blit(restart_surf, (self.width // 2 - restart_surf.get_width() // 2, self.height // 2 + 50))

    def create_tone(self, frequency, duration=1.0):
        """Synthesizes a simple square wave buffer for a given frequency."""
        sample_rate = 44100
        amplitude = 8000
        period = int(sample_rate / frequency)
        frames = int(sample_rate * duration)
        
        buffer = array.array('h') # Signed 16-bit integer array
        for i in range(frames):
            val = amplitude if (i % period) < (period // 2) else -amplitude
            buffer.append(val)
            buffer.append(val)
            
        return pygame.mixer.Sound(buffer=buffer)