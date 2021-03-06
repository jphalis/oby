from rest_framework import permissions, serializers, viewsets
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from rest_framework.reverse import reverse as api_reverse
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from comments.models import Comment


class CommentCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Comment
        fields = [
            'id',
            'user',
            'username',
            'parent',
            'photo',
            'text',
        ]


class CommentUpdateSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField(read_only=True)
    user = serializers.CharField(source='user.username', read_only=True)
    user_url = serializers.HyperlinkedRelatedField(
        view_name='user_profile_detail_api', read_only=True,
        lookup_field='username')

    class Meta:
        model = Comment
        fields = [
            'id',
            'user',
            'user_url',
            'text',
            'children',
        ]

    def get_children(self, instance):
        queryset = Comment.objects.filter(parent__pk=instance.pk)
        serializer = ChildCommentSerializer(queryset,
                                            context={"request": instance},
                                            many=True)
        return serializer.data


class ChildCommentSerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Comment
        fields = [
            'id',
            'user',
            'text',
        ]


class CommentPhotoUrlField(serializers.HyperlinkedIdentityField):
    def get_url(self, obj, view_name, request, format):
        photo = None

        if obj.is_child:
            try:
                photo = obj.parent.photo
            except:
                photo = None
        else:
            try:
                photo = obj.photo
            except:
                photo = None

        if photo:
            kwargs = {
                'cat_slug': obj.photo.category.slug,
                'photo_slug': obj.photo.slug
            }
            return api_reverse(view_name, kwargs=kwargs,
                               request=request, format=format)
        else:
            return None


class CommentSerializer(serializers.HyperlinkedModelSerializer):
    photo = CommentPhotoUrlField("photo_detail_api")
    comment_url = serializers.HyperlinkedIdentityField("comment_detail_api",
                                                       lookup_field='id')
    user = serializers.HyperlinkedRelatedField(
        view_name='user_profile_detail_api', read_only=True,
        lookup_field='username')
    text = serializers.CharField(read_only=True)
    children = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Comment
        fields = [
            'id',
            'photo',
            'comment_url',
            'user',
            'text',
            'children',
        ]

    def get_children(self, instance):
        queryset = Comment.objects.filter(parent__pk=instance.pk)
        serializer = ChildCommentSerializer(queryset,
                                            context={"request": instance},
                                            many=True)
        return serializer.data


class CommentViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication, BasicAuthentication,
                              JSONWebTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
