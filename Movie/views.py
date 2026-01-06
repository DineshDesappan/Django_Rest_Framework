"""
VIEWS FOR IMDB CLONE REST API

This file defines the API endpoints and their logic.
Uses Django REST Framework's ViewSets and Generic Views.

ViewSet: Automatically creates CRUD operations (Create, Read, Update, Delete)
Generic Views: Pre-built views for common operations (Create, List, Detail, etc.)

API Endpoints Created:
- StreamPlatform: /api/stream/ (CRUD)
- Movie: /api/movie/ (CRUD with pagination & filtering)
- Review: /api/movie/<id>/reviews/ (List, Create, Detail)
- UserReview: /api/review?username=<username> (List reviews by user)
"""

from rest_framework import permissions, generics, viewsets
from .models import Movie, Review, StreamPlatform
from .permissions import IsAdminOrReadOnly, IsReviewUserOrReadOnly
from .serializers import MovieSerializer, ReviewSerializer, StreamPlatformSerializer
from rest_framework.exceptions import ValidationError
from django.http import Http404
from .throttling import StreamThrottleAnon, StreamThrottleUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .pagination import MyPagination, MyLimitOffsetPagination, MyCursorPagination


# ==================== USER REVIEW VIEW ====================
class UserReview(generics.ListAPIView):
    """
    API Endpoint to get all reviews by a specific user

    URL: GET /api/review?username=<username>
    Example: /api/review?username=john_doe

    Purpose: View all reviews written by a particular user

    Permissions: Anyone can view (no authentication required)

    How it works:
        1. Get username from query parameter
        2. Filter reviews WHERE review_user.username = username
        3. Return list of reviews

    Example Response:
    [
        {
            "id": 1,
            "review_user": "john_doe",
            "rating": 5,
            "description": "Amazing movie!",
            "active": true,
            "update": "2025-01-06T10:30:00Z"
        },
        {...}
    ]
    """

    serializer_class = ReviewSerializer
    # permission_classes = [permissions.IsAuthenticated]  # Commented: No auth required

    def get_queryset(self):
        """
        Override queryset to filter by username from query parameter

        Flow:
            1. Extract 'username' from URL query params (?username=...)
            2. Filter Review objects where review_user__username matches
            3. Return filtered queryset
        """
        pk = self.request.query_params.get(
            "username"
        )  # Get username from ?username=...
        return Review.objects.filter(
            review_user__username=pk
        )  # Filter reviews by username


# ==================== STREAMING PLATFORM VIEWSET ====================
class StreamPlatformVS(viewsets.ModelViewSet):
    """
    API ViewSet for StreamPlatform CRUD operations

    ModelViewSet automatically creates these endpoints:
        GET    /api/stream/        - List all platforms
        POST   /api/stream/        - Create new platform
        GET    /api/stream/<id>/   - Get specific platform
        PUT    /api/stream/<id>/   - Update platform
        PATCH  /api/stream/<id>/   - Partial update
        DELETE /api/stream/<id>/   - Delete platform

    Permissions:
        - IsAdminOrReadOnly: Anyone can view, only admins can create/update/delete

    Throttling:
        - Anonymous users: Limited requests (defined in StreamThrottleAnon)
        - Authenticated users: Higher limit (defined in StreamThrottleUser)

    Response includes nested movies for each platform!
    """

    permission_classes = [
        IsAdminOrReadOnly
    ]  # Custom permission: Read for all, Write for admin
    throttle_classes = [StreamThrottleAnon, StreamThrottleUser]  # Rate limiting

    queryset = StreamPlatform.objects.all()  # All platforms
    serializer_class = StreamPlatformSerializer  # Includes nested movies
    # permission_classes = [permissions.IsAdminUser]  # Alternative: Only admins can access


# ==================== MOVIE VIEWSET ====================
class MovieVS(viewsets.ModelViewSet):
    """
    API ViewSet for Movie CRUD operations with advanced features

    ModelViewSet automatically creates these endpoints:
        GET    /api/movie/        - List all movies (with pagination)
        POST   /api/movie/        - Create new movie
        GET    /api/movie/<id>/   - Get specific movie
        PUT    /api/movie/<id>/   - Update movie
        PATCH  /api/movie/<id>/   - Partial update
        DELETE /api/movie/<id>/   - Delete movie

    Features:
        - Pagination: Shows 2 movies per page (cursor-based)
        - Filtering: Can filter movies by any field
        - Search: Can search in specific fields

    Permissions:
        - Commented out (anyone can access for now)
        # permission_classes = [IsAdminOrReadOnly]  # Uncomment for admin-only writes

    Pagination:
        - Uses cursor pagination (more efficient for large datasets)
        - Navigate: ?cursor=<cursor_value>

    Filter Backends:
        - DjangoFilterBackend: Filter by fields (?platform=1&active=true)
        - SearchFilter: Search functionality (?search=<term>)
    """

    # permission_classes = [IsAdminOrReadOnly]  # Uncomment to require admin for writes
    queryset = Movie.objects.all()  # All movies
    serializer_class = MovieSerializer  # Includes nested reviews
    # permission_classes = [permissions.IsAuthenticated]  # Uncomment to require login

    pagination_class = MyCursorPagination  # Cursor-based pagination (2 per page)
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
    ]  # Enable filtering & search


# ==================== REVIEW CREATE VIEW ====================
class ReviewCreate(generics.CreateAPIView):
    """
    API Endpoint to create a new review for a movie

    URL: POST /api/movie/<movie_id>/review/create/
    Example: POST /api/movie/1/review/create/

    Permissions:
        - Must be authenticated to create review

    Validation:
        - Each user can only review a movie ONCE
        - Movie must exist

    Automatic Rating Calculation:
        - Updates movie.avg_rating based on all reviews
        - Increments movie.number_rating count

    Request Body:
    {
        "rating": 5,
        "description": "Amazing movie!"
    }

    Response: Created review object

    Business Logic in perform_create():
        1. Get movie ID from URL
        2. Check if movie exists (404 if not)
        3. Check if user already reviewed this movie (ValidationError if yes)
        4. Calculate new average rating:
           - First review: avg_rating = rating
           - Subsequent reviews: avg_rating = (old_avg + new_rating) / 2
        5. Increment number_rating counter
        6. Save review with auto-filled review_user
    """

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]  # Must be logged in to review

    def perform_create(self, serializer):
        """
        Override create logic to add custom business logic

        Flow:
            1. Extract movie ID from URL
            2. Validate movie exists
            3. Check if user already reviewed this movie
            4. Update movie's average rating
            5. Save review with current user
        """
        # Get movie ID from URL parameter (e.g., /movie/1/review/create/)
        pk = self.kwargs.get("pk")

        # Try to get the movie, raise 404 if not found
        try:
            movie = Movie.objects.get(pk=pk)
        except Movie.DoesNotExist:
            raise Http404("Movie not found")

        # Check if this user already reviewed this movie
        review_user = self.request.user
        review_queryset = Review.objects.filter(movie=movie, review_user=review_user)
        if review_queryset.exists():
            raise ValidationError("You have already reviewed this movie")

        # ===== AUTOMATIC RATING CALCULATION =====

        # Case 1: First review for this movie
        if movie.number_rating == 0:
            movie.avg_rating = serializer.validated_data[
                "rating"
            ]  # First rating becomes average
            movie.number_rating = movie.number_rating + 1  # Increment count to 1

        # Case 2: Subsequent reviews
        else:
            # Calculate new average: (current_avg + new_rating) / 2
            movie.avg_rating = (
                movie.avg_rating + serializer.validated_data["rating"]
            ) / 2
            movie.number_rating = movie.number_rating + 1  # Increment review count

        movie.save()  # Save updated rating and count

        # Save review with auto-filled review_user and movie
        serializer.save(review_user=self.request.user, movie=movie)

    # permission_classes = [permissions.IsAuthenticated]


# ==================== REVIEW LIST VIEW ====================
class ReviewList(generics.ListAPIView):
    """
    API Endpoint to list all reviews for a specific movie

    URL: GET /api/movie/<movie_id>/reviews/
    Example: GET /api/movie/1/reviews/

    Purpose: Get all reviews for a movie

    Features:
        - Search: Can search by username or active status
        - Example: /api/movie/1/reviews/?search=john

    Permissions: Anyone can view (no authentication required)

    Search Fields:
        - review_user__username: Search by reviewer's username
        - active: Search by active status
    """

    serializer_class = ReviewSerializer
    # permission_classes = [permissions.IsAuthenticated]  # Commented: No auth required
    filter_backends = [filters.SearchFilter]  # Enable search functionality
    search_fields = ["review_user__username", "active"]  # Searchable fields

    def get_queryset(self):
        """
        Override queryset to filter reviews by movie ID from URL

        Flow:
            1. Extract movie ID from URL
            2. Filter Review objects where movie = movie_id
            3. Return filtered queryset
        """
        pk = self.kwargs.get("pk")  # Get movie ID from URL
        return Review.objects.filter(movie=pk)  # Return reviews for this movie only


# ==================== REVIEW DETAIL VIEW ====================
class ReviewDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    API Endpoint for a specific review (Retrieve, Update, Delete)

    RetrieveUpdateDestroyAPIView automatically creates these endpoints:
        GET    /api/movie/<movie_id>/review/<review_id>/   - Get review
        PUT    /api/movie/<movie_id>/review/<review_id>/   - Update review
        PATCH  /api/movie/<movie_id>/review/<review_id>/   - Partial update
        DELETE /api/movie/<movie_id>/review/<review_id>/   - Delete review

    Permissions:
        - IsReviewUserOrReadOnly:
          * Anyone can view (read)
          * Only the review author or admin can edit/delete (write)

    Purpose: Get/Update/Delete a specific review
    """

    permission_classes = [IsReviewUserOrReadOnly]  # Owner or admin can modify
    queryset = Review.objects.all()  # All reviews
    serializer_class = ReviewSerializer


"""
API ENDPOINT SUMMARY:

StreamPlatform:
    GET    /api/stream/        - List all platforms
    POST   /api/stream/        - Create platform (admin only)
    GET    /api/stream/<id>/   - Get platform details + all movies + all reviews
    PUT    /api/stream/<id>/   - Update platform (admin only)
    DELETE /api/stream/<id>/   - Delete platform (admin only)

Movie:
    GET    /api/movie/         - List movies (paginated, filterable, searchable)
    POST   /api/movie/         - Create movie
    GET    /api/movie/<id>/    - Get movie details + all reviews
    PUT    /api/movie/<id>/    - Update movie
    DELETE /api/movie/<id>/    - Delete movie

Review:
    GET    /api/movie/<id>/reviews/            - List all reviews for movie
    POST   /api/movie/<id>/review/create/      - Create review (auth required)
    GET    /api/movie/<id>/review/<review_id>/ - Get specific review
    PUT    /api/movie/<id>/review/<review_id>/ - Update review (owner only)
    DELETE /api/movie/<id>/review/<review_id>/ - Delete review (owner only)
    GET    /api/review?username=<username>     - Get all reviews by user

RATING CALCULATION EXAMPLE:
    Movie: Inception (no reviews yet)
    avg_rating = 0, number_rating = 0
    
    User1 reviews with rating=5:
        avg_rating = 5 (first review)
        number_rating = 1
    
    User2 reviews with rating=3:
        avg_rating = (5 + 3) / 2 = 4.0
        number_rating = 2
    
    User3 reviews with rating=4:
        avg_rating = (4.0 + 4) / 2 = 4.0
        number_rating = 3
"""
