from __future__ import annotations
import json
import os
import csv
import json

from abc import ABC, abstractmethod

import os
script_dir = os.path.dirname(os.path.abspath(__file__))
file_name = os.path.join(script_dir, "inventory.json")

class Supplier:
    """Represents a supplier. Exists independently of any Product (association)."""

    def __init__(self, supplier_id: str, name: str, contact_email: str) -> None:
        self.__supplier_id: str = str(supplier_id)
        self.__name: str = name
        self.__contact_email: str = contact_email

    def get_id(self) -> str:
        return self.__supplier_id

    def get_name(self) -> str:
        return self.__name

    def get_contact_email(self) -> str:
        return self.__contact_email

    def display_information(self) -> None:
        print(f"Supplier ID: {self.__supplier_id} | "
              f"Name: {self.__name} | "
              f"Email: {self.__contact_email}")

class CanBeShipped(ABC):
    """Interface for products that can be shipped."""

    @abstractmethod
    def calculate_shipping_cost(self) -> float:
        pass

class Product(ABC):
    """Represents a single product in the inventory."""

    @abstractmethod
    def get_fulfilment_info(self) -> str:
        pass
    
    def __init__(self, product_id: str, name: str, price: float, quantity: int, supplier: Supplier) -> None:
        """Constructor - initialize a product with its attributes."""
        if price <= 0:
            raise ValueError("Price must be greater than zero.")
        if quantity < 0:
            raise ValueError("Stock quantity cannot be negative.")
        self.__product_id: str = str(product_id)
        self.__name: str = name
        self.__price: float = price
        self.__quantity: int = quantity
        self.__supplier: Supplier = supplier
    
    def update_stock(self, new_quantity: int) -> None:
        """Update the stock quantity for this product."""
        if new_quantity < 0:
            raise ValueError("Stock quantity cannot be negative.")
        self.__quantity = new_quantity

    def display_single_line(self) -> None:
        """Display product in single-line format (for inventory list)."""
        print(f"ID: P{self.__product_id} | Name: {self.__name} | Price: ${self.__price:.2f} | Stock: {self.__quantity}")

    def get_info_string(self) -> str:
        return (f"ID: P{self.get_id():<6} | "
                f"Name: {self.get_name():<15} | "
                f"Price: ${self.get_price():>8.2f} | "
                f"Stock: {self.get_quantity():>3}")

    def display_information(self) -> None:
        print(self.get_info_string())
    
    # Getters (to read private attributes from outside the class)
    def get_id(self) -> str:
        return self.__product_id
    
    def get_name(self) -> str:
        return self.__name
    
    def get_price(self) -> float:
        return self.__price
    
    def get_quantity(self) -> int:
        return self.__quantity

    def get_supplier(self) -> Supplier:
        return self.__supplier

class DigitalProduct(Product):
    """A product delivered as a download."""

    def __init__(self, product_id: str, name: str, price: float, quantity: int, download_size: float, supplier: Supplier) -> None:
        super().__init__(product_id, name, price, quantity, supplier)
        self.__download_size: float = download_size

    def get_download_size(self) -> float:
        return self.__download_size

    def get_fulfilment_info(self) -> str:
        return "Delivered digitally. Download size: " + str(self.__download_size) + " MB"

    def get_info_string(self) -> str:
        return (super().get_info_string() +
                f" | Type: {'Digital':<8} | Download size: {self.get_download_size():>5} MB")

class PhysicalProduct(Product, CanBeShipped):
    """A product that is shipped to the customer."""

    def __init__(self, product_id: str, name: str, price: float, quantity: int, weight: float, supplier: Supplier) -> None:
        super().__init__(product_id, name, price, quantity, supplier)
        self.__weight: float = weight

    def get_weight(self) -> float:
        return self.__weight

    def get_fulfilment_info(self) -> str:
        return "Ships to the customer's address."

    def get_info_string(self) -> str:
        return (super().get_info_string() +
                f" | Type: {'Physical':<8} | Weight: {self.get_weight():>5} kg")

    def calculate_shipping_cost(self) -> float:
        """Shipping cost: base fee plus rate per kg."""
        return 5.00 + self.get_weight() * 2.00

class SubscriptionProduct(Product):
    """A product delivered as a recurring subscription (Optional Task 8)."""

    def __init__(self, product_id: str, name: str, price: float, quantity: int, duration_months: int, supplier: Supplier) -> None:
        super().__init__(product_id, name, price, quantity, supplier)
        self.__duration_months: int = duration_months

    def get_duration_months(self) -> int:
        return self.__duration_months

    def get_fulfilment_info(self) -> str:
        return f"Subscription service. Duration: {self.__duration_months} months"

    def get_info_string(self) -> str:
        return (super().get_info_string() +
                f" | Type: {'Sub':<8} | Duration: {self.get_duration_months():>3} mos")

class ProductFactory:
    """Centralises product creation. The rest of the program only needs Product and this class."""

    @staticmethod
    def create(product_type: str, product_id: str, name: str, price: float,
               stock_quantity: int, supplier: Supplier, extra: float = 0) -> Product:
        """extra is the type-specific value: weight (physical), download size (digital)
        or duration in months (subscription)."""
        if product_type == "physical":
            return PhysicalProduct(product_id, name, price, stock_quantity, extra, supplier)
        elif product_type == "digital":
            return DigitalProduct(product_id, name, price, stock_quantity, extra, supplier)
        elif product_type == "subscription":
            return SubscriptionProduct(product_id, name, price, stock_quantity, int(extra), supplier)
        else:
            raise ValueError(f"Unknown product type: {product_type}")

class Inventory:
    """Manages a collection of products in the inventory (aggregation)."""

    def __init__(self) -> None:
        """Constructor - initialize an empty product list."""
        self.__products: list[Product] = []

    def add_product(self, product: Product) -> None:
        """Add an existing Product object (Physical, Digital or Subscription)."""
        self.__products.append(product)

    def find_product(self, product_id: str) -> Product | None:
        """Return the product with this exact ID, or None if not found."""
        for product in self.__products:
            if product.get_id() == str(product_id):
                return product
        return None

    def remove_product(self, product_id: str) -> bool:
        """Remove the matching Product reference. The Product itself is not destroyed.
        Returns True if a product was removed."""
        product = self.find_product(product_id)
        if product is None:
            return False
        self.__products.remove(product)
        return True

    def get_total_stock(self) -> int:
        """Return total quantity of all products in inventory."""
        return sum(product.get_quantity() for product in self.__products)

    def search_product_by_term(self, search_term: str) -> list[Product]:
        """Search for products by ID or name. Returns list of matching products."""
        found_items = []
        clean_term = search_term.lstrip("Pp").strip()
        
        for product in self.__products:
            # Match by ID or name (case-insensitive)
            if str(product.get_id()) == clean_term or clean_term.lower() in product.get_name().lower():
                found_items.append(product)
        
        return found_items

    def update_product_stock(self, search_term: str, new_quantity: int) -> bool:
        """Update stock for a product by ID or name. Returns True if successful."""
        clean_term = search_term.lstrip("Pp").strip()
        
        for product in self.__products:
            # Match by ID or name (case-insensitive)
            if str(product.get_id()) == clean_term or clean_term.lower() in product.get_name().lower():
                product.update_stock(new_quantity)
                return True
        
        return False
    
    def display_all(self) -> None:
        for product in self.__products:   # use your actual list name
            product.display_information()
    
    def get_products(self) -> list[Product]:
        """Return the list of all products."""
        return self.__products

class OrderLine:
    """One product and quantity inside an Order.
    Only an Order should create it (composition: it belongs to exactly one Order)."""

    def __init__(self, product: Product, quantity: int) -> None:
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")
        self.__product: Product = product      
        self.__quantity: int = quantity

    def get_product(self) -> Product:
        return self.__product

    def get_quantity(self) -> int:
        return self.__quantity

    def calculate_subtotal(self) -> float:
        return self.__product.get_price() * self.__quantity

    def display_information(self) -> None:
        print(f"{self.__product.get_name():<15} | "
              f"Qty: {self.__quantity:>3} | "
              f"Unit: ${self.__product.get_price():>8.2f} | "
              f"Subtotal: ${self.calculate_subtotal():>8.2f}")

class DiscountStrategy(ABC):
    """Base class for all discount strategies. Order only knows about this."""

    @abstractmethod
    def apply(self, total: float) -> float:
        pass


class NoDiscount(DiscountStrategy):
    """Returns the total unchanged."""

    def apply(self, total: float) -> float:
        return total


class PercentageDiscount(DiscountStrategy):
    """Takes a percentage off the total, e.g. PercentageDiscount(10) takes 10% off."""

    def __init__(self, percentage: float) -> None:
        self.__percentage: float = percentage

    def apply(self, total: float) -> float:
        return total * (1 - self.__percentage / 100)


class BulkDiscount(DiscountStrategy):
    """Takes a fixed amount off any total at or above the threshold."""

    def __init__(self, threshold: float, amount: float) -> None:
        self.__threshold: float = threshold
        self.__amount: float = amount

    def apply(self, total: float) -> float:
        if total >= self.__threshold:
            return total - self.__amount
        return total

class StudentDiscount(DiscountStrategy):
    """5% off for students (the business request from Section 2.1)."""

    def apply(self, total: float) -> float:
        return total * 0.95

class Order:
    """A customer order. Creates and manages its own OrderLine objects (composition)."""

    def __init__(self, order_id: str, discount: DiscountStrategy | None = None) -> None:
        self.__order_id: str = str(order_id)
        self.__order_lines: list[OrderLine] = []
        self.__discount: DiscountStrategy = discount if discount is not None else NoDiscount()

    def get_order_id(self) -> str:
        return self.__order_id

    def set_discount(self, discount: DiscountStrategy) -> None:
        """Swap the discount strategy, e.g. when a customer shows a student card."""
        self.__discount = discount

    def add_order_line(self, product: Product, quantity: int) -> None:
        """Takes a Product and quantity, and creates the OrderLine internally."""
        order_line = OrderLine(product, quantity)
        self.__order_lines.append(order_line)

    def remove_order_line(self, product_id: str) -> bool:
        """Remove the line for this product from the order. Returns True if removed."""
        for order_line in self.__order_lines:
            if order_line.get_product().get_id() == str(product_id):
                self.__order_lines.remove(order_line)
                return True
        return False

    def get_order_lines(self) -> list[OrderLine]:
        """Return a copy, so outside code cannot add or take lines behind the Order's back."""
        return list(self.__order_lines)

    def calculate_total(self) -> float:
        total = sum(order_line.calculate_subtotal() for order_line in self.__order_lines)
        return self.__discount.apply(total)

    def display_information(self) -> None:
        print(f"Order {self.__order_id}")
        for order_line in self.__order_lines:
            order_line.display_information()
        print(f"Total: ${self.calculate_total():.2f}")

def get_positive_float(prompt: str) -> float:
    """Keep asking until the user enters a number greater than zero."""
    while True:
        try:
            value = float(input(prompt))
            if value <= 0:
                print("Please enter a number greater than zero.")
                continue
            return value
        except ValueError:
            print("Please enter a valid number, e.g. 12.50")

def load_products(path: str, inventory: Inventory, supplier: Supplier) -> None:
    """Load products from a CSV file. Bad rows are reported and skipped."""
    loaded = 0
    try:
        file = open(path, newline="")
    except FileNotFoundError:
        print(f"Products file not found: {path}")
    else:
        with file:
            reader = csv.reader(file)
            next(reader, None)  # skip the header row
            for row in reader:
                try:
                    product_type, product_id, name, price, stock_quantity = row
                    product = ProductFactory.create(product_type, product_id, name,
                                                    float(price), int(stock_quantity), supplier)
                    inventory.add_product(product)
                    loaded += 1
                except ValueError as error:
                    print(f"Skipping row {row}: {error}")
        print(f"{loaded} products loaded.")
    finally:
        print("Load attempt finished.")

class MainProgram:
    """Displays the menu, gets user input, calls the appropriate Inventory methods."""

    def __init__(self, file_name: str) -> None:
        self.file_name: str = file_name
        self.inventory: Inventory = Inventory()
        self.file_handler: FileHandling = FileHandling()
        self.file_handler.load_inventory(file_name, self.inventory)

    def display_welcome(self) -> None:
        print("\n========================================")
        print("\nINVENTORY MANAGER SYSTEM")
        print("\n========================================")

        if self.inventory.get_products():
            print("\ninventory.json found.")
            print("Inventory loaded successfully.\n")
        else:
            print("\ninventory.json not found.")
            print("Starting with an empty inventory.\n")

    def display_menu(self) -> None:
        print("\n----------- MENU -----------")
        print("1. Display All Products")
        print("2. Add Product")
        print("3. Update Stock")
        print("4. Search Product")
        print("5. Save Inventory")
        print("6. Calculate Shipping Cost")
        print("7. Exit")

    def handle_display_all(self) -> None:
        print("\nCurrent Inventory")
        print("------------------------------------------------")
        self.inventory.display_all()
        print("------------------------------------------------")

    def handle_add_product(self) -> None:
        print("\nAdd New Product")

        # INPUT 1: Get and validate Product ID - must be numbers only
        while True:
            try:
                raw_id = input("Product ID: ").strip()
                product_id = raw_id.lstrip("Pp")

                if not product_id:
                    print("Invalid ID. Please enter a valid product ID.")
                    continue

                if not product_id.isdigit():
                    print("Invalid ID. ID must contain only numbers (0-9)")
                    continue

                # CHECK IF ID ALREADY EXISTS
                existing_products = self.inventory.search_product_by_term(product_id)
                if existing_products:
                    product = existing_products[0]
                    print(f"\nP{product_id} already added to cart.")
                    print(f"Name: {product.get_name()} | Price: ${product.get_price():.2f} | Current Stock: {product.get_quantity()}")

                    # VALIDATE YES/NO ONLY
                    while True:
                        response = input("Do you want to continue adding more? (yes/no): ").strip().lower()
                        if response in ["yes", "no"]:
                            break
                        print("Invalid input. Please enter 'yes' or 'no'.")

                    if response == "no":
                        print("Cancelled.")
                        return

                break
            except ValueError:
                print("Invalid input. Please enter a valid product ID.")

        # INPUT 2: Get Product Name
        product_name = input("Product Name: ").strip()

        # INPUT 3: Get and validate Price - must be a number, not negative
        price = get_positive_float("Price: ")

        # INPUT 4: Choose product type
        while True:
            print("\nProduct type:")
            print("1. Physical")
            print("2. Digital")
            print("3. Subscription")
            product_type = input("Choose type (1, 2, or 3): ").strip()
            if product_type in ["1", "2", "3"]:
                break
            print("Invalid choice. Enter 1, 2, or 3.")

        # INPUT 5: Extra field depends on type
        if product_type == "1":
            while True:
                try:
                    extra = float(input("Weight (kg): ").strip())
                    if extra <= 0:
                        print("Weight must be greater than 0.")
                        continue
                    break
                except ValueError:
                    print("Invalid input. Please enter a number.")
        elif product_type == "2":
            while True:
                try:
                    extra = float(input("Download size (MB): ").strip())
                    if extra <= 0:
                        print("Download size must be greater than 0.")
                        continue
                    break
                except ValueError:
                    print("Invalid input. Please enter a number.")
        else:
            while True:
                try:
                    extra = int(input("Duration (months): ").strip()) 
                    if extra <= 0:
                        print("Duration must be greater than 0.")
                        continue
                    break
                except ValueError:
                    print("Invalid input. Please enter an integer number.")

        # INPUT 5b: Supplier (created first, then handed to the product)
        supplier = self.get_supplier_input()

        # INPUT 6: Get and validate Stock Quantity - must be number, check 500 limit
        while True:
            qty_input = input("Stock Quantity: ").strip()

            if qty_input.lower() == "quit":
                print("Cancelled.")
                return

            if not qty_input.isdigit():
                print("Invalid input. Quantity must be a positive number.")
                continue

            valid_quantity = int(qty_input)

            if valid_quantity <= 0:
                print("Quantity must be greater than 0.")
                continue

            if valid_quantity > 500:
                print(f"Quantity cannot exceed 500. You entered: {valid_quantity}")
                continue

            current_total = self.inventory.get_total_stock()
            new_total = current_total + valid_quantity

            if new_total > 500:
                print(f"Cannot add {valid_quantity} units.")
                print(f"Current stock: {current_total} | Max allowed: 500 | Available space: {500 - current_total}")
                continue

            # Ask the factory to create the right product type
            type_names = {"1": "physical", "2": "digital", "3": "subscription"}
            product = ProductFactory.create(type_names[product_type], product_id, product_name, price, valid_quantity, supplier, extra)
            self.inventory.add_product(product)
            print(f"Product P{product_id} added successfully.")
            break

    def handle_update_stock(self) -> None:
        print("\nUpdate Stock")
        search_term = input("Enter Product ID or Name: ").strip()

        found_items = self.inventory.search_product_by_term(search_term)

        if found_items:
            product = found_items[0]
            print("\nProduct Found:")
            product.display_information()

            while True:
                raw_qty = input("\nNew Stock Quantity: ").strip()

                if raw_qty.lower() == "quit":
                    print("Cancelled.")
                    break

                if not raw_qty.isdigit():
                    print("Invalid input. Please enter a positive number.")
                    continue

                valid_quantity = int(raw_qty)

                if valid_quantity <= 0:
                    print("Quantity must be greater than 0.")
                    continue

                current_total = self.inventory.get_total_stock()
                old_quantity = product.get_quantity()
                new_total = current_total - old_quantity + valid_quantity

                if new_total <= 500:
                    self.inventory.update_product_stock(search_term, valid_quantity)
                    print("Stock updated successfully!")
                    break
                else:
                    print(f"Current stock (excl. this product): {current_total - old_quantity} | New quantity: {valid_quantity} | Total would be: {new_total} | Limit: 500")

        else:
            print("\nProduct not found.")

    def handle_search_product(self) -> None:
        search_term = input("Search Product ID: ").strip()
        found_items = self.inventory.search_product_by_term(search_term)

        if found_items:
            print("\nProduct Found")
            print("\n------------------------------------------------")
            for product in found_items:
                product.display_information()
            print("------------------------------------------------\n")
        else:
            print("Product not found.\n")

    def handle_save_inventory(self) -> None:
        self.file_handler.save_inventory(self.file_name, self.inventory)
        print("Saving inventory...")
        print(f"Inventory saved successfully to {self.file_name}\n")

    def handle_calculate_shipping(self) -> None:
        search_term = input("Enter Physical Product ID or Name to calculate shipping: ").strip()
        found_items = self.inventory.search_product_by_term(search_term)

        if found_items:
            product = found_items[0]
            if isinstance(product, CanBeShipped):
                cost = product.calculate_shipping_cost()
                print(f"\nShipping cost for {product.get_name()}: ${cost:.2f}")
            else:
                print(f"\n{product.get_name()} is a digital product and cannot be shipped.")
        else:
            print("\nProduct not found.")

    def get_supplier_input(self) -> Supplier:
        """Reuse an existing supplier by ID, or create a new one."""
        while True:
            supplier_id = input("Supplier ID: ").strip()
            if supplier_id:
                break
            print("Supplier ID cannot be empty.")

        for product in self.inventory.get_products():
            existing = product.get_supplier()
            if existing.get_id() == supplier_id:
                print("Existing supplier found:")
                existing.display_information()
                return existing

        name = input("Supplier Name: ").strip()
        email = input("Supplier Email: ").strip()
        return Supplier(supplier_id, name, email)

    def run(self) -> None:
        self.display_welcome()

        while True:
            self.display_menu()
            choice = input("\nEnter option: ").strip()

            if choice == "1":
                self.handle_display_all()
            elif choice == "2":
                self.handle_add_product()
            elif choice == "3":
                self.handle_update_stock()
            elif choice == "4":
                self.handle_search_product()
            elif choice == "5":
                self.handle_save_inventory()
            elif choice == "6":
                self.handle_calculate_shipping()
            elif choice == "7":
                self.handle_save_inventory()
                print("Thank you for using Inventory Management System.")
                print("Program terminated.")
                break
            else:
                print("Invalid choice. Please select from 1 to 7.") 

class FileHandling:
    """Loads inventory data from JSON and saves inventory data to JSON."""

    def save_inventory(self, filename: str, inventory: Inventory) -> None:
        data = []
        for product in inventory.get_products():
            item = {
                "product_id": product.get_id(),
                "name": product.get_name(),
                "price": product.get_price(),
                "quantity": product.get_quantity(),
            }
            supplier = product.get_supplier()
            item["supplier"] = {
                "supplier_id": supplier.get_id(),
                "name": supplier.get_name(),
                "contact_email": supplier.get_contact_email(),
            }
            if isinstance(product, PhysicalProduct):
                item["type"] = "physical"
                item["weight"] = product.get_weight()
            elif isinstance(product, DigitalProduct):
                item["type"] = "digital"
                item["download_size"] = product.get_download_size()
            elif isinstance(product, SubscriptionProduct):  # <-- ADD THIS BLOCK
                item["type"] = "subscription"
                item["duration_months"] = product.get_duration_months()
            data.append(item)

        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

    def load_inventory(self, filename: str, inventory: Inventory) -> None:
        try:
            with open(filename, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            return

        suppliers: dict[str, Supplier] = {}

        for item in data:
            supplier = self._load_supplier(item.get("supplier"), suppliers)
            prod_type = item.get("type", "physical")
            extra_keys = {"physical": "weight", "digital": "download_size", "subscription": "duration_months"}
            extra = item.get(extra_keys.get(prod_type, ""), 0)
            product = ProductFactory.create(prod_type, item.get("product_id", item.get("id")), item["name"], item["price"], item["quantity"], supplier, extra)
            inventory.add_product(product)

    def _load_supplier(self, supplier_data: dict | None,
                       suppliers: dict[str, Supplier]) -> Supplier:
        """Reuse one Supplier object per supplier_id."""
        if supplier_data is None:   # old JSON without supplier info
            supplier_data = {"supplier_id": "S000",
                             "name": "Unknown Supplier",
                             "contact_email": "unknown@example.com"}
        supplier_id = supplier_data["supplier_id"]
        if supplier_id not in suppliers:
            suppliers[supplier_id] = Supplier(supplier_id,
                                              supplier_data["name"],
                                              supplier_data["contact_email"])
        return suppliers[supplier_id]

#---- THE MENU SHIT -----
if __name__ == "__main__":
    program = MainProgram(file_name)
    program.run()

#Eugene Repo URL: https://github.com/Eugene2603188/Lab9

#if wanna test, run "inventory_test.py"

