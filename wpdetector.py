from httpsrequesthandler import HTTPRequestHandler
from proxy import Proxy

_VERSION_NON_DETECTABLE_URLS = ["/license.txt", "/readme.html", "/wp-admin/upgrade.php", '/robots.txt']

_VERSION_DETECTABLE_URLS = ['/wp-admin', '/feed', '/feed/atom', '/wp-links-opml.php']


class WPDetector(object):

    def __init__(self, domain, proxies=None):
        """
        Keep here the domain and the test state (tested URLs, detected versions, etc) using protected attributes
        :param domain: String. the domain we are working on (exp: 'aaa.com')
        :param proxies: working via HTTP proxies
        """
        self._domain = domain
        if proxies is None:
            self._proxies = proxies
        else:
            tmp = []
            self._proxies = []
            for proxy in proxies:
                p = Proxy(proxy)
                tmp.append(p)
            self._proxies = tmp
        self._urls = _VERSION_DETECTABLE_URLS + _VERSION_NON_DETECTABLE_URLS

    def detect(self, retries=0, timeout=5, aggressive=False, urls=None, proxies=None):
        """
        This function detects if the website on the domain runs over wordpress. if it is, it will detect the version
        :param aggressive: if aggressive is False, the maximal number of HTTP requests is len(urls) + 2
        :param urls: URLs to analyze; make sure the URLs are relevant for the domain
        :param proxies: working via HTTP proxies. If None, the constructor's proxies are used (if any)
        :param retries: The number of tries that each HTTP request will be sent until it will succeed
        :param timeout: How much time each HTTP request will wait for an answer
        :return: a tuple: (whether the domain operates over Wordpress, its version)
        """
        try:
            if urls is None:
                urls = self._urls
            if proxies is None:
                proxies = self._proxies
            if not aggressive:
                return self.is_wordpress(urls=urls, proxies=proxies, timeout=timeout, retries=retries)
            else:
                return self.is_wordpress(urls=urls, proxies=proxies, retries=3, timeout=5)
        except Exception as e:
            print(e)

    def is_wordpress_no_url(self, proxies=None, timeout=5, retries=0):
        """
        This function cheks if a domain is running WordPress even if there aren't any urls givven
        :param proxies: working via HTTP proxies. If None, the constructor's proxies are used (if any)
        :param retries: The number of tries that each HTTP request will be sent until it will succeed
        :param timeout: How much time each HTTP request will wait for an answer
        :return: List of tuples of all the indications [(True/False, if a version was discovered)
        """
        response_list = []
        url = 'https://' + str(self._domain)
        http_handler = HTTPRequestHandler(proxies=proxies, retries=retries, timeout=timeout)
        response = http_handler.send_http_request(method='get', url=url)
        if response is None:
            url = 'http://' + str(self._domain)
            http_handler = HTTPRequestHandler(proxies=proxies, retries=retries, timeout=timeout)
            response = http_handler.send_http_request(method='get', url=url)
            if response is None:
                pass
        if str(response.status_code) != '200':
            response_list.append((False, "Could'nt detect version"))
            return response_list
        else:
            response_list = []
            # check in source code if important 'wp-'s in:
            count = 0
            http_handler = HTTPRequestHandler(proxies=proxies, retries=retries, timeout=timeout)
            response = http_handler.send_http_request(method='get', url=url)
            if 'wp-content' in str(response.content):
                count += 1
            if 'wordpress' in str(response.content).lower():
                count += 1
            if 'wp-admin' in str(response.content):
                count += 1
            if 'wp-includes' in str(response.content):
                count += 1
            if 'wp-json' in str(response.content):
                count += 1
            if 5 >= count >= 3:
                response_list.append((True, "Could'nt detect version"))
            else:
                response_list.append((False, "Could'nt detect version"))
            if 'name="generator" content="wordpress"' in str(response.content).lower():
                response_list.append(self.get_version(response.content, url + '/wp-admin'))
                return response_list
        return response_list

    def is_wordpress(self, urls=None, proxies=None, timeout=5, retries=0):
        """
        This function detects if the website runs over wordpress
        :param urls: URLs to analyze; make sure the URLs are relevant for the domain
        :param proxies: working via HTTP proxies. If None, the constructor's proxies are used (if any)
        :param retries: The number of tries that each HTTP request will be sent until it will succeed
        :param timeout: How much time each HTTP request will wait for an answer
        :return: a tuple: (whether the domain operates over Wordpress, its version)
        """
        try:
            response_list = []
            if not urls:
                response_list += self.is_wordpress_no_url(proxies=proxies, timeout=timeout, retries=retries)
            else:
                response_list = []
                for url in urls:
                    complete_url = 'https://' + str(self._domain) + url
                    http_handler = HTTPRequestHandler(proxies=proxies, retries=retries, timeout=timeout)
                    response = http_handler.send_http_request(method='get', url=complete_url)
                    if response is None:
                        complete_url = 'http://' + str(self._domain) + url
                        http_handler = HTTPRequestHandler(proxies=proxies, retries=retries, timeout=timeout)
                        response = http_handler.send_http_request(method='get', url=complete_url)
                        if response is None:
                            break
                    if 'licence' in url:
                        count = 0
                        if str(response.status_code) == '200':
                            if 'WordPress - Web publishing software' in str(response.content):
                                count += 1
                            if 'WordPress is released under the GPL' in str(response.content):
                                count += 1
                            if 'The source code for any program binaries or compressed scripts that are' in str(
                                    response.content) and \
                                    'included with WordPress can be freely obtained at the following URL:' \
                                    in str(response.content):
                                count += 1
                            if 3 >= count >= 2:
                                response_list.append(self.get_version(response.content, url))
                    if 'readme' in url:
                        if str(response.status_code) == '200':
                            if 'wordpress-logo.png' in str(response.content):
                                response_list.append((True, "Could'nt detect version"))
                            response_list.append((False, "Could'nt detect version"))
                    if 'feed' in url:
                        if str(response.status_code) == '200':
                            response_list.append(self.get_version(response.content, url))
                    if 'wp-links-opml' in url:
                        response_list.append(self.get_version(response.content, url))
                    if 'upgrade' in url:
                        if 'wordpress-logo.png' in str(response.content):
                            response_list.append((True, "Could'nt detect version"))
                        response_list.append((False, "Could'nt detect version"))
                    if 'admin' in url:
                        count = 0
                        if 'wp-content' in str(response.content):
                            count += 1
                        elif 'wordpress' in str(response.content):
                            count += 1
                        if 'wp-admin' in str(response.content):
                            count += 1
                        if 'wp-includes' in str(response.content):
                            count += 1
                        if 'wp-json' in str(response.content):
                            count += 1
                        if 5 >= count >= 3:
                            response_list.append((True, "Could'nt detect version"))
                        response_list.append(self.get_version(response.content, url + '/wp-admin'))
                    if 'robots' in url:
                        if ('wp-admin' or 'WP rules' or 'wordpress rules' or 'wp-includes') in str(response.content):
                            response_list.append((True, "Could'nt detect version"))
                        response_list.append((False, "Could'nt detect version"))
                response_list += self.is_wordpress_no_url(proxies=proxies, timeout=timeout, retries=retries)
            possible_outcomes = []
            is_word_press = False
            for item in response_list:
                if item[0]:
                    possible_outcomes.append(item)
            for outcome in possible_outcomes:
                if outcome[0]:
                    is_word_press = True
                if 'version' not in outcome[1]:
                    return outcome
            if is_word_press:
                return True, "Could'nt detect version"
            return False, "Could'nt detect version"
        except Exception as e:
            print(e)

    def get_version(self, data=None, url=None):
        """
        detects the version of the wordpress
        :param data: The answer of the http request
        :param url: the suffix of the url that got the response of data
        :return: a tuple: (whether the domain operates over Wordpress, version)
        """
        try:
            if not (data and url):
                return self.__get_version_standalone()
            if not (data or url):
                return True, "Could'nt detect version"
            else:
                return self.__detect_version_logic(data, url)
        except Exception as e:
            print(e)

    def __detect_version_logic(self, data, url):
        """
        detects the version of the wordpress
        :param data: The answer of the http request
        :param url: the suffix of the url that got the response of data
        :return: a tuple: (whether the domain operates over Wordpress, doesn't return the version)
        """
        try:
            if "wp-admin" in str(url):
                start_index = str(data).find('"name="generator" content="WordPress"')
                if start_index != -1:
                    end = data.find("'", start_index)
                    version = data[start_index + 38:end]
                    for letter in version:
                        if not (str(letter).isdigit() or str(letter) == '.'):
                            return True, "Could'nt detect version"
                    return True, version
                return False, "Could'nt detect version"

            elif "feed" in str(url):
                version = None
                if 'atom' in url:
                    start_index = str(data).find('wordpress.org/" version="')
                    if start_index != -1:
                        end = str(data).find('"', start_index + 25)
                        version = str(data)[start_index + 25:end]
                else:
                    start_index = str(data).find('?v=')
                    if start_index != -1:
                        end = str(data).find("<", start_index)
                        version = str(data)[start_index + 3:end]
                if version is not None:
                    for letter in version:
                        if not (str(letter).isdigit() or str(letter) == '.'):
                            return True, "Could'nt detect version"
                    return True, version
            elif "wp-links-opml" in str(url):
                start_index = str(data).find('generator="WordPress/')
                if start_index != -1:
                    end = str(data).find('"', start_index)
                    version = data[start_index + 7:end]
                    version = str(version).split("\'")[1]
                    for letter in str(version):
                        if not (str(letter).isdigit() or str(letter) == '.'):
                            return True, "Could'nt detect version"
                    return True, version
                return False, "Could'nt detect version"

            return False, "Could'nt detect version"
        except Exception as e:
            print(e)

    def __get_version_standalone(self):
        """
        detects the version of the wordpress
        :return: a list of tuples: [(whether the domain operates over Wordpress, doesn't return the version),..]
        """
        try:
            response_list = []
            for url in _VERSION_DETECTABLE_URLS:
                complete_url_https = 'https://' + str(self._domain) + url
                complete_url_http = 'http://' + str(self._domain) + url
                http_handler = HTTPRequestHandler(proxies=self._proxies, retries=0, timeout=5)
                response = http_handler.send_http_request(method='get', url=complete_url_https)
                if response is None:
                    response = http_handler.send_http_request(method='get', url=complete_url_http)
                response_list.append(self.__detect_version_logic(response.content, url))
            possible_outcomes = []
            outcome = None
            for item in response_list:
                if item[0]:
                    possible_outcomes.append(item)
            for outcome in possible_outcomes:
                if 'version' not in outcome[1]:
                    return outcome
            return outcome
        except Exception as e:
            print(e)
