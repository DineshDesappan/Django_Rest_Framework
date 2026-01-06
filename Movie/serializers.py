"""
SERIALIZERS FOR IMDB CLONE REST API

Serializers convert complex data types (like Django models) to/from JSON format.
They handle:
- Converting Python objects → JSON (for API responses)
- Converting JSON → Python objects (for API requests)
- Data validation
- Nested relationships

Flow: Database Model ↔ Serializer ↔ JSON
"""

from rest_framework import serializers
from .models import Movie, Review, StreamPlatform
from django.contrib.auth.models import User


# ==================== REVIEW SERIALIZER ====================
class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for Review model

    Purpose: Convert Review objects to/from JSON

    Features:
        - review_user is read-only and shows username (not user ID)
        - Excludes 'movie' field (since review is accessed via movie.reviews API)
        - Auto-fills review_user from request.user in view

    Fields included: id, review_user (username), rating, description, active, update
    Fields excluded: movie (because we access reviews through /movie/<id>/reviews/)

    Example JSON Output:
    {
        "id": 1,
        "review_user": "john_doe",  <- Username, not ID
        "rating": 5,
        "description": "Amazing movie!",
        "active": true,
        "update": "2025-01-06T10:30:00Z"
    }
    """

    # StringRelatedField shows related object's __str__() method (username)
    # read_only=True: Can't set user when creating review (auto-filled in view)
    review_user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Review
        # fields = "__all__"  # Would include all fields
        exclude = ["movie"]  # Exclude movie field (already in URL)


# ==================== MOVIE SERIALIZER ====================
class MovieSerializer(serializers.ModelSerializer):
    """
    Serializer for Movie model

    Purpose: Convert Movie objects to/from JSON with nested reviews

    Features:
        - Includes nested reviews (all reviews for this movie)
        - Reviews are read-only (can't create reviews through movie API)
        - Shows platform name instead of ID (commented alternative)

    Nested Serializer:
        reviews: Uses ReviewSerializer to show full review data, not just IDs

    Example JSON Output:
    {
        "id": 1,
        "title": "Inception",
        "storyline": "Dream heist movie",
        "platform": 1,  <- Platform ID
        "active": true,
        "avg_rating": 4.5,
        "number_rating": 2,
        "reviews": [  <- Nested reviews (full objects, not just IDs)
            {
                "id": 1,
                "review_user": "john_doe",
                "rating": 5,
                "description": "Amazing!",
                "active": true,
                "update": "2025-01-06T10:30:00Z"
            },
            {
                "id": 2,
                "review_user": "jane_smith",
                "rating": 4,
                "description": "Great movie",
                "active": true,
                "update": "2025-01-06T11:00:00Z"
            }
        ]
    }
    """

    # Nested serializer - Shows full review data for all reviews of this movie
    # many=True: Movie can have many reviews (not just one)
    # read_only=True: Can't create/update reviews through movie API
    reviews = ReviewSerializer(many=True, read_only=True)

    # Alternative: Show platform name instead of ID (currently commented out)
    # platform = serializers.CharField(source='platform.name', read_only = True)

    class Meta:
        model = Movie
        fields = "__all__"  # Include all Movie fields + nested reviews


# ==================== STREAMING PLATFORM SERIALIZER ====================
class StreamPlatformSerializer(serializers.ModelSerializer):
    """
    Serializer for StreamPlatform model

    Purpose: Convert StreamPlatform objects to/from JSON with nested movies

    Features:
        - Includes nested movies (all movies on this platform)
        - Movies are read-only (can't create movies through platform API)
        - Each movie includes its nested reviews (double nesting!)

    Nested Serializer:
        movies: Uses MovieSerializer to show full movie data
        Each movie also includes its reviews (double nesting)

    Example JSON Output:
    {
        "id": 1,
        "name": "Netflix",
        "about": "Streaming service",
        "website": "https://netflix.com",
        "movies": [  <- Nested movies
            {
                "id": 1,
                "title": "Inception",
                "storyline": "Dream heist movie",
                "platform": 1,
                "active": true,
                "avg_rating": 4.5,
                "number_rating": 2,
                "reviews": [  <- Double nesting: reviews within movies
                    {
                        "id": 1,
                        "review_user": "john_doe",
                        "rating": 5,
                        "description": "Amazing!",
                        "active": true,
                        "update": "2025-01-06T10:30:00Z"
                    }
                ]
            },
            {
                "id": 2,
                "title": "Interstellar",
                ...
            }
        ]
    }
    """

    # Nested serializer - Shows full movie data for all movies on this platform
    # many=True: Platform can have many movies
    # read_only=True: Can't create/update movies through platform API
    # Note: MovieSerializer also includes nested reviews (double nesting!)
    movies = MovieSerializer(many=True, read_only=True)

    class Meta:
        model = StreamPlatform
        fields = "__all__"  # Include all StreamPlatform fields + nested movies


"""
SERIALIZER USAGE FLOW:

1. GET Request (Database → JSON):
   Database: Movie object
        ↓
   MovieSerializer.data
        ↓
   JSON: {"id": 1, "title": "Inception", ...}
        ↓
   API Response to client

2. POST Request (JSON → Database):
   Client sends JSON: {"title": "New Movie", "storyline": "..."}
        ↓
   MovieSerializer(data=request.data)
        ↓
   serializer.is_valid() - Validates data
        ↓
   serializer.save() - Creates Movie object in database

3. Nested Serializers:
   StreamPlatformSerializer includes MovieSerializer
   MovieSerializer includes ReviewSerializer
   
   Result: Platform API response includes full movie and review data
   GET /api/stream/1/ returns:
   - Platform info
   - All movies on platform
   - All reviews for each movie
"""
