from rest_framework.pagination import CursorPagination


class Pagination128(CursorPagination):
    page_size = 128
