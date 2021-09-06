import pygame
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLU import *

class Cube:
    def __init__(self, x, y, z, r, color=[1, 1, 1], projection=False):
        self.color = color
        self.projection = projection

        a, b, c = x, z, y
        x, y, z = a, b, c
        self.verticies = [
            [x - r, y - r, z - r],
            [x + r, y - r, z - r],
            [x + r, y + r, z - r],
            [x - r, y + r, z - r],
            [x - r, y + r, z + r],
            [x + r, y + r, z + r],
            [x + r, y - r, z + r],
            [x - r, y - r, z + r],
        ]
        self.edges = [
            [0, 1],
            [0, 3],
            [0, 7],
            [2, 1],
            [2, 3],
            [2, 5],
            [4, 3],
            [4, 5],
            [4, 7],
            [6, 5],
            [6, 7],
            [6, 1],
        ]
    def render(self):
        glBegin(GL_LINES)
        glColor3f(*self.color)
        for edge in self.edges:
            for vertex in edge:
                glVertex3fv(self.verticies[vertex])
        glEnd()
        if self.projection:
            glBegin(GL_POLYGON)
            for edge in self.edges:
                for vertex in edge:
                    glVertex3fv([self.verticies[vertex][0], 0, self.verticies[vertex][2]])
            glEnd()


class Polygon2D:
    def __init__(self, verticies, in_format=False, color=[1, 0, 1], fill=False):
        self.color, self.fill = color, fill

        if in_format: self.verticies = verticies
        else:
            self.verticies = []
            for i in range(0, len(verticies), 2): self.verticies.append([verticies[i], verticies[i + 1]])

    def render(self):
        glBegin(GL_LINE_LOOP if not self.fill else GL_POLYGON)

        glColor3f(*self.color)
        for i in self.verticies:
            glVertex3fv([i[0], 0, i[1]])

        glEnd()

class Line:
    def __init__(self, x1, y1, z1, x2, y2, z2, color=[1, 1, 1]):
        self.color = color
        self.line = [[x1, z1, y1], [x2, z2, y2]]

    def render(self):
        glBegin(GL_LINES)

        glColor3f(*self.color)
        for l in self.line: glVertex3fv(l)

        glEnd()

def on_key(key, f):
    global on_keys
    on_keys[key] = f

pygame.init()
display = (1000, 1000)
pygame.display.set_mode(display, DOUBLEBUF|OPENGL)

gluPerspective(80, display[0] / display[1], 0.1, 500.0)

glTranslatef(-50, -85, -200)

keys = []
on_keys = {}

floor = Polygon2D([-200, -200, 200, -200, 200, 200, -200, 200], color=[0.3, 0.3, 0.3], fill=True)

def render(objects):
    global x, y, z
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()

        if event.type == 771:
            if not event.text in keys:
                keys.append(event.text)

        if event.type == 769:
            while event.unicode in keys:
                keys.remove(event.unicode)

    if 'd' in keys: glTranslatef(-0.5, 0, 0)
    if 'a' in keys: glTranslatef(0.5, 0, 0)
    if 'q' in keys: glTranslatef(0, -0.5, 0)
    if 'e' in keys: glTranslatef(0, 0.5, 0)
    if 's' in keys: glTranslatef(0, 0, -0.5)
    if 'w' in keys: glTranslatef(0, 0, 0.5)

    if 'j' in keys: glRotatef(1, 0, 1, 0)
    if 'l' in keys: glRotatef(-1, 0, 1, 0)

    for i in keys:
        if i in on_keys.keys():
            on_keys[i]()

    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

    floor.render()

    for i in objects:
        i.render()

    pygame.display.flip()
    pygame.time.wait(10)
