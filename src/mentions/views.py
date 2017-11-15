from common.pagination import Pagination128
from ping.models import Ping
from ping.views import PingSerializer
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated


class MentionsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = PingSerializer
    pagination_class = Pagination128
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Ping.filter_unblocked(
            self.request.user.mentioned_by.select_related('user'),
            self.request
        )
