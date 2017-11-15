from common.pagination import Pagination128
from ping.models import Hashtag, Ping
from ping.views import PingSerializer
from rest_framework import viewsets
from rest_framework.response import Response


class HashtagViewSet(viewsets.GenericViewSet):
    serializer_class = PingSerializer
    pagination_class = Pagination128
    queryset = Hashtag.objects.all()

    def retrieve(self, request, *args, **kwargs):
        hashtag = self.get_object()
        return Response(self.get_serializer(
            Ping.filter_unblocked(
                hashtag.in_pings.select_related('user'),
                self.request
            ),
            many=True,
            context={'request': request},
        ).data)
