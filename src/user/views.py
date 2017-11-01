from user.models import Follows, User

from common.permissions import IsOwnerOrReadOnly
from django.contrib.auth.password_validation import validate_password
from ping.models import Ping
from ping.views import PingSerializer
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import detail_route, list_route
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


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

    def validate_username(self, username):
        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError("This username already exists")
        return username.lower()

    def get_token(self, user):
        return Token.objects.get_or_create(user=user)[0].key


class FollowSerializer(serializers.HyperlinkedModelSerializer):
    follower = serializers.HyperlinkedRelatedField(
        view_name='user-detail',
        lookup_field='username',
        read_only=True,
    )
    followed = serializers.HyperlinkedRelatedField(
        view_name='user-detail',
        lookup_field='username',
        read_only=True,
    )

    class Meta:
        model = Follows
        fields = read_only_fields = (
            'follower', 'followed', 'created'
        )


class User_IOORO(IsOwnerOrReadOnly):
    def get_owner(self, obj):
        return obj

    def has_permission(self, request, view):
        """
        Users may be created without existing authentication
        """
        return request.method == 'POST' or super().has_permission(request, view)


class Pagination128(CursorPagination):
    page_size = 128


class UserPaginator(Pagination128):
    ordering = '-date_joined'


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

    @property
    def timeline_paginator(self):
        "Paginator for use with the timeline view"
        if not hasattr(self, '_timeline_paginator'):
            self._timeline_paginator = Pagination128()
        return self._timeline_paginator

    @property
    def following_paginator(self):
        "Paginator for use with the following view"
        if not hasattr(self, '_following_paginator'):
            self._following_paginator = UserPaginator()
        return self._following_paginator

    @property
    def followed_by_paginator(self):
        "Paginator for use with the followed by view"
        if not hasattr(self, '_followed_by_paginator'):
            self._followed_by_paginator = UserPaginator()
        return self._followed_by_paginator

    @detail_route()
    def timeline(self, request, username):
        """
        View providing a paginated list of a user's most recent pings.
        """
        # DRF pagination is not well documented; this code was assembled by
        # frankensteining together bits from rest_framework.mixins.ListModelMixin,
        # and rest_framework.generics.GenericAPIView.
        # It appears to work, but at this would be an excellent candidate for
        # proper stress-testing at some point.
        user = self.get_object()
        pings_qs = Ping.objects.filter(user=user)
        page = self.timeline_paginator.paginate_queryset(pings_qs, request)
        serializer = PingSerializer(
            page,
            many=True,
            context={'request': request},
        )
        return self.timeline_paginator.get_paginated_response(serializer.data)

    @detail_route(methods=['post'], permission_classes=[IsAuthenticated])
    def follow(self, request, username):
        """
        View allowing the authenticated user to follow this user.
        """
        follower = request.user
        followed = self.get_object()

        if follower != followed:
            follow, created = Follows.objects.get_or_create(follower=follower, followed=followed)
            if created:
                r_status = status.HTTP_201_CREATED
            else:
                r_status = status.HTTP_200_OK
            return Response(
                FollowSerializer(follow, context={'request': request}).data,
                status=r_status
            )
        else:
            return Response(
                {'error': 'Cannot follow oneself'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @detail_route(methods=['post'], permission_classes=[IsAuthenticated])
    def unfollow(self, request, username):
        """
        View allowing the authenticated user to unfollow this user.
        """
        follower = request.user
        followed = self.get_object()

        if follower != followed:
            Follows.objects.filter(follower=follower, followed=followed).delete()
            return Response(
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {'error': 'Cannot unfollow oneself'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @detail_route(url_path='follow-stats')
    def follow_stats(self, request, username):
        """
        View which returns some follow statistics about the given user.
        """
        user = self.get_object()
        following = Follows.objects.filter(follower=user).count()
        followed = Follows.objects.filter(followed=user).count()
        return Response({'following': following, 'followed': followed})

    @list_route(permission_classes=[IsAuthenticated])
    def following(self, request):
        """
        View which returns the list of users which this user is following.
        """
        following_qs = User.objects.filter(followed_by__follower=request.user)
        page = self.following_paginator.paginate_queryset(following_qs, request)
        serializer = UserSerializer(
            page,
            many=True,
            context={'request': request},
        )
        return self.following_paginator.get_paginated_response(serializer.data)

    @list_route(permission_classes=[IsAuthenticated], url_path='followed-by')
    def followed_by(self, request):
        """
        View which returns the list of users following this user.
        """
        following_qs = User.objects.filter(following__followed=request.user)
        page = self.followed_by_paginator.paginate_queryset(following_qs, request)
        serializer = UserSerializer(
            page,
            many=True,
            context={'request': request},
        )
        return self.followed_by_paginator.get_paginated_response(serializer.data)
