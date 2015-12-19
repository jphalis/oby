from itertools import chain

from django.shortcuts import get_object_or_404, Http404
from django.utils.crypto import get_random_string
from django.utils.text import slugify

from rest_framework import generics, mixins, permissions, status
from rest_framework.decorators import api_view
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response as RestResponse
from rest_framework.reverse import reverse as api_reverse
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from accounts.models import Follower, MyUser
from comments.models import Comment
from core.mixins import CacheMixin
from hashtags.models import Hashtag
from notifications.models import Notification
from notifications.signals import notify
from photos.models import Category, Photo
from shop.models import Product
from shop.signals import listuse_status_check
from .account_serializers import (AccountCreateSerializer, FollowerSerializer,
                                  MyUserSerializer)
from .auth_serializers import (PasswordResetSerializer,
                               PasswordResetConfirmSerializer,
                               PasswordChangeSerializer)
from .comment_serializers import (CommentCreateSerializer,
                                  CommentUpdateSerializer)
from .hashtag_serializers import HashtagSerializer
from .mixins import DefaultsMixin, FiltersMixin
from .notification_serializers import NotificationSerializer
from .pagination import (AccountPagination, HashtagPagination,
                         NotificationPagination, PhotoPagination,
                         ShopPagination)
from .permissions import (IsAdvertiser, IsCreatorOrReadOnly, IsOwnerOrReadOnly,
                          MyUserIsOwnerOrReadOnly)
from .photo_serializers import (CategorySerializer, PhotoCreateSerializer,
                                PhotoSerializer)
from .search_serializers import SearchMyUserSerializer
from .shop_serializers import ProductCreateSerializer, ProductSerializer

# Create your views here.


class APIHomeView(CacheMixin, DefaultsMixin, APIView):
    cache_timeout = 120

    def get(self, request, format=None):
        data = {
            'authentication': {
                'login': api_reverse('auth_login_api', request=request),
                'password_reset': api_reverse('rest_password_reset',
                                              request=request),
                'password_change': api_reverse('rest_password_change',
                                               request=request)
            },
            'accounts': {
                'count': MyUser.objects.all().count(),
                'url': api_reverse('user_account_list_api', request=request),
                'create_url': api_reverse('account_create_api',
                                          request=request),
                'edit_profile_url': api_reverse(
                    'user_account_detail_api', request=request,
                    kwargs={'username': request.user.username})
            },
            'categories': {
                'url': api_reverse('category_list_api', request=request),
            },
            'comments': {
                'create_url': api_reverse('comment_create_api',
                                          request=request),
            },
            'hashtags': {
                'count': Hashtag.objects.all().count(),
                'url': api_reverse('hashtag_list_api', request=request),
            },
            'homepage': {
                'url': api_reverse('homepage_api', request=request),
            },
            'notifications': {
                'url': api_reverse('notification_list_api', request=request),
            },
            'photos': {
                'count': Photo.objects.all().count(),
                'url': api_reverse('photo_list_api', request=request),
                'create_url': api_reverse('photo_create_api', request=request),
            },
            'search': {
                'url': api_reverse('search_api', request=request),
                'help_text': "add '?q=searched_parameter' to the "
                             "end of the url to display results"
            },
            'shop': {
                'count': Product.objects.all().count(),
                'url': api_reverse('product_list_api', request=request),
                'create_url': api_reverse('product_create_api',
                                          request=request),
            },
            'timeline': {
                'url': api_reverse('timeline_api', request=request),
            },
        }
        return RestResponse(data)


class HomepageAPIView(CacheMixin, DefaultsMixin, generics.ListAPIView):
    cache_timeout = 60 * 4
    serializer_class = PhotoSerializer

    def get_queryset(self):
        return Photo.objects.most_liked_offset()[:30]


class TimelineAPIView(CacheMixin, DefaultsMixin, generics.ListAPIView):
    cache_timeout = 60 * 4
    serializer_class = PhotoSerializer

    def get_queryset(self):
        user = self.request.user
        photos_self = Photo.objects.own(user)

        try:
            follow = Follower.objects \
                .select_related('user') \
                .get(user=user)
        except Follower.DoesNotExist:
            follow = None

        if follow:
            photos_following = Photo.objects.following(user)
            return (photos_self | photos_following).distinct()[:250]
        else:
            # Add suggested users
            photos_suggested = Photo.objects \
                .select_related("creator", "category") \
                .prefetch_related('likers') \
                .exclude(creator=user)[:50]
            photos = chain(photos_self, photos_suggested)
            return photos


# A C C O U N T S
@api_view(['POST'])
def follow_create_api(request, user_pk):
    follower, created = Follower.objects.get_or_create(user=request.user)
    user = get_object_or_404(MyUser, pk=user_pk)
    followed, created = Follower.objects.get_or_create(user=user)

    try:
        user_followed = (Follower.objects.select_related('user')
                                         .get(user=user, followers=follower))
    except Follower.DoesNotExist:
        user_followed = None

    if user_followed:
        followed.followers.remove(follower)
    else:
        followed.followers.add(follower)
        notify.send(
            request.user,
            recipient=user,
            verb='is now supporting you'
        )
    serializer = FollowerSerializer(followed, context={'request': request})
    return RestResponse(serializer.data, status=status.HTTP_201_CREATED)


class AccountCreateAPIView(generics.CreateAPIView):
    serializer_class = AccountCreateSerializer


class MyUserListAPIView(CacheMixin, DefaultsMixin, generics.ListAPIView):
    cache_timeout = 60 * 4
    pagination_class = AccountPagination
    serializer_class = MyUserSerializer
    queryset = MyUser.objects.all()


class MyUserDetailAPIView(CacheMixin,
                          generics.RetrieveAPIView,
                          mixins.DestroyModelMixin,
                          mixins.UpdateModelMixin):
    cache_timeout = 60 * 3
    permission_classes = (
        permissions.IsAuthenticated,
        MyUserIsOwnerOrReadOnly,
    )
    serializer_class = MyUserSerializer
    parser_classes = (MultiPartParser, FormParser,)

    def get_object(self):
        username = self.kwargs["username"]
        obj = get_object_or_404(MyUser, username=username)
        return obj

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


# A U T H E N T I C A T I O N
class PasswordResetView(generics.GenericAPIView):
    """
    Calls PasswordResetForm save method
    Accepts the following POST parameters: email
    Returns the success/fail message
    """
    serializer_class = PasswordResetSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return RestResponse(
            {"success": "Password reset e-mail has been sent."},
            status=status.HTTP_200_OK)


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    Password reset e-mail link is confirmed, so this resets the user's password
    Accepts the following POST parameters: new_password1, new_password2
    Accepts the following Django URL arguments: token, uid
    Returns the success/fail message
    """
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return RestResponse({"success": "Password has been reset."})


class PasswordChangeView(generics.GenericAPIView):
    """
    Calls SetPasswordForm save method
    Accepts the following POST parameters: new_password1, new_password2
    Returns the success/fail message
    """
    serializer_class = PasswordChangeSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return RestResponse({"success": "New password has been saved."})


# C O M M E N T S
class CommentCreateAPIView(CacheMixin, generics.CreateAPIView):
    serializer_class = CommentCreateSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        parent_id = self.request.data.get('parent')
        photo_id = self.request.data.get('photo')
        parent_comment = None

        try:
            photo = (Photo.objects.select_related('category', 'creator')
                                  .get(id=photo_id))
        except:
            photo = None

        if parent_id is not None:
            try:
                parent_comment = Comment.objects.select_related(
                    'user', 'photo').get(id=parent_id)
            except:
                parent_comment = None
            if parent_comment is not None and parent_comment.photo is not None:
                photo = parent_comment.photo

        if serializer.is_valid():
            comment_text = self.request.data.get('text')
            if parent_comment is not None:
                # parent comments exists
                new_child_comment = Comment.objects.create_comment(
                    user=self.request.user,
                    path=parent_comment.get_origin,
                    text=comment_text,
                    photo=photo,
                    parent=parent_comment
                )
                affected_users = parent_comment.get_affected_users()
                notify.send(
                    self.request.user,
                    action=new_child_comment,
                    target=parent_comment,
                    recipient=parent_comment.user,
                    affected_users=affected_users,
                    verb='replied to'
                )
            else:
                new_parent_comment = Comment.objects.create_comment(
                    user=request.user,
                    path=request.get_full_path,
                    text=comment_text,
                    photo=photo
                )
                notify.send(
                    self.request.user,
                    action=new_parent_comment,
                    target=new_parent_comment.photo,
                    recipient=photo.creator,
                    verb='commented'
                )
            return RestResponse(serializer.data,
                                status=status.HTTP_201_CREATED)
        else:
            return RestResponse(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)


class CommentDetailAPIView(CacheMixin,
                           generics.RetrieveAPIView,
                           mixins.DestroyModelMixin):
    cache_timeout = 60 * 4
    lookup_field = 'id'
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrReadOnly,)
    serializer_class = CommentUpdateSerializer

    def get_queryset(self, *args, **kwargs):
        queryset = (Comment.objects.select_related('user', 'photo')
                                   .filter(pk__gte=0))
        return queryset

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


# H A S H T A G S
class HashtagListAPIView(CacheMixin, DefaultsMixin, FiltersMixin,
                         generics.ListAPIView):
    cache_timeout = 60 * 4
    pagination_class = HashtagPagination
    serializer_class = HashtagSerializer
    queryset = Hashtag.objects.all()
    search_fields = ["tag"]


# N O T I F I C A T I O N S
class NotificationAPIView(CacheMixin, DefaultsMixin, generics.ListAPIView):
    cache_timeout = 60 * 4
    pagination_class = NotificationPagination
    serializer_class = NotificationSerializer

    def get_queryset(self):
        notifications = Notification.objects.all_for_user(
            self.request.user)[:50]
        for notification in notifications:
            if notification.recipient == self.request.user:
                notification.read = True
                notification.save()
            else:
                raise Http404
        return notifications


class NotificationAjaxAPIView(CacheMixin, DefaultsMixin, generics.ListAPIView):
    pagination_class = NotificationPagination
    serializer_class = NotificationSerializer

    def get_queryset(self):
        notifications = Notification.objects.all_unread(
            self.request.user)[:1]
        return notifications


# P H O T O S
@api_view(['POST'])
def like_create_api(request, photo_pk):
    user = request.user
    photo = get_object_or_404(Photo, pk=photo_pk)

    if user in photo.likers.all():
        photo.likers.remove(user)
    else:
        photo.likers.add(user)
        notify.send(
            user,
            action=photo,
            target=photo,
            recipient=photo.creator,
            verb='liked'
        )
    serializer = PhotoSerializer(photo, context={'request': request})
    return RestResponse(serializer.data, status=status.HTTP_201_CREATED)


class PhotoCreateAPIView(ModelViewSet):
    queryset = Photo.objects.select_related('creator').all()
    serializer_class = PhotoCreateSerializer
    parser_classes = (MultiPartParser, FormParser,)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user,
                        slug=get_random_string(length=10),
                        photo=self.request.data.get('photo'))


class PhotoListAPIView(CacheMixin, DefaultsMixin, FiltersMixin,
                       generics.ListAPIView):
    cache_timeout = 60 * 3
    pagination_class = PhotoPagination
    serializer_class = PhotoSerializer
    queryset = (Photo.objects.select_related('creator', 'category')
                             .prefetch_related('likers')
                             .all())
    search_fields = ('description',)
    ordering_fields = ('created', 'modified',)


class PhotoDetailAPIView(CacheMixin,
                         generics.RetrieveAPIView,
                         mixins.DestroyModelMixin,
                         mixins.UpdateModelMixin):
    cache_timeout = 60 * 3
    permission_classes = (permissions.IsAuthenticated, IsCreatorOrReadOnly,)
    serializer_class = PhotoSerializer

    def get_object(self):
        cat_slug = self.kwargs["cat_slug"]
        photo_slug = self.kwargs["photo_slug"]
        category = get_object_or_404(Category, slug=cat_slug)
        obj = get_object_or_404(Photo, category=category, slug=photo_slug)
        return obj

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class CategoryListAPIView(CacheMixin, DefaultsMixin, generics.ListAPIView):
    cache_timeout = 60 * 5
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.most_posts()


class CategoryDetailAPIView(CacheMixin, DefaultsMixin,
                            generics.RetrieveAPIView):
    cache_timeout = 60 * 4
    serializer_class = CategorySerializer

    def get_object(self):
        slug = self.kwargs["slug"]
        obj = get_object_or_404(Category, slug=slug)
        return obj


# S E A R C H
class SearchListAPIView(CacheMixin, DefaultsMixin, FiltersMixin,
                        generics.ListAPIView):
    serializer_class = SearchMyUserSerializer
    # '^' Starts-with search
    # '=' Exact matches
    # '@' Full-text search (Currently only supported Django's MySQL backend.)
    # '$' Regex search
    search_fields = ('^username', '^full_name',)
    # ordering_fields = ('id', 'username', 'full_name',)

    def get_queryset(self):
        queryset = MyUser.objects.all() \
            .only('id', 'username', 'full_name', 'profile_picture')
        username = self.request.query_params.get('username', None)
        full_name = self.request.query_params.get('full_name', None)

        if username and full_name is not None:
            queryset = queryset.filter(username=username, full_name=full_name)
        elif username is not None:
            queryset = queryset.filter(username=username)
        elif full_name is not None:
            queryset = queryset.filter(full_name=full_name)
        return queryset


# S H O P
# Need to fix the list_use_date_start
class ProductCreateAPIView(ModelViewSet):
    queryset = Product.objects.select_related('owner').all()
    serializer_class = ProductCreateSerializer
    parser_classes = (MultiPartParser, FormParser,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user,
                        slug=slugify(self.request.data.get('title')),
                        image=self.request.data.get('image'))


class ProductListAPIView(CacheMixin, DefaultsMixin, FiltersMixin,
                         generics.ListAPIView):
    cache_timeout = 60 * 4
    pagination_class = ShopPagination
    serializer_class = ProductSerializer
    search_fields = ('title', 'owner',)
    ordering_fields = ('created', 'modified', 'list_date_start',)

    def get_queryset(self):
        products = (Product.objects.select_related('owner')
                                   .prefetch_related('buyers')
                                   .all())
        for product in products:
            listuse_status_check.send(sender=product)
        queryset = products.filter(is_listed=True)
        return queryset


class ProductDetailAPIView(CacheMixin, DefaultsMixin,
                           generics.RetrieveAPIView,
                           mixins.DestroyModelMixin,
                           mixins.UpdateModelMixin):
    cache_timeout = 60 * 4
    permission_classes = (IsAdvertiser, IsOwnerOrReadOnly,)
    queryset = (Product.objects.select_related('owner')
                               .prefetch_related('buyers')
                               .all())
    serializer_class = ProductSerializer

    def get_object(self):
        product_slug = self.kwargs["product_slug"]
        obj = get_object_or_404(Product, slug=product_slug)
        return obj

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
