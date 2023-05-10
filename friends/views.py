from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, mixins, viewsets, status
from rest_framework.exceptions import ErrorDetail
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import Friendship, User, STATUS_STR
from .serializers import UserSerializer, FriendshipSerializer, FriendshipStatusSerializer, UserRegisterSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserRegisterSerializer


class FriendsViewSet(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     mixins.DestroyModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    serializer_classes = {'list': UserSerializer,
                          'retrieve': FriendshipStatusSerializer,
                          'create': FriendshipSerializer}
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        """Список друзей"""
        return super(FriendsViewSet, self).list(request, *args, **kwargs)

    @swagger_auto_schema(responses={status.HTTP_200_OK: FriendshipSerializer(),
                                    status.HTTP_201_CREATED: FriendshipSerializer(),
                                    status.HTTP_208_ALREADY_REPORTED: FriendshipSerializer()})
    def create(self, request, *args, **kwargs):
        """Отправить заявку в друзья"""
        ser = FriendshipSerializer(data=request.data)
        if ser.is_valid():
            user = get_object_or_404(User, pk=request.data.get("friend2", 0))
            if request.user != user:
                response, stat = request.user.add_request_friendship(user)
                serializer = FriendshipSerializer(response)
                return Response(serializer.data, status=stat)
            return Response({'detail': ErrorDetail("Нельзя отправить заявку самому себе.", code='bad_self_request')},
                            status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        """Посмотреть статус дружбы"""
        user = get_object_or_404(User, pk=kwargs['pk'])
        status_string = "Это вы."
        if request.user != user:
            s = request.user.get_friendship_status(user)
            status_string = STATUS_STR.get(s, "Вы еще не друзья.")
        return Response({'friendship_status': status_string}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """Удалить друга"""
        user = get_object_or_404(User, pk=kwargs['pk'])
        request.user.delete_friend(user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        return self.request.user.get_users_friends()

    def get_serializer_class(self, *args, **kwargs):
        return self.serializer_classes.get(self.action, None)


class FriendshipViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.DestroyModelMixin,
                        viewsets.GenericViewSet):
    serializer_class = FriendshipSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        """Список заявок"""
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """Принять заявку в друзья"""
        friendship = get_object_or_404(Friendship, pk=kwargs['pk'])
        if friendship.friend1 == request.user and friendship.status == 1:
            friendship = friendship.accept_friendship()
            return Response(FriendshipSerializer(friendship).data, status=status.HTTP_200_OK)
        return Response(
            {"detail": ErrorDetail("Попытка доступа к чужой или неактуальной заявке.", code='not_your_request')},
            status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """Отклонить заявку в друзья"""
        friendship = get_object_or_404(Friendship, pk=kwargs['pk'])
        if friendship.friend1 == request.user and friendship.status == 1:
            friendship.reject_friendship()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"detail": ErrorDetail("Попытка доступа к чужой или неактуальной заявке.", code='not_your_request')},
            status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        return Friendship.objects.filter(friend1=self.request.user)
