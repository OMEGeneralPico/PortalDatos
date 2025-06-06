# models.py
from django.db import models

class TipoGasto(models.Model):
    tipo = models.IntegerField()  # Atributo tipo como número
    categoria = models.IntegerField()  # Atributo categoria como número
    descripcion = models.TextField()  # Atributo descripcion como texto

    def __str__(self):
        return self.descripcion  # O cualquier otro campo que desees mostrar

class Presupuesto(models.Model):
    codigo = models.IntegerField()
    secretaria = models.CharField(max_length=255)
    direccion = models.CharField(max_length=255)
    tipo = models.CharField(max_length=100)
    nombre = models.CharField(max_length=255, blank=True, null=True)
    credito_actual = models.DecimalField(max_digits=15, decimal_places=2) # This is your initial "presupuestado"
    reestructuras = models.DecimalField(max_digits=15, decimal_places=2, default=0.00) # New field for budget adjustments
    compromiso = models.DecimalField(max_digits=15, decimal_places=2)
    disponible = models.DecimalField(max_digits=15, decimal_places=2) # This should reflect: credito_actual + reestructuras - compromiso
    año = models.IntegerField(default=2025)

    def __str__(self):
        return f"{self.secretaria} - {self.tipo} ({self.codigo} {self.año})"

    # Optional: Add a property to calculate available funds if 'disponible' isn't always pre-calculated perfectly
    @property
    def disponible_calculado(self):
        return self.credito_actual + self.reestructuras - self.compromiso

    # Optional: If you want to enforce the calculation when saving, you can override save method
    # Be cautious with this if 'disponible' can also be directly imported/modified from other sources.
    # def save(self, *args, **kwargs):
    #     self.disponible = self.credito_actual + self.reestructuras - self.compromiso
    #     super().save(*args, **kwargs)