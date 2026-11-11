from __future__ import annotations
from inventory_manager import Product, PhysicalProduct, DigitalProduct, CanBeShipped, Supplier

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

print(f"{sum(association_results)} of {len(association_results)} checks passed")
print(f"{sum(fulfilment_results)} of {len(fulfilment_results)} checks passed")