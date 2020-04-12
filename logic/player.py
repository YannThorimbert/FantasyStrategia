from FantasyStrategia.logic.unit import COLORS

class Player:
    def __init__(self, team, name, race):
        self.team = team
        self.name = name
        self.race = race
        self.color = race.color
        self.color_rgb = COLORS[self.color][0]
        self.money = 0
        self.tax = 1.
