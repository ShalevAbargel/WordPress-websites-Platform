# Nethanel Gelernter (c)
import time

from httpsrequesthandler import HTTPRequestHandler
from proxy import Proxy
import json

from wpdetector import WPDetector


class WPEnumerator(object):
    _MIN_ID = 0
    _MAX_ID = 20
    _URL_REST_API = "/wp-json/wp/v2/users/"
    _URL_BRUTE_FORCE = "/?author="
    _URL_BRUTE_FORCE_BYPASS_1 = "?author[]="

    def __init__(self, domain, additional_data=None, proxies=None):
        """
        Keep state of data that is collected and tries that were performed for efficieny
        :param domain: String. domain
        :param additional_data: data that might be useful for performing the enumeration
        :param proxies: working via HTTP proxies
        """
        try:
            self._domain = domain
            self._additional_data = additional_data
            if proxies is None:
                self._proxies = proxies
            else:
                tmp = []
                self._proxies = []
                for proxy in proxies:
                    p = Proxy(proxy)
                    tmp.append(p)
                self._proxies = tmp
            self._user_data_brut = {}
            self._user_data_rest = {}
            self._user_names = []
        except Exception as e:
            print(e)

    def _enumerate_bruteforce(self, min_id=_MIN_ID, max_id=_MAX_ID, proxies=None, bypass=False):
        """
        This Function enumerates users using a bruteforce method
        :param min_id: int. the min id of user to enumerate
        :param max_id: int. the max id of user to enumerate
        :return: None
        """
        try:
            if proxies is not None:
                self._proxies = proxies
            http_handler = HTTPRequestHandler(proxies=self._proxies, retries=0, timeout=5)
            users_dict = {}
            users_list = []
            r = HTTPRequestHandler().send_http_request(method='get', url='http://' + str(self._domain))
            url = r.url
            if min_id == 0:
                min_id += 1
            for i in range(min_id, max_id):
                try:
                    if not bypass:
                        r = http_handler.send_http_request(method='get', url=url + self._URL_BRUTE_FORCE + str(i))
                    else:
                        r = http_handler.send_http_request(method='get',
                                                           url=url + self._URL_BRUTE_FORCE_BYPASS_1 + str(i))
                        if r is None:
                            break
                    user_name = ''
                    if '/author/' in r.url:
                        user_name = str(r.url).split('/author/')[1][:-1]
                    else:
                        data = str(r.content)
                        start_index = data.find('<title>')
                        if start_index != -1:
                            end_1 = data.find(" &", start_index)
                            end_2 = data.find(",", start_index)
                            end = min(end_1, end_2)
                            user_name_optional = data[start_index + 7:end]
                            if str(r.status_code) == '200' and '\\x' not in user_name_optional.lower() \
                                    and len(user_name_optional) < 30:
                                user_name = user_name_optional
                    if user_name:
                        users_dict[i] = user_name
                    if user_name:
                        users_list.append(user_name)
                except Exception as e:
                    print(e)
            self._user_data_brut.update(users_dict)
            if users_list:
                self._user_names = self._user_names + users_list
        except Exception as e:
            print(e)

    def _enumerate_rest_api(self, proxies=None):
        """
        This Function enumerates users using a rest_api method
        :return: None
        """
        try:
            if proxies is not None:
                self._proxies = proxies
            http_handler = HTTPRequestHandler(proxies=self._proxies, retries=0, timeout=5)
            users_dict = {}
            users_list = []
            url_rest_api = 'https://' + str(self._domain) + self._URL_REST_API
            url_rest_api_http = 'http://' + str(self._domain) + self._URL_REST_API
            try:
                r = http_handler.send_http_request(method='get', url=url_rest_api)
                if r is None:
                    r = http_handler.send_http_request(method='get', url=url_rest_api_http)
                json_response_list = json.loads(r.content)
                for json_item in json_response_list:
                    '''
                    id_data = []
                    if json_item['id'] in users_dict.keys():
                        id_data.append(users_dict[json_item['id']])
                        id_data.append(json_item['name'])
                    else:
                    '''
                    users_dict[json_item['id']] = json_item['name']
                    if json_item['name']:
                        users_list.append(json_item['name'])
            except Exception as e:
                print(e)
            self._user_data_rest.update(users_dict)
            if users_list:
                self._user_names = self._user_names + users_list
        except Exception as e:
            print(e)

    def enumerate(self, min_id=_MIN_ID, max_id=_MAX_ID, proxies=None):
        """
        If you use multiple methods, or bypass tricks for plugin's defenses, consider using protected methods and
        managing them from this method
        :param min_id: int. the min id of user to enumerate
        :param max_id: int. the max id of user to enumerate
        :param proxies: working via HTTP proxies. If None, the constructor's proxies are used (if any)
        :return: dictionary from id to username or None if enumeration seems impossible {id:username}. if there are
        a couple of user names with the same id it will return id:[username1,username2..]
        """
        try:
            is_possible = self.is_enumeration_possible()
            detector = WPDetector(self._domain)
            if not is_possible:
                if detector.is_wordpress()[0]:
                    self._enumerate_bruteforce(min_id=min_id, max_id=max_id, proxies=proxies, bypass=True)
                else:
                    return {}
            else:
                for url in is_possible[1]:
                    if 'author' in url:
                        self._enumerate_bruteforce(min_id=min_id, max_id=max_id, proxies=proxies)
                        if not self._user_names:
                            self._enumerate_bruteforce(min_id=min_id, max_id=max_id, proxies=proxies, bypass=True)
                    elif 'users' in url:
                        self._enumerate_rest_api(proxies=proxies)
            return self.get_users_data()
        except Exception as e:
            print(e)

    def get_usernames(self, is_valid=False):
        """
        This Function returns the enumerated list of usernames
        :param is_valid:boolean. if is_valid is true then validate data before return
        list of usernames that were enumerated
        :return: list [username1,username2 ..]
        """
        try:
            if not self._user_names:
                return []
            users_once = []
            for user in self._user_names:
                if user not in users_once:
                    users_once.append(user)
            # if is valid is true so return new dictionary with validate data
            if is_valid:
                data = self.validate_data(users_once)
                valid_data = []
                # remove all duplicate data from list
                for i in data:
                    if i not in valid_data:
                        valid_data.append(i)
                return valid_data
            # is_valid is false- return the full data no validate
            else:
                return users_once
        except Exception as e:
            print(e)

    def get_users_data(self, is_valid=False):
        """
        This Function returns the enumerated dictionary of id's to usernames
        :param is_valid:boolean. if is_valid is true then validate data before return
        dictionary of id to username for all enumerated users
        :return: dictionary from id to username or None if enumeration seems impossible {id:username}. if there are
        a couple of user names with the same id it will return id:[username1,username2..]
        """
        try:
            #if self._user_data_brut == {} and self._user_data_rest == {}:
             #   self.enumerate()
            combine_user_data = {}
            combine_user_data.update(self._user_data_rest)
            for key in self._user_data_brut:
                id_data = []
                if key in combine_user_data.keys() and self._user_data_brut[key] != combine_user_data[key]:
                    id_data.append(self._user_data_brut[key])
                    id_data.append(combine_user_data[key])
                    combine_user_data[key] = id_data
                else:
                    combine_user_data[key] = self._user_data_brut[key]
            combine_user_data_tmp = {}
            for key in combine_user_data.keys():
                if combine_user_data[key] not in combine_user_data_tmp.values():
                    combine_user_data_tmp.update({key: combine_user_data[key]})
            # if is valid is true so return new dictionary with validate data
            if is_valid:
                list_of_usernames = list(combine_user_data_tmp.values())
                new_list_of_usernames = []
                # because some values are list and some string- build new list of strings
                for l in list_of_usernames:
                    if type(l) == list:
                        for val in l:
                            new_list_of_usernames.append(val)
                    else:
                        new_list_of_usernames.append(l)
                valid_data = self.validate_data(new_list_of_usernames)
                new_valid_data = []
                new_dict = dict()
                # remove all duplicate data from list
                for i in valid_data:
                    if i not in new_valid_data:
                        new_valid_data.append(i)
                # build new dictionary with the same key and the validate and correct username
                for i in combine_user_data_tmp:
                    for value in new_valid_data:
                        if value in combine_user_data_tmp.get(i):
                            new_dict[i] = value
                return new_dict
            # is_valid is false- return the full data no validate
            else:
                return combine_user_data_tmp
        except Exception as e:
            print(e)

    def validate_data(self, data):
        """
        This function validates the usernames that were enumerated
        :param data: list. the usernames to validate
        return: list. the final validate usernames
        """
        try:
            r = HTTPRequestHandler().send_http_request(method='get', url='http://' + str(self._domain))
            wp_login_url = r.url + '/wp-login.php'
            r = HTTPRequestHandler().send_http_request(method='get', url=wp_login_url)
            if str(r.status_code) == '200':
                for user in data:
                    if " " in user:
                        new_user = str(user).split(" ")
                        data += new_user
                        u = str(user).replace(" ", "_")
                        data += [u]
                valid_data = self.wp_login_validate(wp_login_url, data)
                return valid_data
            else:
                return data
        except Exception as e:
            print(e)

    def wp_login_validate(self, url, data):
        """
        This function validates the usernames by trying to log in with the username and sees what is the error. is there
        no such username or is only the password wrong
        :param url: full url for the login request
        :param data: list. the usernames to validate
        return: list. the final validate usernames
        """
        try:
            valid_data = []
            for u in data:
                try:
                    payload = {'log': u, 'pwd': '1234'}
                    http_handler = HTTPRequestHandler(proxies=self._proxies, retries=0, timeout=5,
                                                      payload=payload)
                    r = http_handler.send_http_request(method='post', url=url)
                    if 'Please verify you are human' in r.text:
                        break
                    if 'Invalid username' in r.text:
                        continue
                    elif 'The password you entered for the username' in r.text:
                        valid_data.append(u)
                except Exception as e:
                    print(e)
                    continue
            return valid_data
        except Exception as e:
            print(e)

    def is_enumeration_possible(self):
        """
        Returns whether the enumeration is possible or not
        :return: tuple (if enumeration is possible or not, list of the urls that indicated it is possible)
        """
        try:
            url_rest_api = 'https://' + str(self._domain) + self._URL_REST_API
            url_rest_api_http = 'http://' + str(self._domain) + self._URL_REST_API
            url_brute_force = 'https://' + str(self._domain) + self._URL_BRUTE_FORCE + str(self._MIN_ID + 1)
            url_brute_force_http = 'http://' + str(self._domain) + self._URL_BRUTE_FORCE + str(self._MIN_ID + 1)

            http_handler = HTTPRequestHandler(proxies=self._proxies, retries=0, timeout=5)
            try:
                r1 = http_handler.send_http_request(method='get', url=url_rest_api)
                if r1 is None:
                    r1 = http_handler.send_http_request(method='get', url=url_rest_api_http)
                r2 = http_handler.send_http_request(method='get', url=url_brute_force)
                if r2 is None:
                    r2 = http_handler.send_http_request(method='get', url=url_brute_force_http)

                if r1.status_code != 200 and '/author/' not in r2.url:
                    return False
                else:
                    if r1.status_code == 200 and '/author/' in r2.url:
                        return True, [self._URL_REST_API, self._URL_BRUTE_FORCE]
                    elif r1.status_code != 200 and '/author/' in r2.url:
                        return True, [self._URL_BRUTE_FORCE]
                    elif r1.status_code == 200 and '/author/' not in r2.url:
                        return True, [self._URL_REST_API]
            except Exception as e:
                print(e)
        except Exception as e:
            print(e)

    # Feel free to add public method that you consider to be relevant for the users
    # user _ and __ for private and protected methods that should not be used outside the class
