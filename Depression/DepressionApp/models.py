from django.db import models

class ExperiencePost(models.Model):
    """Model to store user's positive experiences and success stories"""
    username = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    experience = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.IntegerField(default=0)
    is_approved = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} by {self.username}"
