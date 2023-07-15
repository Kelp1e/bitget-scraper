import os


def get_correct_format(data):
    result = []

    for proxy in data:
        proxy_list = proxy.split(":")

        login = proxy_list[-2]
        password = proxy_list[-1]
        ip = f"{proxy_list[0]}:{proxy_list[1]}"

        correct_string = f"{login}:{password}@{ip}"

        result.append(correct_string)

    return result


def get_proxies():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    proxies_file = os.path.join(current_dir, "proxies.txt")

    with open(proxies_file, "r") as file:
        data = file.read().split("\n")

        proxies = get_correct_format(data)

        return proxies
