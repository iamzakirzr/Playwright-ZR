Feature: Store login
  As a Sauce Demo customer
  I want to sign in securely
  So that I can shop with my account

  Background:
    Given I am on the login page

  @smoke
  Scenario: Standard user signs in
    When I log in as "standard_user"
    Then I see the product catalogue with 6 products

  Scenario Outline: Invalid sign-in attempts are rejected
    When I log in as "<username>" with password "<password>"
    Then I see the error "<error>"

    Examples:
      | username        | password     | error                   |
      | locked_out_user | secret_sauce | locked out              |
      |                 | secret_sauce | Username is required    |
      | standard_user   | wrong        | do not match any user   |
