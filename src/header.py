import os


def get_headers():
    return {
        "Authorization": "Basic " + os.environ['GITHUB_TOKEN'],
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
