# File: crm/schema.py
import graphene
from graphene_django import DjangoObjectType
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Customer, Product, Order
import datetime
import re
from .filters import CustomerFilter, ProductFilter, OrderFilter
from graphene_django.filter import DjangoFilterConnectionField

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        interfaces = (graphene.relay.Node,)
        fields = (
            'customer_id', 
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'created_at',
        )
        
# Define ProductType for GraphQL queries and mutations
class ProductType(DjangoObjectType):
    """
    GraphQL type for Product model.

    Exposes product_id, name, price, and quantity fields.
    Used in UpdateLowStockProducts mutation to return updated products.
    """
    class Meta:
        model = Product
        interfaces = (graphene.relay.Node,)
        fields = (
            'product_id',
            'name',
            'price',
            'quantity',
        )
        
class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        interfaces = (graphene.relay.Node,)
        fields = (
            'order_id',
            'customer',
            'products',
            'order_date',
            'total_amount',
        )

class CustomerInput(graphene.InputObjectType):
    first_name = graphene.String(required=True)
    last_name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone_number = graphene.String(required=True)
    
class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    quantity = graphene.Int(required=True, default=0)
    
class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime()

class CreateCustomer(graphene.Mutation):
    customer = graphene.Field(CustomerType)
    message = graphene.String()
    
    class Arguments:
        input = CustomerInput(required=True)
        
    def mutate(self, info, input):
        if input.phone_number:
            phone_pattern = r'^\s*(?:\+?(\d{1,3}))?[-. (]*(\d{3,4})[-. )]*(\d{3})[-. ]*(\d{3,4})(?: *x(\d+))?\s*$'
            if not re.match(phone_pattern, input.phone_number):
                raise ValidationError("Invalid Phone Number Format!")
        if Customer.objects.filter(email=input.email).exists():
            raise ValidationError("A user with a similar email already exists")
        customer = Customer(
            first_name=input.first_name,
            last_name=input.last_name,
            email=input.email, 
            phone_number=input.phone_number or "", 
        )
        customer.save()
        return CreateCustomer(
            customer=customer,
            message="Customer created successfully"
        )
        
class BulkCreateCustomers(graphene.Mutation):
    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)
    
    class Arguments:
        input = graphene.List(CustomerInput, required=True)
        
    def mutate(self, info, input):
        customers = []
        errors = []
        phone_pattern = r'^\s*(?:\+?(\d{1,3}))?[-. (]*(\d{3,4})[-. )]*(\d{3})[-. ]*(\d{3,4})(?: *x(\d+))?\s*$'
        with transaction.atomic():
            for item in input:
                try:
                    if item.phone_number and not re.match(phone_pattern, item.phone_number):
                        errors.append(f"Invalid Phone Number Format for {item.first_name}: {item.phone_number}")
                        continue
                    if Customer.objects.filter(email=item.email).exists():
                        errors.append(f"Email already exists: {item.email}")
                        continue
                    customer = Customer(
                        first_name=item.first_name, 
                        last_name=item.last_name,
                        phone_number=item.phone_number,
                        email=item.email,
                    )
                    customer.save()
                    customers.append(customer)
                except Exception as e:
                    errors.append(f"Error for {item.first_name}: {str(e)}")
            if errors:
                raise ValidationError(errors)
            return BulkCreateCustomers(
                customers=customers,
                errors=errors
            )

class CreateProduct(graphene.Mutation):
    product = graphene.Field(ProductType)
    message = graphene.String()
    
    class Arguments:
        input = ProductInput(required=True)
        
    def mutate(self, info, input):
        if input.price < 0:
            raise ValidationError("Price cannot be negative")
        if input.quantity < 0:
            raise ValidationError("Quantity cannot be negative")
        product = Product(
            name=input.name,
            price=input.price,
            quantity=input.quantity
        )
        product.save()
        return CreateProduct(
            product=product,
            message="Product created successfully"
        )
        
class CreateOrder(graphene.Mutation):
    order = graphene.Field(OrderType)
    
    class Arguments:
        input = OrderInput(required=True)
        
    def mutate(self, info, input):
        try:
            customer = Customer.objects.get(customer_id=input.customer_id)
        except Customer.DoesNotExist:
            raise ValidationError("Customer does not exist")
        if not input.product_ids:
            raise ValidationError("At least one product is required")
        products = Product.objects.filter(product_id__in=input.product_ids)
        if len(products) != len(input.product_ids):
            raise ValidationError("One or more product IDs are invalid")
        total_amount = sum(product.price for product in products)
        order = Order(
            customer=customer,
            total_amount=total_amount,
            order_date=input.order_date or datetime.datetime.now()
        )
        order.save()
        order.products.set(products)
        return CreateOrder(order=order)

class UpdateLowStockProducts(graphene.Mutation):
    """
    GraphQL mutation to update low-stock products.

    Requirements:
    - Query products with quantity < 10 (stock).
    - Increment quantity by 10 for each product.
    - Return a list of updated products, a success boolean, and a message.
    - Used by cron job in crm/cron.py to restock products every 12 hours.
    """
    class Arguments:
        pass  # No input arguments required

    products = graphene.List(ProductType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info):
        """
        Execute the mutation to update low-stock products.

        Queries Product model for items with quantity < 10, increments quantity by 10,
        and returns the updated products with a success message.
        """
        try:
            with transaction.atomic():
                # Query products with stock (quantity) < 10
                low_stock_products = Product.objects.filter(quantity__lt=10)
                updated_products = []
                # Restock each product by adding 10 to quantity
                for product in low_stock_products:
                    product.quantity += 10
                    product.save()
                    updated_products.append(product)
                # Return updated products and success message
                return UpdateLowStockProducts(
                    products=updated_products,
                    success=True,
                    message=f"Updated {len(updated_products)} low-stock products"
                )
        except Exception as e:
            # Handle errors and return failure response
            return UpdateLowStockProducts(
                products=[],
                success=False,
                message=f"Failed to update low-stock products: {str(e)}"
            )

class Query(graphene.ObjectType):
    hello = graphene.String()
    all_customers = DjangoFilterConnectionField(
        CustomerType, filterset_class=CustomerFilter
    )
    all_products = DjangoFilterConnectionField(
        ProductType, filterset_class=ProductFilter
    )
    all_orders = DjangoFilterConnectionField(
        OrderType, filterset_class=OrderFilter
    )
    
    def resolve_hello(self, info):
        return "Hello, GraphQL"
    
    def resolve_all_customers(self, info, **kwargs):
        qs = Customer.objects.all()
        if 'order_by' in kwargs:
            qs = qs.order_by(kwargs['order_by'])
        return qs
    
    def resolve_all_products(self, info, **kwargs):
        qs = Product.objects.all()
        if 'order_by' in kwargs:
            qs = qs.order_by(kwargs['order_by'])
        return qs
    
    def resolve_all_orders(self, info, **kwargs):
        qs = Order.objects.all()
        if 'order_by' in kwargs:
            qs = qs.order_by(kwargs['order_by'])
        return qs 

class Mutation(graphene.ObjectType):
    """
    Root mutation type for GraphQL schema.

    Includes UpdateLowStockProducts mutation for cron job to restock low-stock products.
    """
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
    update_low_stock_products = UpdateLowStockProducts.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

