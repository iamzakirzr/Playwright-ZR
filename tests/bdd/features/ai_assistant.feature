Feature: AI shopping assistant
  As a customer chatting with the store assistant
  I want it to change my cart when I ask
  So that I can shop by conversation

  Scenario: The assistant adds items to the cart
    Given a new chat session
    When I say "Add 2 backpacks to my cart"
    Then my cart contains 2 x "Sauce Labs Backpack"
    And the assistant called the "add_to_cart" tool

  Scenario: The assistant answers policy questions from the knowledge base
    Given a new chat session
    When I say "How many days do I have to return an item?"
    Then the reply mentions "45"
    And my cart is empty
