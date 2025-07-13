from django.db import models
import datetime
from django.utils import timezone


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)  
    email = models.EmailField(unique=True)   
    phone_number = models.CharField(max_length=20, blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)  

    def __str__(self):
        return self.first_name + self.last_name  

class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=250)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=0)
    
    def __str__(self) -> str:
        return self.name
class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    products = models.ManyToManyField(to=Product)
    customer = models.ForeignKey(to = Customer, on_delete=models.CASCADE, related_name='order')
    order_date = models.DateTimeField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self): # String representation
        return f"Order {self.order_id} by {self.customer.last_name}"


    