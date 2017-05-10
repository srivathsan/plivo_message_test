# plivo_message_test
Messaging test cases for Pliva apis

Main Test File: test_message.py

Brief: Python unittest based test cases for testing purchaising numbers and sending message using Plivo REST apis.

Description:
Test case data are defined by the 'TEST_CASES' global variable.
The test functions are dynamically generated using the generator function
with the data from the TEST_CASES, and added to the test suite.

How to run:
>python test_message.py

Requires:
- requests python package need to be pre-installed (pip install requests)
- resource.py either in the same directory or in PYTHONPATH
resource.py contains three classes
ResourceBase: the class for handling all the REST calls.
Account: This class is for managing account details and purchasing Numbers.
Number: This class is for purchasing and managing numbers and is encapsulated in Account class.
Message: This class helps to send message and get the sent message details.

isclose: This is a helper function for comparison of float variables

resource.py Usage:
from resource import Account, Message

account = Account(auth_id, auth_token)
numbers = account.buy_numbers(numbers_count, country_iso)
message = Message(src, dst, text, account)

Note:
- works in python 2.7.x (prints used are not compatible with 3.x)

