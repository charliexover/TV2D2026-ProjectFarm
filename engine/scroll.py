import pygame


class Camera:
	def __init__(self):
		self.offset = (0, 0)
		self.world_bounds = pygame.Rect(0, 0, 0, 0)

	def update(self, target, viewport, world_bounds):
		self.world_bounds = pygame.Rect(world_bounds)
		max_x = max(
			self.world_bounds.left,
			self.world_bounds.right - viewport.width,
		)
		max_y = max(
			self.world_bounds.top,
			self.world_bounds.bottom - viewport.height,
		)
		self.offset = (
			max(
				self.world_bounds.left,
				min(target.centerx - viewport.centerx, max_x),
			),
			max(
				self.world_bounds.top,
				min(target.centery - viewport.centery, max_y),
			),
		)

	def apply(self, rect):
		return rect.move(-self.offset[0], -self.offset[1])

	def to_world(self, position):
		return (
			position[0] + self.offset[0],
			position[1] + self.offset[1],
		)

	def to_map(self, rect):
		return rect.move(-self.world_bounds.left, -self.world_bounds.top)

	@property
	def screen_offset(self):
		return (-self.offset[0], -self.offset[1])
