"""
VOID SALVAGER - Open World Space Exploration Game
Run: python main.py
Requires: pip install pygame
"""

import pygame
import sys
from game import Game

def main():
    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("VOID SALVAGER")
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()

    game = Game(screen)

    while True:
        dt = clock.tick(60) / 1000.0
        dt = min(dt, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # ESC exits fullscreen / quits when not in skill tree
                from game import GameState
                if game.state == GameState.SKILL_TREE:
                    game.state = GameState.PLAYING
                else:
                    pygame.quit()
                    sys.exit()
            game.handle_event(event)

        game.update(dt)
        game.draw()
        pygame.display.flip()

if __name__ == "__main__":
    main()
