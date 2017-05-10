'''
@File: resource.py

@Brief: Classes for accessing/maganing Plivo resources like Account, Numbers and Messages.

@Author: Srivathsan Kumar

@Description:
Contains three classes
ResourceBase: the class for handling all the REST calls.
Account: This class is for managing account details and purchasing Numbers.
Number: This class is for purchasing and managing numbers and is encapsulated in Account class.
Message: This class helps to send message and get the sent message details.

isclose: This is a helper function for comparison of float variables

@Usage:
from resource import Account, Message

account = Account(auth_id, auth_token)
numbers = account.buy_numbers(numbers_count, country_iso)
message = Message(src, dst, text, account)

Exceptions are not handled in the library, as this is supposed to be used
with python unittest, which does catch exception at the highr level and failes the tests.

@Requires:
- requests python package need to be pre-installed (pip install requests)

@Note:
- This script cannot be called as a standalone but should be used as a library
'''
import json
import requests
import sys
import time

# Import for Basic Auth
from requests.auth import HTTPBasicAuth

# URLs to connect to Plivo
URLS = {
    'GET_AVAILABLE_NUMBERS': 'https://api.plivo.com/v1/Account/{auth_id}/PhoneNumber/',
    'BUY_NUMBER': 'https://api.plivo.com/v1/Account/{auth_id}/PhoneNumber/{number}/',
    'DELETE_NUMBER': 'https://api.plivo.com/v1/Account/{auth_id}/Number/{number}/',
    'GET_MY_NUMBERS': 'https://api.plivo.com/v1/Account/{auth_id}/Number/',
    'SEND_MESSAGE': 'https://api.plivo.com/v1/Account/{auth_id}/Message/',
    'GET_MESSAGE_DETAILS': 'https://api.plivo.com/v1/Account/{auth_id}/Message/{message_uuid}/',
    'GET_ACCOUNT_BALENCE': 'https://api.plivo.com/v1/Account/{auth_id}/',
    'GET_PRICING': 'https://api.plivo.com/v1/Account/{auth_id}/Pricing/',
}

        
class ResourceBase(object):
    '''
    The class to encapsulate all the REST calls.
    Requires auth_id and auth_token for basic auth of the apis.
    '''

    def __init__(self, auth_id, auth_token):
        '''
        Constructor
        '''
        self.auth_id = auth_id
        self.auth_token = auth_token

    def send_get_request(self, url, params={}):
        '''
        Get call wrapper
        '''
        url = url.format(auth_id=self.auth_id)
        response = requests.get(url, params=params, auth=HTTPBasicAuth(self.auth_id, self.auth_token))
        return True if 200==response.status_code else False, response.json()
        
    def send_post_request(self, url, payload={}):
        '''
        Post call wrapper
        '''
        url = url.format(auth_id=self.auth_id)
        headers = {'Content-type': 'application/json'}
        response = requests.post(url, data=payload, auth=HTTPBasicAuth(self.auth_id, self.auth_token), headers=headers)
        return True if response.status_code in [201, 202] else False, response.json()
        
    def send_delete_request(self, url):
        '''
        Delete call wrapper
        '''
        url = url.format(auth_id=self.auth_id)
        response = requests.delete(url, data=payload, auth=HTTPBasicAuth(self.auth_id, self.auth_token), headers=headers)
        return True if 204==response.status_code else False

class Account(ResourceBase):
    '''
    Class to encapsulate Plivo Account related queries.
    As this is class holding the auth credentials, it inherits ResourceBase
    and in turn wraps all the REST calls for other resources. All the other resources will
    have to depend on this class to make REST calls.
    '''

    def __init__(self, auth_id, auth_token):
        '''
        Constructor
        '''
        super(Account, self).__init__(auth_id, auth_token)
        self.bought_numbers = {}
        
    def get_message_pricing(self, country_iso='US'):
        '''
        Function to get messaging outbound rate for a given country
        '''
        status, response = self.send_get_request(URLS['GET_PRICING'], params={'country_iso':country_iso})
        return response['message']['outbound']['rate']
        
    def buy_numbers(self, numbers_count=1, country_iso=None, number_type=None, pattern=None, force_buy=False):
        '''
        Function to purchase requested number of number of speficid pattern and country.
        When not forced to buy will see if there are available numbers
        in the account and return that. This is done to save cost of renting number.
        Returns a list of bought numbers
        '''
        if not force_buy:
            status, response = self.send_get_request(URLS['GET_MY_NUMBERS'])
            my_numbers = [n['number'] for n in response['objects']]
            if len(my_numbers) >= numbers_count:
                return my_numbers[:numbers_count]
        for count in range(numbers_count):
            number = Number(country_iso, number_type, pattern, self)
            self.bought_numbers[number] = {'country_iso': country_iso, 'number_type': number_type, 'pattern': pattern}
        return [n.number for n in self.bought_numbers]
        
    def unrent_number(self, numbers_list):
        '''
        Function to unrent list of numbers 
        '''
        if not isinstance(numbers_list, list):
            numbers_list = [numbers_list]
            
        for number in numbers_list:
            self.send_delete_request(URLS['DELETE_NUMBER'].format(auth_id='{auth_id}', number=number))
            
    def get_credit_balence(self):
        '''
        Function to get current credit balence of the account
        '''
        status, response = self.send_get_request(URLS['GET_ACCOUNT_BALENCE'])
        credit = response['cash_credits']
        return float(credit)
        
            
class Number(object):
    '''
    Class to handle number related transactions.
    '''
    def __init__(self, country_iso='US', number_type=None, pattern=None, account=None, buy_number=True):
        '''
        Constructor
        Also purchases the number unless specifically asked not to.
        '''
        self.country_iso = country_iso
        self.number_type = number_type
        self.pattern = pattern
        self.account = account
        if buy_number:
            self.number = self.buy_number(country_iso, number_type, pattern)
        
    def get_available_numbers(self, country_iso=None, number_type=None, pattern=None):
        '''
        Returns a list of available numbers with specified pattern and country.
        '''
        availble_numbers = []
        params = {'country_iso':country_iso}
        if pattern:
            params.update({'pattern': pattern})
        status, response = self.account.send_get_request(
            url=URLS['GET_AVAILABLE_NUMBERS'],
            params=params,
        )
        if status:
            for number_object in response['objects']:
                availble_numbers.append(number_object['number'])
        return availble_numbers
        
    def buy_number(self, country_iso=None, number_type=None, pattern=None, number_choice='first'):
        '''
        Function to purchase number with given pattern and country.
        Choise of number selection from available list is configurable.
        '''
        available_numbers = self.get_available_numbers(country_iso, number_type, pattern)
        if not available_numbers:
            return None
        # Currently the first number is chosen
        # TODO: Random selection of number
        if 'first' == number_choice:
            choosen_number = available_numbers[0]
        status, response = self.account.send_post_request(
            url=URLS['BUY_NUMBER'].format(auth_id='{auth_id}', number=choosen_number),
        )
        return response['numbers'][0]['number']

        
class Message(object):
    '''
    Class that encapsulates messaging sending and its details.
    '''
    def __init__(self, from_number, to_number, message_text, account=None, send_message=True):
        '''
        Constructor
        Also sends the message unless not explicitely asked to.
        '''
        self.from_number = from_number
        self.to_number = to_number
        self.message_text = message_text
        self.account = account
        self.message_sent = False
        if send_message:
            self.send_message(from_number, to_number, message_text)
        
    def send_message(self, from_number, to_number, message_text):
        '''
        Function to send a text message from given number to another riven number
        '''
        status, response = self.account.send_post_request(
            url = URLS['SEND_MESSAGE'],
            payload = json.dumps({
                'src':from_number,
                'dst':to_number,
                'text':message_text,
            })
        )
        self.message_uuid = response['message_uuid'][0]
        count = 0
        max_count = 12
        # wait maximum of 60 seconds for message to be sent
        # TODO max wait time for wait should be configurable from test
        while not self.message_sent:
            self.details = self.get_message_details(self.message_uuid)
            print self.details['message_state']
            if self.details['message_state'].lower() == 'sent':
                self.message_sent = True
            else:
                if count >= max_count:
                    break
                count += 1
                time.sleep(5)
        return self.message_uuid, self.details
        
    def get_rate(self):
        '''
        Function to get total rate of the message transaction
        '''
        return self.details['total_rate']
        
    def get_message_details(self, message_uuid):
        '''
        Function to get message details
        '''
        status, response = self.account.send_get_request(
            URLS['GET_MESSAGE_DETAILS'].format(auth_id='{auth_id}', message_uuid=message_uuid),
        )
        return response

        
def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    '''
    Helper function to compare float numbers
    '''
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


if __name__ == '__main__':
    sys.exit('Cannot run this script as standalone')

