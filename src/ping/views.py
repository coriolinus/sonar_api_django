from common.permissions import IsOwnerOrReadOnly
from ping.models import Ping
from rest_framework import mixins, serializers, viewsets


class PingSerializer(serializers.HyperlinkedModelSerializer):
    edited = serializers.SerializerMethodField()

    class Meta:
        model = Ping
        fields = (
            'url',
            'user',
            'created',
            'edited',
            'text',
        )

        read_only_fields = (
            'user',
        )

        extra_kwargs = {'user': {'lookup_field': 'username'}}

    def get_edited(self, obj):
        edited_after = (obj.edited - obj.created).seconds
        if edited_after < 15:
            return None
        return edited_after


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
