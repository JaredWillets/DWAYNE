import requests
from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QPainter, QColor
from bs4 import BeautifulSoup
import random

def get_contributions(username):
    url = f"https://github.com/users/{username}/contributions"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    # Look for SVG with contributions (located in the profile page, not /contributions path)
    rects = soup.select('svg.js-calendar-graph-svg rect[data-date][data-count]')

    tiles = soup.find_all("td", {"class":"ContributionCalendar-day"})

    contributions = {}

    grid = [[0 for i in range(7)] for __ in range(53)]

    for tile in tiles:
        x = int(tile['id'].split("-")[-1])
        y = int(tile['id'].split("-")[-2])
        level = int(tile['data-level'])
        contributions[tile['data-date']] = {
            "x":x,
            "y":y,
            "level":level
        }
        grid[x][y] = level

    return contributions, grid

class GitHubWidget(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_NoSystemBackground, True)

        self.setAttribute(Qt.WA_TranslucentBackground)

        self.username = "JaredWillets"

        self.cell_size = 20  # Width/Height of each square
        self.spacing = 3      # Spacing between squares
        self.columns = 53     # 53 weeks
        self.rows = 7         # 7 days
        self.margin = 3
        self.data = get_contributions(self.username)[1]

        self.setMinimumSize(
            self.columns * (self.cell_size + self.spacing) + self.margin * 2,
            self.rows * (self.cell_size + self.spacing) + self.margin * 2
        )

        self.block_width = self.columns * (self.cell_size + self.spacing) + self.margin * 2
        self.block_height = self.rows * (self.cell_size + self.spacing) + self.margin * 2

        self.update()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(300000)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setPen(QColor("#fff"))
        painter.setBrush(QColor("#fff"))
        painter.setOpacity(0.3)

        painter.drawRoundedRect(QRectF(0, 0, self.block_width, self.block_height), 10, 10)

        painter.setOpacity(1.0)

        for col in range(self.columns):
            for row in range(self.rows):
                level = self.data[col][row]
                color = self.get_color(level)

                x = self.margin + col * (self.cell_size + self.spacing)
                y = self.margin + row * (self.cell_size + self.spacing)

                painter.setBrush(color)
                painter.setPen(QColor('#d0d7de'))
                painter.drawRect(x, y, self.cell_size, self.cell_size)


    def get_color(self, level):
        # RGBA values with transparency
        color = QColor(0,255,0,int(255*level/4))
        return color

    def update(self):
        self.data = get_contributions(self.username)[1]



if __name__ == "__main__":
    # Example
    username = 'JaredWillets'  # Replace with any GitHub username
    contribs, grid = get_contributions(username)
    for y in range(len(grid)):
        for x in range(len(grid[y])):
            print(grid[y][x], end = "", flush = True)
        print()
    
