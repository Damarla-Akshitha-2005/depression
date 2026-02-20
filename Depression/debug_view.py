
import os
import sys
import django
from django.conf import settings
from django.template import Context, Template
from django.http import HttpRequest

# Setup Django environment
sys.path.append(r'c:\Users\dhema\Downloads\DEPRESSION DETECTION USING ECG\Depression')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Depression.settings')
django.setup()

from DepressionApp import views

# Mock request
request = HttpRequest()
request.method = 'GET'

try:
    print("Testing MotivatedText view...")
    response = views.MotivatedText(request)
    print("View executed successfully.")
    print("Status Code:", response.status_code)
except Exception as e:
    print("Error executing view:")
    print(e)
