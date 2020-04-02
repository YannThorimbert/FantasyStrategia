from FantasyStrategia.logic.unit import COLORS

class Player:
    def __init__(self, team, name, color):
        self.team = team
        self.name = name
        self.color = color
        self.color_rgb = COLORS[color][0]
        self.money = 0
