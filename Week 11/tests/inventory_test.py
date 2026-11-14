from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # so this file can find inventory_manager.py

import ast
import contextlib
import inspect
import io
import tempfile
import unittest
from unittest.mock import patch

import inventory_manager
from inventory_manager import (
    BulkDiscount, CanBeShipped, DigitalProduct, DiscountStrategy, Inventory, NoDiscount,
    Order, OrderLine, PercentageDiscount, PhysicalProduct, Product, ProductFactory,
    StudentDiscount, SubscriptionProduct, Supplier, get_positive_float, load_products,
)
# =====================================================================
# LAB 8 CHECKS (print PASS/FAIL) - kept exactly as before
# =====================================================================
def check(label, condition):
    print(("PASS" if condition else "FAIL") + ": " + label)
    return condition

test_supplier = Supplier("S001", "TechSupply Co", "sales@techsupply.com")

# ----- TEST PRODUCT -----
print("----- TEST PRODUCT -----")
product_results = []

try:
    Product("999", "Test", 1.0, 1, test_supplier)
    product_results.append(check("Product cannot be instantiated", False))
except TypeError:
    product_results.append(check("Product cannot be instantiated", True))

try:
    PhysicalProduct("9", "Test", 1.0, 1, 2.0, test_supplier)
    product_results.append(check("PhysicalProduct can be instantiated", True))
except TypeError:
    product_results.append(check("PhysicalProduct can be instantiated", False))

try:
    DigitalProduct("8", "Test", 1.0, 1, 2.0, test_supplier)
    product_results.append(check("DigitalProduct can be instantiated", True))
except TypeError:
    product_results.append(check("DigitalProduct can be instantiated", False))

print(f"{sum(product_results)} of {len(product_results)} checks passed")
print()

# ----- TEST CANBESHIPPED() -----
print("----- TEST CANBESHIPPED() -----")
shipping_results = []

p_light = PhysicalProduct("9", "Test", 1.0, 1, 0.5, test_supplier)
p_heavy = PhysicalProduct("10", "Test", 1.0, 1, 2.0, test_supplier)
d_item = DigitalProduct("8", "Test", 1.0, 1, 2.0, test_supplier)

shipping_results.append(check("PhysicalProduct is a CanBeShipped", isinstance(p_light, CanBeShipped)))
shipping_results.append(check("DigitalProduct is not a CanBeShipped", not isinstance(d_item, CanBeShipped)))
shipping_results.append(check("Shipping cost for 0.5 kg is 6.0", p_light.calculate_shipping_cost() == 6.0))
shipping_results.append(check("Shipping cost for 2.0 kg is 9.0", p_heavy.calculate_shipping_cost() == 9.0))
shipping_results.append(check("Heavier item costs more to ship", p_heavy.calculate_shipping_cost() > p_light.calculate_shipping_cost()))

print(f"{sum(shipping_results)} of {len(shipping_results)} checks passed")

# ----- TEST FULFILMENT MESSAGES -----
print("\n----- TEST FULFILMENT MESSAGES -----")
fulfilment_results = []

p_msg = PhysicalProduct("9", "Test", 1.0, 1, 0.5, test_supplier).get_fulfilment_info()
d_msg = DigitalProduct("8", "Test", 1.0, 1, 2.0, test_supplier).get_fulfilment_info()

fulfilment_results.append(check("PhysicalProduct returns its own fulfilment message", p_msg == "Ships to the customer's address."))
fulfilment_results.append(check("DigitalProduct returns a fulfilment message", isinstance(d_msg, str) and d_msg != ""))
fulfilment_results.append(check("Fulfilment messages differ between subclasses", p_msg != d_msg))

# ----- TEST ASSOCIATION (SUPPLIER AND PRODUCT) -----
print("\n----- TEST ASSOCIATION (SUPPLIER AND PRODUCT) -----")
association_results = []

assoc_supplier = Supplier("S002", "Acme Parts", "info@acme.com")
assoc_physical = PhysicalProduct("11", "Test", 1.0, 1, 0.5, assoc_supplier)
assoc_digital = DigitalProduct("12", "Test", 1.0, 1, 2.0, assoc_supplier)

print("Supplier info via PhysicalProduct:")
assoc_physical.get_supplier().display_information()
print("Supplier info via DigitalProduct:")
assoc_digital.get_supplier().display_information()

association_results.append(check("PhysicalProduct stores a reference to its Supplier", assoc_physical.get_supplier() is assoc_supplier))
association_results.append(check("DigitalProduct stores a reference to its Supplier", assoc_digital.get_supplier() is assoc_supplier))
association_results.append(check("One Supplier object is shared by both products", assoc_physical.get_supplier() is assoc_digital.get_supplier()))
association_results.append(check("Supplier and Product are separate objects", assoc_supplier is not assoc_physical))

del assoc_supplier
print("\nAfter 'del assoc_supplier':")
association_results.append(check("Product can still display its supplier info", assoc_physical.get_supplier().get_name() == "Acme Parts"))
assoc_physical.get_supplier().display_information()
print(f"{sum(fulfilment_results)} of {len(fulfilment_results)} checks passed")

# ----- TEST AGGREGATION (INVENTORY AND PRODUCT) -----
print("\n----- TEST AGGREGATION (INVENTORY AND PRODUCT) -----")
aggregation_results = []

agg_supplier = Supplier("S003", "Delta Goods", "hello@delta.com")
agg_product = PhysicalProduct("20", "Test", 5.0, 2, 1.0, agg_supplier)   # created BEFORE any inventory

inventory_a = Inventory()
inventory_b = Inventory()

# Add to Inventory A
inventory_a.add_product(agg_product)
aggregation_results.append(check("Inventory A finds the product after adding", inventory_a.find_product("20") is agg_product))

# Remove from Inventory A
removed = inventory_a.remove_product("20")
aggregation_results.append(check("remove_product() reports success", removed is True))
aggregation_results.append(check("Inventory A no longer contains the product", inventory_a.find_product("20") is None))
aggregation_results.append(check("Removing a missing product returns False", inventory_a.remove_product("20") is False))

# Product still works after removal
print("Product after removal from Inventory A:")
agg_product.display_information()
aggregation_results.append(check("Product is still usable after removal", agg_product.get_name() == "Test" and agg_product.get_quantity() == 2))
aggregation_results.append(check("Product still knows its supplier", agg_product.get_supplier() is agg_supplier))

# Transfer to Inventory B
inventory_b.add_product(agg_product)
aggregation_results.append(check("Same Product object can be added to Inventory B", inventory_b.find_product("20") is agg_product))

# Empty Inventory B
inventory_b.remove_product("20")
aggregation_results.append(check("Inventory B is now empty", len(inventory_b.get_products()) == 0))
aggregation_results.append(check("Product still exists after its inventory is emptied", agg_product.get_name() == "Test"))

print(f"{sum(aggregation_results)} of {len(aggregation_results)} checks passed")

# ----- TEST COMPOSITION (ORDER AND ORDERLINE) -----
print("\n----- TEST COMPOSITION (ORDER AND ORDERLINE) -----")
composition_results = []

comp_supplier = Supplier("S004", "Echo Supplies", "contact@echo.com")
comp_mouse = PhysicalProduct("30", "Mouse", 10.0, 5, 0.3, comp_supplier)
comp_ebook = DigitalProduct("31", "E-book", 5.0, 5, 2.0, comp_supplier)

# Order 1: the Order creates its own OrderLines from a product and quantity
order_1 = Order("ORD-1")
order_1.add_order_line(comp_mouse, 2)
order_1.add_order_line(comp_ebook, 3)

print("Order 1:")
order_1.display_information()

composition_results.append(check("Order 1 has 2 order lines", len(order_1.get_order_lines()) == 2))
composition_results.append(check("Subtotal of first line is 20.0", order_1.get_order_lines()[0].calculate_subtotal() == 20.0))
composition_results.append(check("Order total is 35.0 (20.0 + 15.0)", order_1.calculate_total() == 35.0))

# Order 2: the SAME product goes into a different order
order_2 = Order("ORD-2")
order_2.add_order_line(comp_mouse, 1)

line_in_order_1 = order_1.get_order_lines()[0]
line_in_order_2 = order_2.get_order_lines()[0]

composition_results.append(check("Each Order creates its own OrderLine object", line_in_order_1 is not line_in_order_2))
composition_results.append(check("Both OrderLines refer to the same Product object", line_in_order_1.get_product() is line_in_order_2.get_product()))
composition_results.append(check("OrderLine refers to the Product but does not own it", line_in_order_1.get_product() is comp_mouse))

# Outside code cannot sneak a line in or out of an Order
order_1.get_order_lines().append("junk")
composition_results.append(check("Changing the returned list does not change the Order", len(order_1.get_order_lines()) == 2))

# Remove a line through the Order
composition_results.append(check("Order removes its own line", order_1.remove_order_line("31") is True))
composition_results.append(check("Order 1 now has 1 order line", len(order_1.get_order_lines()) == 1))
composition_results.append(check("Order total updates to 20.0", order_1.calculate_total() == 20.0))
composition_results.append(check("Removing a missing line returns False", order_1.remove_order_line("31") is False))

# The Products are not destroyed by any of this
composition_results.append(check("Product still exists after its OrderLine was removed", comp_ebook.get_name() == "E-book"))
composition_results.append(check("Order 2 is unaffected by changes to Order 1", order_2.calculate_total() == 10.0))

print(f"{sum(composition_results)} of {len(composition_results)} checks passed")

# ----- TEST LSP (SUBSTITUTABILITY) -----
print("\n----- TEST LSP (SUBSTITUTABILITY) -----")
lsp_results = []

def show_product_details(product: Product) -> None:
    """Works on ANY Product, using only what Product promises."""
    product.display_information()
    print(product.get_fulfilment_info())

lsp_supplier = Supplier("S005", "Foxtrot Ltd", "team@foxtrot.com")
lsp_physical = PhysicalProduct("40", "LSP Mouse", 10.0, 5, 0.3, lsp_supplier)
lsp_digital = DigitalProduct("41", "LSP Ebook", 5.0, 5, 2.0, lsp_supplier)

# The same function, unchanged, with both subclasses
for item in (lsp_physical, lsp_digital):
    try:
        show_product_details(item)
        lsp_results.append(check(f"show_product_details works with {type(item).__name__}", True))
    except Exception:
        lsp_results.append(check(f"show_product_details works with {type(item).__name__}", False))

# Both subclasses work in an Inventory through its normal operations
lsp_inventory = Inventory()
lsp_inventory.add_product(lsp_physical)
lsp_inventory.add_product(lsp_digital)

lsp_results.append(check("Inventory finds the physical product", lsp_inventory.find_product("40") is lsp_physical))
lsp_results.append(check("Inventory finds the digital product", lsp_inventory.find_product("41") is lsp_digital))
print("display_all():")
lsp_inventory.display_all()

# The expectation Product sets: update_stock(n) makes get_quantity() return

# ----- TEST POLYMORPHISM -----
print("\n----- TEST POLYMORPHISM -----")
poly_results = []

poly_supplier = Supplier("S006", "Golf Traders", "hi@golf.com")
poly_inventory = Inventory()
poly_inventory.add_product(PhysicalProduct("50", "Poly Keyboard", 30.0, 5, 1.0, poly_supplier))
poly_inventory.add_product(DigitalProduct("51", "Poly Ebook", 10.0, 5, 2.0, poly_supplier))
poly_inventory.add_product(SubscriptionProduct("52", "Poly Cloud", 5.0, 5, 12, poly_supplier))

# ONE loop over the Product collection, no isinstance()
fulfilment_messages = []
for product in poly_inventory.get_products():
    product.display_information()
    message = product.get_fulfilment_info()
    print(message)
    fulfilment_messages.append(message)

poly_results.append(check("All 3 product types are stored in the same Inventory", len(poly_inventory.get_products()) == 3))
poly_results.append(check("Every product returned a fulfilment message", all(isinstance(m, str) and m != "" for m in fulfilment_messages)))
poly_results.append(check("Each subclass gave its own, different message", len(set(fulfilment_messages)) == 3))

print(f"{sum(poly_results)} of {len(poly_results)} checks passed")


# =====================================================================
# LAB 9 TESTS (unittest) - Strategy, Factory, validation, exceptions
# =====================================================================

def make_supplier() -> Supplier:
    return Supplier("S1", "Test Supplier", "test@example.com")


def capture_output(function, *args):
    """Call function(*args); return (its result, everything it printed)."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        result = function(*args)
    return result, buffer.getvalue()


def order_worth_250(discount=None) -> Order:
    """An order whose lines add up to 250.0 before any discount."""
    desk = PhysicalProduct("1", "Desk", 125.0, 5, 12.0, make_supplier())
    order = Order("ORD-1", discount)
    order.add_order_line(desk, 2)
    return order


class HalfPrice(DiscountStrategy):
    """A brand-new strategy, defined here WITHOUT touching the Order class."""

    def apply(self, total: float) -> float:
        return total / 2


class TestDiscountStrategies(unittest.TestCase):
    def test_default_is_no_discount(self):
        self.assertEqual(order_worth_250().calculate_total(), 250.0)

    def test_bulk_discount_applies_at_threshold(self):
        self.assertEqual(order_worth_250(BulkDiscount(200, 20)).calculate_total(), 230.0)

    def test_bulk_discount_not_applied_below_threshold(self):
        self.assertEqual(order_worth_250(BulkDiscount(300, 20)).calculate_total(), 250.0)

    def test_percentage_discount(self):
        self.assertAlmostEqual(order_worth_250(PercentageDiscount(10)).calculate_total(), 225.0)

    def test_student_discount(self):
        self.assertAlmostEqual(order_worth_250(StudentDiscount()).calculate_total(), 237.5)

    def test_set_discount_changes_the_strategy(self):
        order = order_worth_250(BulkDiscount(200, 20))
        self.assertEqual(order.calculate_total(), 230.0)
        order.set_discount(PercentageDiscount(10))
        self.assertAlmostEqual(order.calculate_total(), 225.0)

    def test_new_strategy_works_without_changing_order(self):
        self.assertEqual(order_worth_250(HalfPrice()).calculate_total(), 125.0)

    def test_order_has_no_discount_branching(self):
        source = inspect.getsource(Order)
        self.assertNotIn("elif", source)
        self.assertNotIn("discount_type", source)

    def test_base_strategy_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            DiscountStrategy()

    def test_two_orders_can_share_one_strategy(self):
        shared = PercentageDiscount(10)
        first, second = order_worth_250(shared), order_worth_250(shared)
        self.assertAlmostEqual(first.calculate_total(), second.calculate_total())


class TestProductFactory(unittest.TestCase):
    def test_creates_physical_product(self):
        product = ProductFactory.create("physical", "1", "Desk", 10.0, 5, make_supplier(), 2.0)
        self.assertIsInstance(product, PhysicalProduct)
        self.assertIsInstance(product, Product)
        self.assertEqual(product.get_weight(), 2.0)

    def test_creates_digital_product(self):
        product = ProductFactory.create("digital", "2", "E-book", 10.0, 5, make_supplier(), 35.0)
        self.assertIsInstance(product, DigitalProduct)
        self.assertEqual(product.get_download_size(), 35.0)

    def test_creates_subscription_product(self):
        product = ProductFactory.create("subscription", "3", "Cloud", 5.0, 5, make_supplier(), 12.0)
        self.assertIsInstance(product, SubscriptionProduct)
        self.assertEqual(product.get_duration_months(), 12)

    def test_unknown_type_raises_clear_error(self):
        with self.assertRaises(ValueError) as context:
            ProductFactory.create("service", "4", "Install", 10.0, 5, make_supplier())
        self.assertIn("Unknown product type", str(context.exception))
        self.assertIn("service", str(context.exception))

    def test_every_created_product_works_through_the_product_type(self):
        for product_type in ("physical", "digital", "subscription"):
            with self.subTest(product_type=product_type):
                product = ProductFactory.create(product_type, "9", "X", 1.0, 1, make_supplier(), 1)
                self.assertIsInstance(product, Product)
                self.assertTrue(product.get_fulfilment_info())


class TestValidation(unittest.TestCase):
    def setUp(self):
        self.supplier = make_supplier()
        self.product = PhysicalProduct("1", "Desk", 10.0, 5, 2.0, self.supplier)

    def test_price_of_zero_is_rejected(self):
        with self.assertRaises(ValueError):
            PhysicalProduct("2", "X", 0, 5, 1.0, self.supplier)

    def test_negative_price_is_rejected(self):
        with self.assertRaises(ValueError):
            DigitalProduct("3", "X", -5.0, 5, 1.0, self.supplier)

    def test_negative_stock_is_rejected(self):
        with self.assertRaises(ValueError):
            SubscriptionProduct("4", "X", 5.0, -1, 12, self.supplier)

    def test_zero_stock_is_allowed(self):
        self.assertEqual(PhysicalProduct("5", "X", 5.0, 0, 1.0, self.supplier).get_quantity(), 0)

    def test_update_stock_rejects_negative(self):
        with self.assertRaises(ValueError):
            self.product.update_stock(-1)
        self.assertEqual(self.product.get_quantity(), 5)

    def test_update_stock_accepts_valid_value(self):
        self.product.update_stock(20)
        self.assertEqual(self.product.get_quantity(), 20)

    def test_every_subclass_inherits_the_rules(self):
        for product_type in ("physical", "digital", "subscription"):
            with self.subTest(product_type=product_type):
                with self.assertRaises(ValueError):
                    ProductFactory.create(product_type, "1", "X", 0, 5, self.supplier, 1)
                with self.assertRaises(ValueError):
                    ProductFactory.create(product_type, "1", "X", 5.0, -1, self.supplier, 1)

    def test_order_line_rejects_zero_quantity(self):
        with self.assertRaises(ValueError):
            OrderLine(self.product, 0)

    def test_order_line_rejects_negative_quantity(self):
        with self.assertRaises(ValueError):
            OrderLine(self.product, -3)

    def test_order_rejects_bad_quantity_and_keeps_no_line(self):
        order = Order("ORD-9")
        with self.assertRaises(ValueError):
            order.add_order_line(self.product, 0)
        self.assertEqual(len(order.get_order_lines()), 0)


class TestGetPositiveFloat(unittest.TestCase):
    def test_keeps_asking_until_valid(self):
        with patch("builtins.input", side_effect=["abc", "-5", "12.50"]):
            result, printed = capture_output(get_positive_float, "Price: ")
        self.assertEqual(result, 12.5)
        self.assertIn("valid number", printed)
        self.assertIn("greater than zero", printed)

    def test_zero_is_rejected(self):
        with patch("builtins.input", side_effect=["0", "3"]):
            result, printed = capture_output(get_positive_float, "Price: ")
        self.assertEqual(result, 3.0)
        self.assertIn("greater than zero", printed)


CSV_TEXT = (
    "product_type,product_id,name,price,stock_quantity\n"
    "physical,P001,Desk Lamp,25.00,10\n"
    "digital,D001,Photo Editor,49.90,100\n"
    "service,S001,Installation,30.00,5\n"
    "physical,P002,Office Chair,abc,3\n"
    "physical,P003,Monitor Stand,39.50,7\n"
)


class TestLoadProducts(unittest.TestCase):
    def test_valid_rows_load_and_bad_rows_are_skipped(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "products.csv")
            with open(path, "w", newline="") as file:
                file.write(CSV_TEXT)
            inventory = Inventory()
            _, printed = capture_output(load_products, path, inventory, make_supplier())
        ids = [product.get_id() for product in inventory.get_products()]
        self.assertEqual(ids, ["P001", "D001", "P003"])
        self.assertEqual(printed.count("Skipping row"), 2)
        self.assertIn("S001", printed)
        self.assertIn("P002", printed)
        self.assertIn("3 products loaded.", printed)
        self.assertTrue(printed.strip().endswith("Load attempt finished."))

    def test_missing_file_is_handled_without_crashing(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "does_not_exist.csv")
            inventory = Inventory()
            _, printed = capture_output(load_products, path, inventory, make_supplier())
        self.assertEqual(len(inventory.get_products()), 0)
        self.assertIn("Products file not found", printed)
        self.assertNotIn("products loaded", printed)
        self.assertTrue(printed.strip().endswith("Load attempt finished."))

    def test_row_with_wrong_number_of_columns_is_skipped(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "short.csv")
            with open(path, "w", newline="") as file:
                file.write("product_type,product_id,name,price,stock_quantity\nphysical,P9,Short\n")
            inventory = Inventory()
            _, printed = capture_output(load_products, path, inventory, make_supplier())
        self.assertEqual(len(inventory.get_products()), 0)
        self.assertIn("Skipping row", printed)
        self.assertIn("0 products loaded.", printed)


class TestExceptionStyle(unittest.TestCase):
    def test_no_bare_except_anywhere(self):
        tree = ast.parse(inspect.getsource(inventory_manager))
        bare = [h.lineno for h in ast.walk(tree)
                if isinstance(h, ast.ExceptHandler) and h.type is None]
        self.assertEqual(bare, [], f"Bare 'except:' found on line(s) {bare}")


class TestLab8Checks(unittest.TestCase):
    """Makes the Lab 8 PASS/FAIL checks count as a real pass/fail for CI."""

    def test_all_lab8_checks_pass(self):
        all_results = (product_results + shipping_results + fulfilment_results
                       + association_results + aggregation_results + composition_results
                       + lsp_results + poly_results)
        self.assertTrue(all(all_results), "A Lab 8 check printed FAIL above")


if __name__ == "__main__":
    unittest.main()