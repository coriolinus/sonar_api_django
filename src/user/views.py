from common.permissions import IsOwnerOrReadOnly
from rest_framework import mixins, serializers, viewsets
from user.models import User


class UserSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='user-detail',
        lookup_field='username',
    )

    class Meta:
        model = User
        fields = (
            'url',
            'username',
            'first_name',
            'last_name',
            'email',
            'blurb',
        )


class User_IOORO(IsOwnerOrReadOnly):
    def get_owner(self):
        return self

    def has_permission(self, request, view):
        """
        Users may be created without existing authentication
        """
        return request.method == 'POST' or super().has_permission(request, view)


class UserViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    """
    Provide CRUD operations for Users.

    Note that we do not specify the ListModelMixin;
    we don't want there to be a way for anyone to get
    a complete user list.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (User_IOORO,)
    lookup_field = 'username'
