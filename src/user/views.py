from user.models import User

from common.permissions import IsOwnerOrReadOnly
from django.contrib.auth.password_validation import validate_password
from rest_framework import mixins, serializers, viewsets
from rest_framework.authtoken.models import Token


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

        read_only_fields = (
            'username',
        )


class CreateUserSerializer(UserSerializer):
    token = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'password',
            'token',
        )

        extra_kwargs = {'password': {'write_only': True}}

        read_only_fields = (
            'token',
        )

    def validate_password(self, pw):
        validate_password(pw)
        return pw

    def get_token(self, user):
        return Token.objects.get_or_create(user=user)[0].key


class User_IOORO(IsOwnerOrReadOnly):
    def get_owner(self, obj):
        return obj

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
    permission_classes = (User_IOORO,)
    lookup_field = 'username'

    def get_serializer_class(self):
        "Use the appropriate serializer class"
        if self.request.method == 'POST':
            return CreateUserSerializer
        return UserSerializer

    def perform_create(self, serializer):
        """
        Override perform_create to use the create_user function.

        This means that i.e. the password gets set appropriately
        """
        serializer.instance = User.objects.create_user(**serializer.validated_data)
