"""
MODELS FOR IMDB CLONE REST API

This file defines the database structure for the movie review platform.
Three main models: StreamPlatform, Movie, and Review

Database Relationships:
- StreamPlatform (1) ----< (Many) Movie
- Movie (1) ----< (Many) Review
- User (1) ----< (Many) Review
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User


# ==================== STREAMING PLATFORM MODEL ====================
class StreamPlatform(models.Model):
    """
    Represents streaming platforms like Netflix, Amazon Prime, Disney+, etc.

    Fields:
        name: Platform name (e.g., "Netflix", "Amazon Prime")
        about: Short description of the platform
        website: Official website URL

    Relationships:
        movies: One-to-Many with Movie (One platform has many movies)
    """

    name = models.CharField(max_length=30)  # Platform name
    about = models.CharField(max_length=150)  # Platform description
    website = models.URLField(max_length=100)  # Platform website URL

    def __str__(self):
        """Returns platform name for admin display"""
        return self.name


# ==================== MOVIE MODEL ====================
class Movie(models.Model):
    """
    Represents individual movies/shows available on streaming platforms.

    Fields:
        title: Movie title
        storyline: Brief plot summary
        platform: Which streaming platform hosts this movie (ForeignKey)
        active: Whether movie is currently available
        avg_rating: Calculated average rating from all reviews
        number_rating: Total number of reviews received

    Relationships:
        platform: Many-to-One with StreamPlatform (Many movies belong to one platform)
        reviews: One-to-Many with Review (One movie has many reviews)
    """

    title = models.CharField(max_length=50)  # Movie title
    storyline = models.CharField(max_length=200)  # Plot summary

    # ForeignKey to StreamPlatform - Each movie belongs to one platform
    # on_delete=CASCADE: If platform is deleted, delete all its movies
    # related_name="movies": Access all movies of a platform via platform.movies.all()
    platform = models.ForeignKey(
        StreamPlatform, on_delete=models.CASCADE, related_name="movies"
    )

    active = models.BooleanField(default=True)  # Is movie currently available?
    avg_rating = models.FloatField(
        default=0
    )  # Average rating (calculated from reviews)
    number_rating = models.IntegerField(default=0)  # Total number of reviews
    # created = models.DateTimeField(auto_now_add=True)  # When movie was added

    def __str__(self):
        """Returns movie title for admin display"""
        return self.title


# ==================== REVIEW MODEL ====================
class Review(models.Model):
    """
    Represents user reviews for movies.

    Fields:
        review_user: Which user wrote this review (ForeignKey to User)
        rating: Star rating from 1 to 5
        description: Written review text
        movie: Which movie is being reviewed (ForeignKey)
        active: Whether review is active/approved
        update: When review was last updated

    Relationships:
        review_user: Many-to-One with User (One user can write many reviews)
        movie: Many-to-One with Movie (One movie can have many reviews)

    Validators:
        rating: Must be between 1 and 5 (enforced by MinValueValidator and MaxValueValidator)
    """

    # ForeignKey to User - Each review belongs to one user
    # on_delete=CASCADE: If user is deleted, delete all their reviews
    review_user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Rating field with validators: Must be integer between 1-5
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    description = models.CharField(max_length=200, null=True)  # Review text (optional)

    # ForeignKey to Movie - Each review is for one movie
    # on_delete=CASCADE: If movie is deleted, delete all its reviews
    # related_name="reviews": Access all reviews of a movie via movie.reviews.all()
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="reviews")

    active = models.BooleanField(default=True)  # Is review active/approved?
    # created = models.DateTimeField(auto_now_add=True, default=None)  # When review was created
    update = models.DateTimeField(
        auto_now=True
    )  # Auto-updates whenever review is modified

    def __str__(self):
        """Returns formatted string showing rating, movie, and user"""
        return (
            str(self.rating) + " | " + self.movie.title + " | " + str(self.review_user)
        )


"""
EXAMPLE DATABASE STRUCTURE:

StreamPlatform Table:
+----+---------+---------------------+------------------------+
| id | name    | about               | website                |
+----+---------+---------------------+------------------------+
| 1  | Netflix | Streaming service   | netflix.com            |
| 2  | Prime   | Amazon's platform   | primevideo.com         |
+----+---------+---------------------+------------------------+

Movie Table:
+----+-----------+-------------------+---------+--------+------------+---------------+
| id | title     | storyline         | platform| active | avg_rating | number_rating |
+----+-----------+-------------------+---------+--------+------------+---------------+
| 1  | Inception | Dream heist movie | 1       | True   | 4.5        | 2             |
| 2  | Interstellar| Space exploration| 1       | True   | 5.0        | 1             |
+----+-----------+-------------------+---------+--------+------------+---------------+

Review Table:
+----+-------------+--------+----------------+-------+--------+
| id | review_user | rating | description    | movie | active |
+----+-------------+--------+----------------+-------+--------+
| 1  | user1       | 5      | Amazing!       | 1     | True   |
| 2  | user2       | 4      | Great movie    | 1     | True   |
| 3  | user1       | 5      | Mind-blowing   | 2     | True   |
+----+-------------+--------+----------------+-------+--------+
"""
