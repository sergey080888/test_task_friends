from django.contrib.auth.models import AbstractUser
from django.db import models

OUTGOING_REQUEST = -1
FRIEND = 0
INCOMING_REQUEST = 1

STATUS_STR = {
    OUTGOING_REQUEST: "Вы подали заявку на дружбу.",
    FRIEND: "Вы друзья.",
    INCOMING_REQUEST: "Пользователь отправил Вам заявку в друзья.",
}


class Friendship(models.Model):
    """Заявка в друзья"""
    STATUS_CHOICES = {
        (OUTGOING_REQUEST, "Исходящая заявка"),
        (FRIEND, "Друзья"),
        (INCOMING_REQUEST, "Входящая заявка")
    }

    friend1 = models.ForeignKey("User", on_delete=models.CASCADE, related_name='friend1')
    friend2 = models.ForeignKey("User", on_delete=models.CASCADE, related_name='friend2')
    status = models.IntegerField("Статус заявки в друзья", choices=STATUS_CHOICES)
    send_date = models.DateTimeField("Дата и время отправки/принятия заявки", auto_now=True)

    class Meta:
        verbose_name = "Дружба"
        verbose_name_plural = "Дружба"
        unique_together = ('friend1', 'friend2', 'status')

    def __str__(self):
        return "%s - %s: %s" % (self.friend1.username, self.friend2.username, self.status)

    def accept_friendship(self):
        """Принять заявку в друзья"""
        Friendship.objects.filter(friend1__in=[self.friend1, self.friend2],
                                  friend2__in=[self.friend2, self.friend1]).update(status=FRIEND)
        return Friendship.objects.get(friend1=self.friend1, friend2=self.friend2, status=FRIEND)

    def reject_friendship(self):
        """Отклонить заявку в друзья"""
        Friendship.objects.filter(friend1__in=[self.friend1, self.friend2],
                                  friend2__in=[self.friend2, self.friend1]).delete()


class User(AbstractUser):
    """Пользователь"""
    first_name = None
    last_name = None
    EMAIL_FIELD = None

    def add_request_friendship(self, user):
        """Отправить заявку в друзья"""
        if Friendship.objects.filter(friend1=self, friend2=user, status=FRIEND):
            return Friendship.objects.get(friend1=self, friend2=user, status=FRIEND), 208
        if Friendship.objects.filter(friend1=self, friend2=user, status=OUTGOING_REQUEST):
            return Friendship.objects.get(friend1=self, friend2=user, status=OUTGOING_REQUEST), 208
        if Friendship.objects.filter(friend1=self, friend2=user, status=INCOMING_REQUEST):
            Friendship.objects.filter(friend1__in=[self, user], friend2__in=[user, self]).update(status=FRIEND)
            return Friendship.objects.get(friend1=self, friend2=user, status=FRIEND), 200
        r = Friendship.objects.create(friend1=self, friend2=user, status=OUTGOING_REQUEST)
        Friendship.objects.create(friend1=user, friend2=self, status=INCOMING_REQUEST)
        return r, 201

    def delete_friend(self, user):
        """Удалить из друзей"""
        friendships = Friendship.objects.filter(friend1__in=[self, user], friend2__in=[user, self], status=FRIEND)
        if friendships:
            friendships.delete()

    def get_users_friends(self, is_friend=FRIEND):
        """Получить список друзей или список пользователей, которые отправили/получили заявки от пользователя"""
        friends_id = Friendship.objects.filter(friend1=self, status=is_friend).values_list("friend2__id", flat=True)
        return User.objects.filter(id__in=friends_id)

    def get_friendship_request(self, in_out):
        """Получить список заявок в друзья (полученных/отправленных/принятых)"""
        return Friendship.objects.filter(friend1=self, status=in_out)

    def get_friendship_status(self, user):
        """Получить статус дружбы с пользователем"""
        qs = Friendship.objects.filter(friend1=self, friend2=user)
        if qs.exists():
            return qs[0].status
