from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField

class User(AbstractUser):
    USER_TYPES = (
        ('customer', 'Заказчик'),
        ('performer', 'Исполнитель'),
    )
    
    SERVICE_TYPES = (
        ('photo', 'Фотограф'),
        ('video', 'Видеограф'),
        ('music', 'Музыкант'),
        ('host', 'Ведущий'),
        ('dance', 'Шоу-программа'),
        ('restaurant', 'Ресторан'),
        ('makeup', 'Визожист'),
        ('registry', 'Регистрация брака'),
        ('star', 'Звезда Эстрады'),
        ('cottage', 'Коттеджы'),
        ('recreation_areas', 'Зоны отдыха'),
        ('aphishe', 'Концертные Афишы'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    phone_number = models.CharField(max_length=20, unique=True, null=True)
    is_phone_verified = models.BooleanField(default=False)
    city = models.CharField(max_length=100, blank=True)
    rating = models.FloatField(default=0)
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    
    # Поля для исполнителей
    company_name = models.CharField(max_length=100, blank=True, null=True)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES, blank=True, null=True)
    bio = models.TextField(blank=True)
    services = models.JSONField(default=list, blank=True, null=True, help_text="Список предоставляемых услуг")
    
    # Настройки уведомлений
    email_notifications = models.BooleanField(default=True)
    whatsapp_notifications = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def completed_orders_count(self):
        return self.orders_received.filter(status='completed').count()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

class Portfolio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolio')
    image = models.ImageField(upload_to='portfolio/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Фото портфолио'
        verbose_name_plural = 'Фотографии портфолио'
        ordering = ['-created_at']

class PortfolioPhoto(models.Model):
    image = models.ImageField(upload_to='portfolio/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Portfolio photo {self.id}"

class Tariff(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tariffs')
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Тариф'
        verbose_name_plural = 'Тарифы'
        ordering = ['price']

class BusyDate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    
    class Meta:
        unique_together = ['user', 'date']

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('in_progress', 'В работе'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен')
    ]

    EVENT_TYPES = [
        ('wedding', 'Свадьба'),
        ('birthday', 'День рождения'),
        ('corporate', 'Корпоратив'),
        ('other', 'Другое')
    ]

    ORDER_TYPES = [
        ('request', 'Заявка'),  # Заявка от заказчика
        ('booking', 'Бронирование')  # Бронирование у исполнителя
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders_created')
    performer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders_received')
    title = models.CharField(max_length=200)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    event_date = models.DateField()
    city = models.CharField(max_length=100)
    venue = models.CharField(max_length=200, blank=True)
    guest_count = models.IntegerField(validators=[MinValueValidator(1)])
    description = models.TextField()
    budget_min = models.DecimalField(max_digits=10, decimal_places=2)
    budget_max = models.DecimalField(max_digits=10, decimal_places=2)
    services = models.JSONField()  # Хранит список выбранных услуг
    selected_performers = models.JSONField(default=dict, blank=True, help_text="Выбранные исполнители по услугам: {service_type: performer_id}")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tariff = models.ForeignKey(Tariff, on_delete=models.SET_NULL, null=True, related_name='orders')
    details = models.TextField(blank=True)
    order_type = models.CharField(max_length=20, choices=ORDER_TYPES, default='request')

    def __str__(self):
        return f"{self.title} - {self.customer.get_full_name()}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

class Review(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='reviews')
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
    rating = models.IntegerField(validators=[MinValueValidator(1)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.from_user.get_full_name()} for {self.to_user.get_full_name()}"

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

class Message(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='messages')
    from_user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='sent_messages')
    to_user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    performer = models.ForeignKey('User', on_delete=models.CASCADE, null=True, blank=True, related_name='chat_messages_performer')
    
    class Meta:
        ordering = ['created_at']
        
    def __str__(self):
        return f'Message from {self.from_user} to {self.to_user} in order {self.order.id}'

class OrderResponse(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='responses')
    performer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='order_responses')
    message = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Отклик на заказ'
        verbose_name_plural = 'Отклики на заказы'
        ordering = ['-created_at']
        unique_together = ['order', 'performer']  # Один исполнитель - один отклик на заказ
        
    def __str__(self):
        return f'Response from {self.performer.get_full_name()} to order {self.order.id}'

class OTP(models.Model):
    phone_number = models.CharField(max_length=15)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)

    def is_valid(self):
        # OTP is valid for 5 minutes and max 3 attempts
        return (
            not self.is_verified and
            self.attempts < 3 and
            (timezone.now() - self.created_at).total_seconds() < 300
        )

class BookingProposal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает ответа'),
        ('accepted', 'Принято'),
        ('rejected', 'Отклонено'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='booking_proposals')
    performer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='booking_proposals')
    tariff = models.ForeignKey(Tariff, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['order', 'performer', 'date']
