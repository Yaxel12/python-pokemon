import pygame
from pygame.locals import *
import time
import math
import random
import requests
import io
from urllib.request import urlopen

pygame.init()


# crear la ventana del juego
game_width = 500
game_height = 500
size = (game_width, game_height)
game = pygame.display.set_mode(size)
pygame.display.set_caption('Pokemon Battle')

# definir colores
black = (0, 0, 0)
gold = (218, 165, 32)
grey = (200, 200, 200)
green = (0, 200, 0)
red = (200, 0, 0)
white = (255, 255, 255)

# URL base de la API
base_url = 'https://pokeapi.co/api/v2'

class Move():
    
    def __init__(self, url):
        
        # call the moves API endpoint
        req = requests.get(url)
        self.json = req.json()
        
        self.name = self.json['name']
        self.power = self.json['power']
        self.type = self.json['type']['name']

class Pokemon(pygame.sprite.Sprite):
    
    def __init__(self, name, level, x, y):
        
        pygame.sprite.Sprite.__init__(self)
        
        
        # llamar al punto final de la API de Pokémon
        req = requests.get(f'{base_url}/pokemon/{name.lower()}')
        self.json = req.json()
        
        # establecer el nombre y el nivel del pokemon
        self.name = name
        self.level = level
        
        
       # establecer la posición del sprite en la pantalla
        self.x = x
        self.y = y
        
        # número de posiciones restantes
        self.num_potions = 3
        
        # obtener las estadísticas de Pokémon de la API
        stats = self.json['stats']
        for stat in stats:
            if stat['stat']['name'] == 'hp':
                self.current_hp = stat['base_stat'] + self.level
                self.max_hp = stat['base_stat'] + self.level
            elif stat['stat']['name'] == 'attack':
                self.attack = stat['base_stat']
            elif stat['stat']['name'] == 'defense':
                self.defense = stat['base_stat']
            elif stat['stat']['name'] == 'speed':
                self.speed = stat['base_stat']
                
        # establecer los tipos de pokemon
        self.types = []
        for i in range(len(self.json['types'])):
            type = self.json['types'][i]
            self.types.append(type['type']['name'])
            
        # establecer el ancho del sprite
        self.size = 150
        
        # establece el sprite en el sprite frontal
        self.set_sprite('front_default')
    
    def perform_attack(self, other, move):
        
        display_message(f'{self.name} used {move.name}')
        
        # pausa durante 2 segundos
        time.sleep(2)
        
        # calcular el daño
        damage = (2 * self.level + 10) / 250 * self.attack / other.defense * move.power
        
        # bonificación de ataque del mismo tipo (STAB)
        if move.type in self.types:
            damage *= 1.5
            
        # golpe crítico (6,25% de probabilidad)
        random_num = random.randint(1, 10000)
        if random_num <= 625:
            damage *= 1.5
            
        # redondear el daño
        damage = math.floor(damage)
        
        other.take_damage(damage)
        
    def take_damage(self, damage):
        
        self.current_hp -= damage
        
        # hp no debe bajar de 0
        if self.current_hp < 0:
            self.current_hp = 0
    
    def use_potion(self):
        
        # comprobar si quedan pociones
        if self.num_potions > 0:
            
            # añadir 30 CV (pero no sobrepasar el CV máximo)
            self.current_hp += 30
            if self.current_hp > self.max_hp:
                self.current_hp = self.max_hp
                
            # disminuir el número de pociones restantes
            self.num_potions -= 1
        
    def set_sprite(self, side):
        
        # establecer el sprite del pokemon
        image = self.json['sprites'][side]
        image_stream = urlopen(image).read()
        image_file = io.BytesIO(image_stream)
        self.image = pygame.image.load(image_file).convert_alpha()
        
        # escalar la imagen
        scale = self.size / self.image.get_width()
        new_width = self.image.get_width() * scale
        new_height = self.image.get_height() * scale
        self.image = pygame.transform.scale(self.image, (new_width, new_height))
        
    def set_moves(self):
        
        self.moves = []
        
        # realizar todos los movimientos desde la API
        for i in range(len(self.json['moves'])):
            
            # obtener el movimiento de diferentes versiones del juego
            versions = self.json['moves'][i]['version_group_details']
            for j in range(len(versions)):
                
                version = versions[j]
                
                # solo obtenemos movimientos de la versión rojo-azul
                if version['version_group']['name'] != 'red-blue':
                    continue
                    
               # solo obtienes movimientos que se pueden aprender al subir de nivel (es decir, excluye movimientos TM)
                learn_method = version['move_learn_method']['name']
                if learn_method != 'level-up':
                    continue
                    
                # agrega movimiento si el nivel de Pokémon es lo suficientemente alto
                level_learned = version['level_learned_at']
                if self.level >= level_learned:
                    move = Move(self.json['moves'][i]['move']['url'])
                    
                    # solo incluye movimientos de ataque
                    if move.power is not None:
                        self.moves.append(move)
                        
        # selecciona hasta 4 movimientos aleatorios
        if len(self.moves) > 4:
            self.moves = random.sample(self.moves, 4)
        
    def draw(self, alpha=255):
        
        sprite = self.image.copy()
        transparency = (255, 255, 255, alpha)
        sprite.fill(transparency, None, pygame.BLEND_RGBA_MULT)
        game.blit(sprite, (self.x, self.y))
        
    def draw_hp(self):
        
        # mostrar la barra de salud
        bar_scale = 200 // self.max_hp
        for i in range(self.max_hp):
            bar = (self.hp_x + bar_scale * i, self.hp_y, bar_scale, 20)
            pygame.draw.rect(game, red, bar)
            
        for i in range(self.current_hp):
            bar = (self.hp_x + bar_scale * i, self.hp_y, bar_scale, 20)
            pygame.draw.rect(game, green, bar)
            
        # mostrar el texto "HP"
        font = pygame.font.Font(pygame.font.get_default_font(), 16)
        text = font.render(f'HP: {self.current_hp} / {self.max_hp}', True, black)
        text_rect = text.get_rect()
        text_rect.x = self.hp_x
        text_rect.y = self.hp_y + 30
        game.blit(text, text_rect)
        
    def get_rect(self):
        
        return Rect(self.x, self.y, self.image.get_width(), self.image.get_height())

def display_message(message):
    
    # dibuja un cuadro blanco con borde negro
    pygame.draw.rect(game, white, (10, 350, 480, 140))
    pygame.draw.rect(game, black, (10, 350, 480, 140), 3)
    
    # mostrar el mensaje
    font = pygame.font.Font(pygame.font.get_default_font(), 20)
    text = font.render(message, True, black)
    text_rect = text.get_rect()
    text_rect.x = 30
    text_rect.y = 410
    game.blit(text, text_rect)
    
    pygame.display.update()
    
def create_button(width, height, left, top, text_cx, text_cy, label):
    
    # posición del cursor del mouse
    mouse_cursor = pygame.mouse.get_pos()
    
    button = Rect(left, top, width, height)
    
    # resaltar el botón si el mouse está apuntando hacia él
    if button.collidepoint(mouse_cursor):
        pygame.draw.rect(game, gold, button)
    else:
        pygame.draw.rect(game, white, button)
        
    # agregar la etiqueta al botón
    font = pygame.font.Font(pygame.font.get_default_font(), 16)
    text = font.render(f'{label}', True, black)
    text_rect = text.get_rect(center=(text_cx, text_cy))
    game.blit(text, text_rect)
    
    return button
        
# crear los pokemon iniciales
level = 30
bulbasaur = Pokemon('Bulbasaur', level, 25, 150)
charmander = Pokemon('Charmander', level, 175, 150)
squirtle = Pokemon('Squirtle', level, 325, 150)
pokemons = [bulbasaur, charmander, squirtle]

# Pokémon seleccionados por el jugador y el rival.
player_pokemon = None
rival_pokemon = None

# bucle de juego
game_status = 'select pokemon'
while game_status != 'quit':
    
    for event in pygame.event.get():
        if event.type == QUIT:
            game_status = 'quit'
            
       # detectar pulsación de tecla
        if event.type == KEYDOWN:
            
            # juega de nuevo
            if event.key == K_y:
                # reset the pokemons
                bulbasaur = Pokemon('Bulbasaur', level, 25, 150)
                charmander = Pokemon('Charmander', level, 175, 150)
                squirtle = Pokemon('Squirtle', level, 325, 150)
                pokemons = [bulbasaur, charmander, squirtle]
                game_status = 'select pokemon'
                
            # abandonar
            elif event.key == K_n:
                game_status = 'quit'
            
        # detectar clic del mouse
        if event.type == MOUSEBUTTONDOWN:
            
            # coordenadas del clic del mouse
            mouse_click = event.pos
            
            # para seleccionar un pokemon
            if game_status == 'select pokemon':
                
                # comprobar en qué Pokémon se hizo clic
                for i in range(len(pokemons)):
                    
                    if pokemons[i].get_rect().collidepoint(mouse_click):
                        
                        # asignar los pokemon del jugador y del rival
                        player_pokemon = pokemons[i]
                        rival_pokemon = pokemons[(i + 1) % len(pokemons)]
                        
                        # Baja el nivel del Pokémon rival para facilitar la batalla.
                        rival_pokemon.level = int(rival_pokemon.level * .75)
                        
                        # establece las coordenadas de las barras de hp
                        player_pokemon.hp_x = 275
                        player_pokemon.hp_y = 250
                        rival_pokemon.hp_x = 50
                        rival_pokemon.hp_y = 50
                        
                        game_status = 'prebattle'
            
            # para seleccionar pelear o usar poción
            elif game_status == 'player turn':
                
                # comprobar si se hizo clic en el botón de pelea
                if fight_button.collidepoint(mouse_click):
                    game_status = 'player move'
                    
                # comprobar si se hizo clic en el botón de poción
                if potion_button.collidepoint(mouse_click):
                    
                    # fuerza para atacar si no hay más pociones
                    if player_pokemon.num_potions == 0:
                        display_message('No more potions left')
                        time.sleep(2)
                        game_status = 'player move'
                    else:
                        player_pokemon.use_potion()
                        display_message(f'{player_pokemon.name} used potion')
                        time.sleep(2)
                        game_status = 'rival turn'
                        
            # para seleccionar un movimiento
            elif game_status == 'player move':
                
                # comprobar en qué botón de movimiento se hizo clic
                for i in range(len(move_buttons)):
                    button = move_buttons[i]
                    
                    if button.collidepoint(mouse_click):
                        move = player_pokemon.moves[i]
                        player_pokemon.perform_attack(rival_pokemon, move)
                        
                        # comprobar si el pokemon del rival se desmayó
                        if rival_pokemon.current_hp == 0:
                            game_status = 'fainted'
                        else:
                            game_status = 'rival turn'
            
    # pantalla de selección de pokemon
    if game_status == 'select pokemon':
        
        game.fill(white)
        
        # dibujar los pokemon iniciales
        bulbasaur.draw()
        charmander.draw()
        squirtle.draw()
        
        # Dibujar un cuadro alrededor del Pokémon al que apunta el mouse.
        mouse_cursor = pygame.mouse.get_pos()
        for pokemon in pokemons:
            
            if pokemon.get_rect().collidepoint(mouse_cursor):
                pygame.draw.rect(game, black, pokemon.get_rect(), 2)
        
        pygame.display.update()
        
    # obtener movimientos de la API y reposicionar los pokemons
    if game_status == 'prebattle':
        
        #dibuja el pokemon seleccionado
        game.fill(white)
        player_pokemon.draw()
        pygame.display.update()
        
        player_pokemon.set_moves()
        rival_pokemon.set_moves()
        
        # reposicionar los pokemons
        player_pokemon.x = -50
        player_pokemon.y = 100
        rival_pokemon.x = 250
        rival_pokemon.y = -50
        
        # cambiar el tamaño de los sprites
        player_pokemon.size = 300
        rival_pokemon.size = 300
        player_pokemon.set_sprite('back_default')
        rival_pokemon.set_sprite('front_default')
        
        game_status = 'start battle'
        
    # iniciar animación de batalla
    if game_status == 'start battle':
        
        # rival envía su pokemon
        alpha = 0
        while alpha < 255:
            
            game.fill(white)
            rival_pokemon.draw(alpha)
            display_message(f'Rival sent out {rival_pokemon.name}!')
            alpha += .4
            
            pygame.display.update()
            
        # pausa durante 1 segundo
        time.sleep(1)
        
        # jugador envía su pokemon
        alpha = 0
        while alpha < 255:
            
            game.fill(white)
            rival_pokemon.draw()
            player_pokemon.draw(alpha)
            display_message(f'Go {player_pokemon.name}!')
            alpha += .4
            
            pygame.display.update()
        
        # dibuja las barras de hp
        player_pokemon.draw_hp()
        rival_pokemon.draw_hp()
        
        # determinar quién va primero
        if rival_pokemon.speed > player_pokemon.speed:
            game_status = 'rival turn'
        else:
            game_status = 'player turn'
            
        pygame.display.update()
        
        # pausa durante 1 segundo
        time.sleep(1)
        
    # muestra la pelea y usa botones de pociones
    if game_status == 'player turn':
        
        game.fill(white)
        player_pokemon.draw()
        rival_pokemon.draw()
        player_pokemon.draw_hp()
        rival_pokemon.draw_hp()
        
        # crea la pelea y usa botones de poción
        fight_button = create_button(240, 140, 10, 350, 130, 412, 'Fight')
        potion_button = create_button(240, 140, 250, 350, 370, 412, f'Use Potion ({player_pokemon.num_potions})')

        # dibuja el borde negro
        pygame.draw.rect(game, black, (10, 350, 480, 140), 3)
        
        pygame.display.update()
        
    # mostrar los botones de movimiento
    if game_status == 'player move':
        
        game.fill(white)
        player_pokemon.draw()
        rival_pokemon.draw()
        player_pokemon.draw_hp()
        rival_pokemon.draw_hp()
        
        # crear un botón para cada movimiento
        move_buttons = []
        for i in range(len(player_pokemon.moves)):
            move = player_pokemon.moves[i]
            button_width = 240
            button_height = 70
            left = 10 + i % 2 * button_width
            top = 350 + i // 2 * button_height
            text_center_x = left + 120
            text_center_y = top + 35
            button = create_button(button_width, button_height, left, top, text_center_x, text_center_y, move.name.capitalize())
            move_buttons.append(button)
            
        # dibuja el borde negro
        pygame.draw.rect(game, black, (10, 350, 480, 140), 3)
        
        pygame.display.update()
        
    # rival selecciona un movimiento aleatorio para atacar
    if game_status == 'rival turn':
        
        game.fill(white)
        player_pokemon.draw()
        rival_pokemon.draw()
        player_pokemon.draw_hp()
        rival_pokemon.draw_hp()
        
        # vacíe el cuadro de visualización y haga una pausa de 2 segundos antes de atacar
        display_message('')
        time.sleep(2)
        
        # selecciona un movimiento aleatorio
        move = random.choice(rival_pokemon.moves)
        rival_pokemon.perform_attack(player_pokemon, move)
        
        # comprobar si el pokemon del jugador se desmayó
        if player_pokemon.current_hp == 0:
            game_status = 'fainted'
        else:
            game_status = 'player turn'
            
        pygame.display.update()
        
    # uno de los pokemons se desmayó
    if game_status == 'fainted':
        
        alpha = 255
        while alpha > 0:
            
            game.fill(white)
            player_pokemon.draw_hp()
            rival_pokemon.draw_hp()
            
            # determinar qué pokemon se desmayó
            if rival_pokemon.current_hp == 0:
                player_pokemon.draw()
                rival_pokemon.draw(alpha)
                display_message(f'{rival_pokemon.name} fainted!')
            else:
                player_pokemon.draw(alpha)
                rival_pokemon.draw()
                display_message(f'{player_pokemon.name} fainted!')
            alpha -= .4
            
            pygame.display.update()
            
        game_status = 'gameover'
        
    # pantalla de finalización del juego
    if game_status == 'gameover':
        
        display_message('Play again (Y/N)?')
        
pygame.quit()
