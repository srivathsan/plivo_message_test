'''
@File: test_message.py

@Brief: Python unittest based test cases for testing purchaising numbers and sending message using Plivo REST apis.

@Author: Srivathsan Kumar

@Description:
Test case data are defined by the 'TEST_CASES' global variable.
The test functions are dynamically generated using the generator function
with the data from the TEST_CASES, and added to the test suite.

@How to run:
>python test_message.py

@Requires:
- resource.py either in the same directory or in PYTHONPATH

@Note:
- works in python 2.7.x (prints used are not compatible with 3.x)
'''
import time
import unittest

# importing custom test libraries
from resource import Account, Message, isclose

# List of test case data
TEST_CASES=[
    {
        'test_name':'simple_test',
        'auth_id':'MAYTFINJIYOTLMNTHKZJ',
        'auth_token':'NjQ2ZjIzZmFiN2MyZjFlMGZiYjJkMzM3MjM1Mzhl',
        'country_iso':'US',
        'numbers_count':2,
        'message_text':'test message',
        'max_wait_for_credit_update': 60,
        'pattern': 234,
        'expect_failure': False,
    },
    {
        'test_name':'big_text',
        'auth_id':'MAYTFINJIYOTLMNTHKZJ',
        'auth_token':'NjQ2ZjIzZmFiN2MyZjFlMGZiYjJkMzM3MjM1Mzhl',
        'country_iso':'US',
        'numbers_count':2,
        'message_text':'this is a big test message this is a big test message',
        'max_wait_for_credit_update': 60,
        'pattern': 234,
        'expect_failure': False,
    },
]


class TestMessage(unittest.TestCase):
    '''
    The main test class into which the test case functions will be added dynamically.
    '''
    pass


def test_generator(test_name, auth_id, auth_token, country_iso, numbers_count, message_text, max_wait_for_credit_update, pattern, expect_failure=False):
    '''
    Test generator function, which creates test functions dynamically 
    based on the test data and returns it to caller to be added to test class.
    
    Params:
        - test_name: name of the test case
        - auth_id: auth_id of the account
        - auth_token: auth token of the account
        - country_iso: ISO country code for purchaising numbers and pricing details
        - numbers_count: count of numbers to be purchaised
        - message_text: message text to be sent
        - max_wait_for_credit_update: maximum wait time for message to be sent
        - pattern: pattern pf number to search when purchaising
        - expect_failure: set to True if its a negative test cases, else False
    '''
    def test(self):
        print
        print "--------------------{name}--------------------".format(name=test_name)
        print "Auth ID: {auth_id}".format(auth_id=auth_id)
        print "Auth Token: {auth_token}".format(auth_token=auth_token)
        print "Country ISO: {country_iso}".format(country_iso=country_iso)
        print "Numbers Count: {numbers_count}".format(numbers_count=numbers_count)
        print "Message Text: {message_text}".format(message_text=message_text)
        print "--------------------------------------------------------"
        
        account = Account(auth_id, auth_token)
        print "Account details"
        message_rate = account.get_message_pricing(country_iso)
        print "--Message outbound rate for the account: {message_rate}".format(message_rate=message_rate)
        print "Buying %s numbers..." % numbers_count
        numbers = account.buy_numbers(numbers_count, country_iso)
        print "Bought Numbers:"
        for number in numbers:
            print "  %s" % number
        credit_before_message = account.get_credit_balence()
        print "Credit balance before sending message: %s" % credit_before_message

        print "Sending message from {_from} to {_to} ...".format(_from=numbers[0], _to=numbers[1])
        message = Message('{num}'.format(num=numbers[0]), '{num}'.format(num=numbers[1]), message_text, account)
        print "Message sent status %s" % message.message_sent
        self.assertTrue(message.message_sent, 'Message not sent within 60 seconds')
        print "Message UUID: %s" % message.message_uuid
        
        count = 0
        max_count = max_wait_for_credit_update
        step = 5
        print "Waiting for maximum of %s seconds for credit to get detected" % max_count
        while count <= max_count:
            credit_after_message = account.get_credit_balence()
            if credit_before_message > credit_after_message:
                break
            else:
                count += step
                time.sleep(step)

        print "Latest Credit balance: %s" % credit_after_message
        self.assertLess(credit_after_message, credit_before_message, 'Failed to deduct cost from credit')
        total_cost = credit_before_message - credit_after_message
        print "Totel cost of the message: %s" % total_cost
        self.assertTrue(isclose(total_cost, float(message_rate)), 'Failed to deduct correct cost from credit')
        print "%s Test: Passed" % test_name
        
    # make negative test cases pass by making failure as pass
    if expect_failure:
        # equivalent of macro @unittest.expectedFailure
        callable_test_function = unittest.expectedFailure(test)
    else:
        callable_test_function = test
    return callable_test_function

if __name__ == '__main__':
    # loop through the test data and generate test functions and add to test class
    for test_data in TEST_CASES:
        dynamic_test = test_generator(
            test_name = test_data['test_name'],
            auth_id = test_data['auth_id'],
            auth_token = test_data['auth_token'],
            country_iso = test_data['country_iso'],
            numbers_count = test_data['numbers_count'],
            message_text = test_data['message_text'],
            max_wait_for_credit_update = test_data['max_wait_for_credit_update'],
            pattern = test_data['pattern'],
            expect_failure = test_data['expect_failure'],
        )
        setattr(TestMessage, 'test_{name}'.format(name=test_data['test_name']), dynamic_test)
        
    # run the tests
    unittest.main()

