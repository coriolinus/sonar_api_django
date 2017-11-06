from common.pagination import Pagination128
from ping.models import Hashtag
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
            hashtag.in_pings.select_related('user'),
            many=True,
            context={'request': request},
        ).data)
