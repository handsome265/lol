from manim import *

class SquareAnimation(Scene):
    def construct(self):
        square = Square()
        self.play(Create(square))
        self.wait(1)