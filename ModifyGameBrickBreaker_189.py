import tkinter as tk


class GameObject:
    def __init__(self, canvas, x, y, width, height, color):
        self.canvas = canvas
        self.item = canvas.create_rectangle(x - width / 2, y - height / 2,
                                            x + width / 2, y + height / 2,
                                            fill=color)

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


class Ball(GameObject):
    def __init__(self, canvas, x, y):
        super().__init__(canvas, x, y, 10, 10, 'white')
        self.velocity = [5, -5]

    def update(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if coords[0] <= 0 or coords[2] >= width:
            self.velocity[0] *= -1
        if coords[1] <= 0:
            self.velocity[1] *= -1

        self.move(self.velocity[0], self.velocity[1])

    def collide(self, objects):
        coords = self.get_position()
        if len(objects) > 0:
            self.velocity[1] *= -1
            for obj in objects:
                if isinstance(obj, Brick):
                    obj.hit()


class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        super().__init__(canvas, x, y, 100, 10, 'orange')
        self.ball = None

    def move(self, offset):
        coords = self.get_position()
        if coords[0] + offset >= 0 and coords[2] + offset <= self.canvas.winfo_width():
            super().move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)

    def set_ball(self, ball):
        self.ball = ball


class Brick(GameObject):
    COLORS = {1: '#ff99cc', 2: '#66ff66', 3: '#3399ff'}

    def __init__(self, canvas, x, y, hits):
        super().__init__(canvas, x, y, 75, 20, Brick.COLORS[hits])
        self.hits = hits
        self.canvas.addtag_withtag('brick', self.item)

    def hit(self):
        self.hits -= 1
        if self.hits <= 0:
            self.delete()
        else:
            self.canvas.itemconfig(self.item, fill=Brick.COLORS[self.hits])


class HomeScreen(tk.Frame):
    def __init__(self, master, start_game_callback, highscore):
        super().__init__(master)
        self.master = master
        self.start_game_callback = start_game_callback
        self.highscore = highscore
        self.configure(bg='#D6D1F5')

        self.pack(fill='both', expand=True)

        title = tk.Label(self, text="Brick Breaker", font=('Forte', 32), bg='#D6D1F5')
        title.pack(pady=50)

        play_button = tk.Button(self, text="Play", font=('Arial', 16),
                                command=self.start_game_callback, width=10)
        play_button.pack(pady=20)

        self.highscore_label = tk.Label(self, text=f"Highscore: {self.highscore}", font=('Arial', 14), bg='#D6D1F5')
        self.highscore_label.pack(pady=10)

    def update_highscore(self, new_highscore):
        self.highscore = new_highscore
        self.highscore_label.config(text=f"Highscore: {self.highscore}")


class Game(tk.Frame):
    def __init__(self, master, on_game_over_callback, highscore):
        super().__init__(master)
        self.master = master
        self.on_game_over_callback = on_game_over_callback
        self.highscore = highscore
        self.lives = 3
        self.score = 0
        self.width = 610
        self.height = 400
        self.paused = False

        self.canvas = tk.Canvas(self, bg='#D6D1F5', width=self.width, height=self.height)
        self.canvas.pack(fill='both', expand=True)

        self.pack()

        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width / 2, 326)
        self.items[self.paddle.item] = self.paddle

        for x in range(5, self.width - 5, 75):
            self.add_brick(x + 37.5, 50, 3)
            self.add_brick(x + 37.5, 70, 2)
            self.add_brick(x + 37.5, 90, 1)

        self.hud = None
        self.score_text = None
        self.highscore_text = None
        self.setup_game()

        self.canvas.focus_set()
        self.canvas.bind('<Left>', lambda _: self.paddle.move(-10))
        self.canvas.bind('<Right>', lambda _: self.paddle.move(10))
        self.canvas.bind('<p>', self.toggle_pause)

    def setup_game(self):
        self.add_ball()
        self.update_lives_text()
        self.update_score_text()
        self.text = self.draw_text(300, 200, 'Press Space to start')
        self.canvas.bind('<space>', lambda _: self.start_game())

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas, x, 310)
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size='40'):
        font = ('Forte', size)
        return self.canvas.create_text(x, y, text=text, font=font)

    def update_lives_text(self):
        text = f'Lives: {self.lives}'
        if self.hud is None:
            self.hud = self.draw_text(50, 20, text, 15)
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def update_score_text(self):
        if self.score_text is None:
            self.score_text = self.draw_text(300, 20, f'Score: {self.score}', 15)
        else:
            self.canvas.itemconfig(self.score_text, text=f'Score: {self.score}')
        if self.highscore_text is None:
            self.highscore_text = self.draw_text(550, 20, f'Highscore: {self.highscore}', 15)
        else:
            self.canvas.itemconfig(self.highscore_text, text=f'Highscore: {self.highscore}')

    def start_game(self):
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text)
        self.paddle.set_ball(None)
        self.paused = False
        self.game_loop()

    def toggle_pause(self, event=None):
        self.paused = not self.paused
        if not self.paused:
            self.game_loop()

    def game_loop(self):
        if not self.paused:
            self.check_collisions()
            num_bricks = len(self.canvas.find_withtag('brick'))
            if num_bricks == 0:
                self.end_game(True)
            elif self.ball.get_position()[3] >= self.height:
                self.lives -= 1
                if self.lives < 0:
                    self.end_game(False)
                else:
                    self.setup_game()
            else:
                self.ball.update()
                self.after(17, self.game_loop)

    def end_game(self, win):
        self.paused = True
        if win:
            self.highscore = max(self.score, self.highscore)
            self.update_score_text()
            self.draw_text(300, 200, 'You Win! Congrats!')
        else:
            self.draw_text(300, 200, 'Game Over!')
        self.after(2000, self.on_game_over_callback)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        self.ball.collide(objects)

        for obj in objects:
            if isinstance(obj, Brick):
                self.score += 10
                self.update_score_text()


def start_game():
    global game
    home_screen.pack_forget()
    game = Game(root, game_over, highscore)
    game.pack()


def game_over():
    global highscore, game
    highscore = max(highscore, game.score)
    game.pack_forget()
    home_screen.update_highscore(highscore)
    home_screen.pack()


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Brick Breaker')
    highscore = 0

    home_screen = HomeScreen(root, start_game, highscore)
    home_screen.pack()

    root.mainloop()