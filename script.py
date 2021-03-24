import math
import os
import sys

import requests

r = requests.get("https://www.google.com")
print(r.status_code)
