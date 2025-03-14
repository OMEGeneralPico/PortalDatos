from django.db import models

class Presupuesto(models.Model):
    codigo = models.IntegerField()
    secretaria = models.CharField(max_length=255)
    direccion = models.CharField(max_length=255)
    tipo = models.CharField(max_length=100)
    nombre = models.CharField(max_length=255, blank=True, null=True)  # Opcional
    credito_actual = models.DecimalField(max_digits=15, decimal_places=2)
    compromiso = models.DecimalField(max_digits=15, decimal_places=2)
    disponible = models.DecimalField(max_digits=15, decimal_places=2)
    año = models.IntegerField(default=2025)

    def __str__(self):
        return f"{self.secretaria} - {self.tipo} ({self.codigo} {self.año})"