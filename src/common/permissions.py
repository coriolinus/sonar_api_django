from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """
    Grants permission on a per-object level to the owner only.

    Derives from IsAuthenticatedOrReadOnly for view-level access;
    everyone can read anything, but only authenticated users can
    potentially write things.

    # Caution

    Object level permissions are [not run on list views](http://www.django-rest-framework.org/api-guide/permissions/#limitations-of-object-level-permissions).
    This is a DRF limitation. For list views, you'll want to filter the queryset appropriately.

    # Examples

    ## Basic Use

    If your view's objects have a `user` field which are the object's
    owner, then you can use this permission as-is:

    ```python
    class ProfileViewSet(ModelViewSet):
        permission_classes = (IsOwnerOrReadOnly,)
        ...
    ```

    ## Custom user field name

    If your view's objects use a field name other than `"user"` to
    link to the user object which owns the resource, you can
    derive a custom subclass which sets the `OWNER_FIELD` appropriately:

    ```python
    class Child(models.Model):
        parent = models.ForeignKey(User)

    class Child_IOORO(IsOwnerOrReadOnly):
        OWNER_FIELD = 'parent'

    class ChildViewSet(ModelViewSet):
        permission_classes = (Child_IOORO,)
        ...
    ```

    ## Other custom owner acquisition

    If your view's objects don't have a field linking to the appropriate
    owner, you can derive a custom subclass which overrides the `get_owner(self)`
    method, which should return that object's owner. This is most common for the
    `User` objects:

    ```python
    class User_IOORO(IsOwnerOrReadOnly):
        def get_owner(self, obj):
            return obj

    class UserViewSet(ModelViewSet):
        permission_classes = (User_IOORO,)
        ...
    ```
    """
    OWNER_FIELD = 'user'

    def get_owner(self, obj):
        """
        Get the owner of the supplied `obj` object.
        """
        return getattr(obj, self.OWNER_FIELD)

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS or
                request.user == self.get_owner(obj))


class IsOwner(permissions.IsAuthenticated):
    """
    Class which provides read/write object-level permissions for only the object's owner.

    Derives from IsAuthenticated for view-level access. Only authenticated users can
    potentially own objects.

    # Caution

    Object level permissions are [not run on list views](http://www.django-rest-framework.org/api-guide/permissions/#limitations-of-object-level-permissions).
    This is a DRF limitation. For list views, you'll want to filter the queryset appropriately.

    # Examples

    ## Basic Use

    If your view's objects have a `user` field which are the object's
    owner, then you can use this permission as-is:

    ```python
    class ProfileViewSet(ModelViewSet):
        permission_classes = (IsOwner,)
        ...
    ```

    ## Custom user field name

    If your view's objects use a field name other than `"user"` to
    link to the user object which owns the resource, you can
    derive a custom subclass which sets the `OWNER_FIELD` appropriately:

    ```python
    class Child(models.Model):
        parent = models.ForeignKey(User)

    class Child_IO(IsOwner):
        OWNER_FIELD = 'parent'

    class ChildViewSet(ModelViewSet):
        permission_classes = (Child_IO,)
        ...
    ```

    ## Other custom owner acquisition

    If your view's objects don't have a field linking to the appropriate
    owner, you can derive a custom subclass which overrides the `get_owner(self)`
    method, which should return that object's owner. This is most common for the
    `User` objects:

    ```python
    class User_IO(IsOwner):
        def get_owner(self, obj):
            return obj

    class UserViewSet(ModelViewSet):
        permission_classes = (User_IO,)
        ...
    ```
    """
    OWNER_FIELD = 'user'

    def get_owner(self, obj):
        """
        Get the owner of the supplied `obj` object.
        """
        return getattr(obj, self.OWNER_FIELD)

    def has_object_permission(self, request, view, obj):
        return request.user == self.get_owner(obj)
