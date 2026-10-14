import pygame

from flappy_bird import FlappyBird


def main():
    boardWidth = 360
    boardHeight = 640

    pygame.init()
    screen = pygame.display.set_mode((boardWidth, boardHeight))
    pygame.display.set_caption("Flappy Bird")

    flappyBird = FlappyBird(screen)
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                flappyBird.handleEvent(event)

        flappyBird.update()
        flappyBird.draw()
        pygame.display.flip()
        clock.tick(60)  # 60 FPS game loop

    pygame.quit()


if __name__ == "__main__":
    main()
