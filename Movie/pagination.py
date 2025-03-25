from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination, CursorPagination


class MyPagination(PageNumberPagination):
    page_size = 2
    # page_size_query_param = 'size'
    max_page_size = 10
    
    
class MyLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 2
    max_limit = 10
    
class MyCursorPagination(CursorPagination):
    page_size = 2
    ordering = 'title'