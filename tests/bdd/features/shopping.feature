Feature: Checkout
  As a signed-in customer
  I want to buy products
  So that they are shipped to me

  Scenario: Buy two products
    Given I am signed in as "standard_user"
    When I add "Sauce Labs Backpack" to the cart
    And I add "Sauce Labs Bike Light" to the cart
    And I check out with generated customer details
    Then the order total equals the item total plus tax
    And I see "Thank you for your order!"
