from rest_framework import serializers

from .models import User, Friendship


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "password"]

    def create(self, validated_data):
        return User.objects.create_user(username=validated_data['username'], password=validated_data['password'])


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "username"]


class FriendshipStatusSerializer(serializers.Serializer):
    friendship_status = serializers.CharField(read_only=True)


class FriendshipSerializer(serializers.ModelSerializer):

    class Meta:
        model = Friendship
        fields = ["id", "friend2", "status", "send_date"]
        read_only_fields = ["status"]
