from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from users.models import CustomUser

class Review(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    reviewer = models.ForeignKey(CustomUser, related_name='reviews_given', on_delete=models.CASCADE)
    reviewee = models.ForeignKey(CustomUser, related_name='reviews_received', on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reviewer} rated {self.reviewee} {self.rating} stars"
