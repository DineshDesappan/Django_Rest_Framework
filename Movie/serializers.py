from rest_framework import serializers
from .models import Movie, Review, StreamPlatform
from django.contrib.auth.models import User

class ReviewSerializer(serializers.ModelSerializer):
    review_user = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Review
        # fields = "__all__"
        exclude = ['movie']

class MovieSerializer(serializers.ModelSerializer):
    reviews = ReviewSerializer(many=True, read_only=True)
    # platform = serializers.CharField(source = 'platform.name', read_only = True)
    class Meta:
        model = Movie
        fields = "__all__"

class StreamPlatformSerializer(serializers.ModelSerializer):
    movies = MovieSerializer(many=True, read_only=True)
    
    class Meta:
        model = StreamPlatform
        fields = "__all__"