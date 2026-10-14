from django.db import models


class Route(models.Model):
    origin_name = models.CharField(max_length=120)
    destination_name = models.CharField(max_length=120)
    boarding_point = models.CharField(max_length=160)
    destination_point = models.CharField(max_length=160)
    display_label = models.CharField(max_length=180)
    is_demo = models.BooleanField(default=False)

    def __str__(self):
        return self.display_label
