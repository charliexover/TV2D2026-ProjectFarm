import pygame
import json
import os

class Spritesheet:
    """
    Clase para cargar y gestionar spritesheets generadas por el editor.
    """

    def __init__(self, json_path):
        """Carga los datos del JSON y la imagen del spritesheet."""
        with open(json_path) as f:
            self.data = json.load(f)

        json_dir = os.path.dirname(json_path)
        configured_path = self.data['spritesheet_path']
        if os.path.isabs(configured_path):
            full_image_path = configured_path
        else:
            full_image_path = os.path.join(json_dir, configured_path)
            if not os.path.exists(full_image_path):
                full_image_path = os.path.join(
                    json_dir, os.path.basename(configured_path)
                )

        self.spritesheet = pygame.image.load(full_image_path).convert_alpha()

    def get_sprite(self, name):
        """Obtiene una única imagen (Surface) por su nombre."""
        # ... (el resto de esta clase se mantiene igual que en la versión anterior) ...
        for anim_name, anim_list in self.data['animations'].items():
            for sprite_data in anim_list:
                if sprite_data['name'] == name:
                    rect = pygame.Rect(
                        sprite_data['x'],
                        sprite_data['y'],
                        sprite_data['width'],
                        sprite_data['height']
                    )
                    return self.spritesheet.subsurface(rect)
        raise ValueError(f"Sprite con nombre '{name}' no encontrado en el JSON.")

    def get_animation_frames(self, anim_name):
        """Obtiene una lista de imágenes (Surfaces) para una animación."""
        if anim_name not in self.data['animations']:
            raise ValueError(f"Animación '{anim_name}' no encontrada en el JSON.")

        frames = []
        for sprite_data in self.data['animations'][anim_name]:
            rect = pygame.Rect(
                sprite_data['x'],
                sprite_data['y'],
                sprite_data['width'],
                sprite_data['height']
            )
            frames.append(self.spritesheet.subsurface(rect))
        return frames