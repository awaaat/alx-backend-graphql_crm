import django_filters
from django_filters import CharFilter, NumberFilter, FilterSet, DateTimeFilter
from .models import Product, Order, Customer

class CustomerFilter(FilterSet):
    first_name = CharFilter(lookup_expr='icontains')
    last_name = CharFilter(lookup_expr='icontains')
    email = CharFilter(lookup_expr='icontains')
    created_at_gte = DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_lte = DateTimeFilter(field_name='created_at', lookup_expr='lte')
    phone_pattern = CharFilter(method='filter_phone')
    
    def filter_phone(self, queryset, name, value):
        return queryset.filter(phone__startswith=value)
    
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 
                'email', 'created_at_gte', 
                'created_at_lte', 'phone_pattern']

class ProductFilter(FilterSet):
    name = CharFilter(lookup_expr='icontains')
    price_gte = NumberFilter(field_name='price', lookup_expr='gte')
    price_lte = NumberFilter(field_name='price', lookup_expr='gte')
    stock_gte = NumberFilter(field_name='quantity', lookup_expr='gte')
    stock_lte = NumberFilter(field_name='quantity', lookup_expr='lte')
    low_stock = NumberFilter(method='filter_low_stock')
    
    def filter_low_stock(self, queryset, name, value):
        return queryset.filter(stock__lt = value)
    
    class Meta:
        model = Product
        fields=  ['name', 'price_gte', 'price_lte', 
                'stock_gte', 'stock_lte', 'low_stock']
class OrderFilter(FilterSet):
    total_amount_gte = NumberFilter(field_name='total_amount', lookup_expr='gte')
    total_amount_lte = NumberFilter(field_name='total_amount', lookup_expr='lte')
    order_date_gte = DateTimeFilter(field_name='order_date', lookup_expr='gte')
    order_date_lte = DateTimeFilter(field_name='order_date', lookup_expr='lte')
    customer_name = CharFilter(field_name='customer__last_name', lookup_expr='icontains')
    product_name = CharFilter(field_name='product__product_id', lookup_expr='exact')
    
    class Meta:
        model = Order
        fields = ['total_amount_gte', 'total_amount_lte', 
                'order_date_gte', 'order_date_lte',
                'customer_name', 'product_name']
        