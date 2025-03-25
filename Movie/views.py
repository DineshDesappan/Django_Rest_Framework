from rest_framework import permissions, generics, viewsets
from .models import Movie, Review, StreamPlatform
from .permissions import IsAdminOrReadOnly, IsReviewUserOrReadOnly
from .serializers import MovieSerializer, ReviewSerializer, StreamPlatformSerializer
from rest_framework.exceptions import ValidationError
from django.http import Http404
from . throttling import StreamThrottleAnon, StreamThrottleUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from . pagination import MyPagination, MyLimitOffsetPagination, MyCursorPagination



class UserReview(generics.ListAPIView):
    serializer_class = ReviewSerializer
    # permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        pk = self.request.query_params.get('username')
        return Review.objects.filter(review_user__username = pk)
    
class StreamPlatformVS(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    throttle_classes = [StreamThrottleAnon, StreamThrottleUser]

    queryset = StreamPlatform.objects.all()
    serializer_class = StreamPlatformSerializer
    # permission_classes = [permissions.IsAdminUser]

class MovieVS(viewsets.ModelViewSet):
    # permission_classes = [IsAdminOrReadOnly]
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    # permission_classes = [permissions.IsAuthenticated]
    pagination_class = MyCursorPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    

class ReviewCreate(generics.CreateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    
    def perform_create(self, serializer):
        pk = self.kwargs.get('pk')
        try:
            movie = Movie.objects.get(pk=pk)
        except Movie.DoesNotExist:
            raise Http404("Movie not found")
        
        review_user = self.request.user
        review_queryset = Review.objects.filter(movie=movie, review_user=review_user)
        if review_queryset.exists():
            raise ValidationError("You have already reviewed this movie")
        
        if movie.number_rating == 0:
            movie.avg_rating = serializer.validated_data['rating']
            movie.number_rating = movie.number_rating + 1
            
        else:
            movie.avg_rating = (movie.avg_rating + serializer.validated_data['rating'])/2
            movie.number_rating = movie.number_rating + 1
            
        movie.save()
        
        serializer.save(review_user=self.request.user, movie=movie)
    # permission_classes = [permissions.IsAuthenticated]

class ReviewList(generics.ListAPIView):
    serializer_class = ReviewSerializer
    # permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['review_user__username', 'active']
    
    def get_queryset(self):
        pk = self.kwargs.get('pk')
        return Review.objects.filter(movie=pk)

class ReviewDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsReviewUserOrReadOnly]
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer