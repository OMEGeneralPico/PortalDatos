from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Si es admin puede ver todo
    is_admin = models.BooleanField(default=False)
    
    # Áreas que puede ver este usuario
    areas_permitidas = models.CharField(max_length=255, help_text="Ej: 10,20,21")

    def get_areas_list(self):
        return self.areas_permitidas.split(',')

    def __str__(self):
        return f"{self.user.username} - Áreas: {self.areas_permitidas}"
