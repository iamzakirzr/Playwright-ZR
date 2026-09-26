"""UI page objects. One class per page; shared widgets live in ``pages/components``."""
from pages.cart_page import CartPage
from pages.chat_page import ChatPage
from pages.checkout_page import CheckoutPage
from pages.demo_login_page import DemoLoginPage
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage

__all__ = ["CartPage", "ChatPage", "CheckoutPage", "DemoLoginPage", "InventoryPage", "LoginPage"]
