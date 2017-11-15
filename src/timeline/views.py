from user.models import Follow

from common.pagination import Pagination128
from django.db.models import Q, Subquery
from ping.models import Ping
from ping.views import PingSerializer
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated


class TimelineViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = PingSerializer
    pagination_class = Pagination128
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        follows = Follow.objects.filter(follower=self.request.user)
        return Ping.objects_unblocked(self.request).filter(
            Q(user=self.request.user) |
            Q(user__in=Subquery(follows.values('followed')))
        ).select_related('user', 'replying_to')
