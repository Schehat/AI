import pygame
import neat
import os
import random

pygame.init()
pygame.font.init()

font_score = pygame.font.SysFont("timesnewroman", 40)
BLACK = (0, 0, 0)

os.environ['SDL_VIDEO_CENTERED'] = '1'
pygame.display.set_caption("Flappy Bird AI")

WINDOW_SIZE = (600, 600)
WINDOW = pygame.display.set_mode(WINDOW_SIZE)

CLOCK = pygame.time.Clock()
FPS = 30

BIRD_IMGS = [pygame.image.load(os.path.join("imgs", "bird1.png")),
             pygame.image.load(os.path.join("imgs", "bird2.png")),
             pygame.image.load(os.path.join("imgs", "bird3.png"))]
PIPE_IMG = pygame.image.load(os.path.join("imgs", "pipe.png"))
BG_IMG = pygame.image.load(os.path.join("imgs", "bg.png"))
BASE_IMG = pygame.image.load(os.path.join("imgs", "base.png"))

gen = 0
DRAW_LINES = True


class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0  # degrees of rotation
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1

        d = self.vel * self.tick_count + 1.5 * self.tick_count ** 2

        if d >= 10:
            d = 10

        if d < 0:
            d -= 2

        self.y = self.y + d

        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self):
        self.img_count += 1

        # animation
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2

        # to tilt around the center - idk why it works...
        rotated_img = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_img.get_rect(center=self.img.get_rect(topleft=(int(self.x), int(self.y))).center)

        WINDOW.blit(rotated_img, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


class Pipe:
    GAP = 130
    VEL = 10

    def __init__(self, x):
        self.x = x
        self.height = 0

        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)  # x and y bool?
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 300)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self):
        WINDOW.blit(self.PIPE_TOP, (self.x, self.top))
        WINDOW.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        # returns bool weather pixels are intersecting
        t_point = bird_mask.overlap(top_mask, top_offset)
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)

        if t_point or b_point:
            return True

        return False


class Base:
    VEL = 10
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self):
        WINDOW.blit(self.IMG, (self.x1, self.y))
        WINDOW.blit(self.IMG, (self.x2, self.y))


def draw_window(birds, pipes, base, score, gen, pipe_ind):
    WINDOW.blit(BG_IMG, (0, 0))
    for pipe in pipes:
        pipe.draw()
    base.draw()
    text_score = font_score.render(f"Score: {score}", 1, BLACK)
    WINDOW.blit(text_score, (10, 10))

    text_gen = font_score.render(f"Gen: {gen}", 1, BLACK)
    WINDOW.blit(text_gen, (10, 50))

    text_alive = font_score.render(f"Alive: {len(birds)}", 1, BLACK)
    WINDOW.blit(text_alive, (10, 90))

    for bird in birds:
        # draw lines from bird to pipe
        if DRAW_LINES:
            try:
                pygame.draw.line(WINDOW, (255, 0, 0),
                                 (int(bird.x + bird.img.get_width() / 2), int(bird.y + bird.img.get_height() / 2)),
                                 (int(pipes[pipe_ind].x + pipes[pipe_ind].PIPE_TOP.get_width() / 2),
                                  pipes[pipe_ind].height), 1)
                pygame.draw.line(WINDOW, (255, 0, 0),
                                 (int(bird.x + bird.img.get_width() / 2), int(bird.y + bird.img.get_height() / 2)),
                                 (int(pipes[pipe_ind].x + pipes[pipe_ind].PIPE_BOTTOM.get_width() / 2),
                                  pipes[pipe_ind].bottom), 1)
            except TypeError and IndexError:
                pass

        bird.draw()

    pygame.display.update()


def eval_genomes(genomes, config):
    """
    running the simulation of the current generation and evaluating
    their fitness level by how war far the distance is they travel
    """

    # counting generations
    global gen
    gen += 1

    # start by creating lists holding the genome itself, the
    # neural network associated with the genome and the
    # bird object that uses that network to play
    ge = []
    nets = []
    birds = []

    #  setting up neural networks
    for genome_id, genome in genomes:
        genome.fitness = 0  # start with fitness level of 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        ge.append(genome)
        nets.append(net)
        birds.append(Bird(170, 100))

    pipes = [Pipe(WINDOW_SIZE[0])]
    base = Base(WINDOW_SIZE[0] - BASE_IMG.get_height())
    score = 0

    run = True

    while run:
        CLOCK.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        # necessary with multiple pipes which pipe to put as an input
        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            run = False

        # give each bird every frame a little fitness for staying alive
        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.2

            # giving input to determine neural network to decide weather to jump or not
            output = nets[x].activate(
                (bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            #  usage of tanh activation function so result will be between -1 and 1. if over 0.5 jump
            if output[0] > 0.5:  # 0 due to only one output
                bird.jump()

        add_pipe = False
        rem = []
        for pipe in pipes:
            pipe.move()
            # check collision
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[x].fitness -= 5  # punish for colliding
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            # pipes out of the screen get added to this list and removed
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

        for r in rem:
            pipes.remove(r)

        if add_pipe:
            # genome gets rewarded for passing through a pipe
            for g in ge:
                g.fitness += 5
            score += 1
            pipes.append(Pipe(WINDOW_SIZE[0]))

        for x, bird in enumerate(birds):
            if abs(bird.y - pipes[0].height) < 200 or abs(bird.y - pipes[0].bottom) < 150:
                ge[x].fitness += 0.1
            else:
                ge[x].fitness -= 1
            if bird.y < pipes[0].bottom and bird.y + bird.img.get_height() > pipes[0].top:
                pass
            else:
                ge[x].fitness += 0.01

        # pop birds touching the bottom & top
        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() > WINDOW_SIZE[1] - BASE_IMG.get_height() or bird.y < 0:
                ge[x].fitness -= 5
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        base.move()
        draw_window(birds, pipes, base, score, gen, pipe_ind)


def run(config_path):
    """
    runs the NEAT algorithm to train the neural network
    :param config_path: location of config file
    :return: None
    """
    # load the config
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                                neat.DefaultStagnation, config_path)

    # setting population
    p = neat.Population(config)

    # Add a stdout reporter to show progress in the terminal
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # 1. simulation & 2. amount of generations here limitless
    # simulation will end after amount of generations are reached or the fitness threshold
    winner = p.run(eval_genomes)

    # show final stats
    print('\nBest genome:\n{!s}'.format(winner))


if __name__ == "__main__":
    # Determine path to configuration file. This path manipulation is
    # here so that the script will run successfully regardless of the
    # current working directory
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)
