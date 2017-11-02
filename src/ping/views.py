from common.pagination import Pagination128
from common.permissions import IsOwnerOrReadOnly
from ping.models import Ping
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class PingSerializer(serializers.HyperlinkedModelSerializer):
    edited = serializers.SerializerMethodField()

    class Meta:
        model = Ping
        fields = (
            'url',
            'replying_to',
            'user',
            'created',
            'edited',
            'text',
        )

        read_only_fields = (
            'user',
            'replying_to',
        )

        extra_kwargs = {'user': {'lookup_field': 'username'}}

    def get_edited(self, obj):
        edited_after = (obj.edited - obj.created).seconds
        if edited_after < 15:
            return None
        return edited_after


class AscendingPagination128(Pagination128):
    ordering = 'created'


class PingViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    """
    Provide CRUD operations for Users.

    Note that we do not specify the ListModelMixin;
    we want users to use a timeline view to view pings.
    """
    queryset = Ping.objects.all()
    serializer_class = PingSerializer
    permission_classes = (IsOwnerOrReadOnly,)

    def perform_create(self, serializer):
        """
        Override perform_create to insert the appropriate user

        This means that i.e. the password gets set appropriately
        """
        serializer.save(user=self.request.user)

    @detail_route(methods=['post'], permission_classes=(IsAuthenticated,))
    def reply(self, request, pk):
        """
        Create a new Ping in response to this one.

        This is the official way to reply to a ping, and frontends should
        use this instead of POSTing /pings/ when they create replies.
        """
        serializer = PingSerializer(data=request.data,
                                    context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(
            user=self.request.user,
            replying_to=self.get_object(),
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @property
    def replies_paginator(self):
        "Paginator for use with the replies view"
        if not hasattr(self, '_replies_paginator'):
            self._replies_paginator = AscendingPagination128()
        return self._replies_paginator

    @detail_route()
    def replies(self, request, pk):
        """
        View providing a paginated list of replies to a given ping
        """
        replied_to = self.get_object()
        replies_qs = replied_to.replies.select_related('user', 'replying_to')
        page = self.replies_paginator.paginate_queryset(replies_qs, request)
        serializer = PingSerializer(
            page,
            many=True,
            context={'request': request},
        )
        return self.replies_paginator.get_paginated_response(serializer.data)
