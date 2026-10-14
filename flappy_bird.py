import os
import random
import pygame

try:
    from PIL import Image, ImageSequence
except ImportError:
    Image = None


# Game er asset file er path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# Image er path ber kore
def asset(name):
    return os.path.join(BASE_DIR, name)


# Image load kore size thik kore
def load_image(name, size):
    img = pygame.image.load(asset(name)).convert_alpha()
    return pygame.transform.scale(img, size)


# Bird er GIF animation load kore
def load_gif(name, size):
    frames = []
    if Image is not None:
        with Image.open(asset(name)) as gif:
            for frame in ImageSequence.Iterator(gif):
                duration = frame.info.get("duration", 100) or 100
                rgba = frame.convert("RGBA")
                make = getattr(pygame.image, "frombytes", None) or pygame.image.fromstring
                surf = make(rgba.tobytes(), rgba.size, "RGBA").convert_alpha()
                frames.append((pygame.transform.scale(surf, size), duration))
    else:
        frames.append((load_image(name, size), 100))
    return frames


# Bird er position ar size
class Bird:
    def __init__(self, game, img):
        self.x = game.birdX
        self.y = game.birdY
        self.width = game.birdWidth
        self.height = game.birdHeight
        self.img = img


# Pipe er position ar size
class Pipe:
    def __init__(self, game, img):
        self.x = game.pipeX
        self.y = game.pipeY
        self.width = game.pipeWidth
        self.height = game.pipeHeight
        self.img = img
        self.passed = False


# Main game
class FlappyBird:
    def __init__(self, screen):
        self.screen = screen

        # Game board er size
        self.boardWidth = 360
        self.boardHeight = 640

        # Bird er size ar starting position
        self.birdX = self.boardWidth // 8
        self.birdY = self.boardWidth // 2
        self.birdWidth = 34
        self.birdHeight = 24

        # Pipe er size ar starting position
        self.pipeX = self.boardWidth
        self.pipeY = 0
        self.pipeWidth = 64
        self.pipeHeight = 512

        # Game er image load
        self.backgroundImg = load_image("flappybirdbg.png", (self.boardWidth, self.boardHeight))
        self.birdImg = load_gif("flappyBird.gif", (self.birdWidth, self.birdHeight))
        self.topPipeImg = load_image("toppipe.png", (self.pipeWidth, self.pipeHeight))
        self.bottomPipeImg = load_image("bottompipe.png", (self.pipeWidth, self.pipeHeight))

        # Game er movement ar score
        self.bird = Bird(self, self.birdImg)
        self.velocityX = -3
        self.velocityY = 0
        self.gravity = 0.4

        self.pipes = []
        self.gameOver = False
        self.score = 0.0

        # Score ar instruction er font
        self.scoreFont = pygame.font.SysFont("arial", 32)
        self.uiFont = pygame.font.SysFont("arial", 16, bold=True)

        # Play Again button
        self.playAgainRect = pygame.Rect((self.boardWidth - 150) // 2,
                                         (self.boardHeight - 50) // 2, 150, 50)
        self.playAgainVisible = False

        # Click instruction er position
        self.instructionRect = pygame.Rect(0, self.boardHeight - 40, self.boardWidth, 30)
        self.instructionVisible = True

        # Game er timer
        now = pygame.time.get_ticks()
        self.animStart = now
        self.blinkNext = now + 500
        self.placePipeNext = now + 1500
        self.gameLoopRunning = True

    # Random position e pipe create kore
    def placePipes(self):
        randomPipeY = int(self.pipeY - self.pipeHeight // 4 - random.random() * (self.pipeHeight // 2))
        openingSpace = self.boardHeight // 4

        topPipe = Pipe(self, self.topPipeImg)
        topPipe.y = randomPipeY
        self.pipes.append(topPipe)

        bottomPipe = Pipe(self, self.bottomPipeImg)
        bottomPipe.y = topPipe.y + self.pipeHeight + openingSpace
        self.pipes.append(bottomPipe)

    # Game screen e sob kichu draw kore
    def draw(self):
        now = pygame.time.get_ticks()

        self.screen.blit(self.backgroundImg, (0, 0))

        # Bird animation draw kore
        self.screen.blit(self._birdFrame(now), (self.bird.x, self.bird.y))

        # Pipe draw kore
        for pipe in self.pipes:
            self.screen.blit(pipe.img, (pipe.x, pipe.y))

        # Score show kore
        if self.gameOver:
            text = "Game Over: " + str(int(self.score))
        else:
            text = str(int(self.score))
        surf = self.scoreFont.render(text, True, (255, 255, 255))
        self.screen.blit(surf, (10, 35 - self.scoreFont.get_ascent()))

        # Click instruction show kore
        if self.instructionVisible:
            label = self.uiFont.render("Click to Jump", True, (255, 255, 255))
            self.screen.blit(label, label.get_rect(center=self.instructionRect.center))

        # Game over hole button show kore
        if self.playAgainVisible:
            self._drawButton()

    # GIF er current frame select kore
    def _birdFrame(self, now):
        frames = self.bird.img
        total = sum(d for _, d in frames)
        t = (now - self.animStart) % total if total > 0 else 0
        for surf, duration in frames:
            if t < duration:
                return surf
            t -= duration
        return frames[-1][0]

    # Play Again button draw kore
    def _drawButton(self):
        pressed = pygame.mouse.get_pressed()[0] and self.playAgainRect.collidepoint(pygame.mouse.get_pos())
        fill = (184, 207, 229) if pressed else (238, 238, 238)
        pygame.draw.rect(self.screen, fill, self.playAgainRect)
        pygame.draw.rect(self.screen, (122, 138, 153), self.playAgainRect, 1)
        label = self.uiFont.render("Play Again", True, (0, 0, 0))
        self.screen.blit(label, label.get_rect(center=self.playAgainRect.center))

    # Bird ar pipe er movement update kore
    def move(self):
        self.velocityY += self.gravity
        self.velocityY = min(self.velocityY, 6)
        self.bird.y += self.velocityY
        self.bird.y = max(self.bird.y, 0)

        # Pipe move kore ar score update kore
        for pipe in self.pipes:
            pipe.x += self.velocityX

            if not pipe.passed and self.bird.x > pipe.x + pipe.width:
                self.score += 0.5
                pipe.passed = True

            # Bird pipe e lagle game over
            if self.collision(self.bird, pipe):
                self.gameOver = True

        # Bird ground e porle game over
        if self.bird.y > self.boardHeight:
            self.gameOver = True

    # Bird ar pipe er collision check kore
    def collision(self, a, b):
        return (a.x < b.x + b.width and
                a.x + a.width > b.x and
                a.y < b.y + b.height and
                a.y + a.height > b.y)

    # Timer ar game update kore
    def update(self):
        now = pygame.time.get_ticks()

        # Instruction blink koray
        if self.blinkNext is not None and now >= self.blinkNext:
            self.instructionVisible = not self.instructionVisible
            self.blinkNext += 500

        # Nirdisto somoy por pipe create kore
        if self.placePipeNext is not None and now >= self.placePipeNext:
            self.placePipes()
            self.placePipeNext += 1500

        if not self.gameLoopRunning:
            return

        self.move()

        # Game over hole timer bondho kore
        if self.gameOver:
            self.placePipeNext = None
            self.gameLoopRunning = False
            self.blinkNext = None
            self.playAgainVisible = True
            self.instructionVisible = False

    # Mouse click ar keyboard input handle kore
    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Play Again button e click korle restart
            if self.playAgainVisible and self.playAgainRect.collidepoint(event.pos):
                self.resetGame()
            elif not self.gameOver:
                # Click korle bird jump kore
                self.velocityY = -7

        # Game over hole SPACE diye restart
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            if self.gameOver:
                self.resetGame()

    # Game abar starting obosthay niye jay
    def resetGame(self):
        self.bird.y = self.birdY
        self.velocityY = 0
        self.pipes.clear()
        self.gameOver = False
        self.score = 0.0
        self.playAgainVisible = False
        self.instructionVisible = True
        now = pygame.time.get_ticks()
        self.blinkNext = now + 500
        self.gameLoopRunning = True
        self.placePipeNext = now + 1500
