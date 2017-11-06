from common.pagination import Pagination128
from ping.views import PingSerializer
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated


class MentionsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = PingSerializer
    pagination_class = Pagination128
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.mentioned_by.select_related('user')
