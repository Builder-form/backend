import ssl

import requests

from ..base import SMSProvider


class Megafon(SMSProvider):
    token = 'eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJRV05sMENiTXY1SHZSV29CVUpkWjVNQURXSFVDS0NWODRlNGMzbEQtVHA0In0.eyJleHAiOjIwMDc1MzY3ODYsImlhdCI6MTY5MjE3Njc4NiwianRpIjoiZTFmMGZhMWQtMDk5Zi00NGU3LWJlZWItMjk3Mjk3MGZlZTJkIiwiaXNzIjoiaHR0cHM6Ly9zc28uZXhvbHZlLnJ1L3JlYWxtcy9FeG9sdmUiLCJhdWQiOiJhY2NvdW50Iiwic3ViIjoiYzIxM2Y4MzktNzM3Mi00OWNiLTk0NWUtZTAzNWUwZTNkOTNmIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiNzUwYzExMmItNmY0MS00NmE1LWEyOTAtNTQzYmZhNWY0Nzc0Iiwic2Vzc2lvbl9zdGF0ZSI6IjlmOTY5NDkxLWUyZTgtNDE5Yi1hNmI2LTI1NTNmNGMyNjk4YyIsImFjciI6IjEiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsiZGVmYXVsdC1yb2xlcy1leG9sdmUiLCJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJleG9sdmVfYXBwIHByb2ZpbGUgZW1haWwiLCJzaWQiOiI5Zjk2OTQ5MS1lMmU4LTQxOWItYTZiNi0yNTUzZjRjMjY5OGMiLCJ1c2VyX3V1aWQiOiJiNjUwZDY1MC0wZTY2LTQ1ODYtOWYzMy01ZGIyNWQ4MTMwNTEiLCJjbGllbnRJZCI6Ijc1MGMxMTJiLTZmNDEtNDZhNS1hMjkwLTU0M2JmYTVmNDc3NCIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwiY2xpZW50SG9zdCI6IjE3Mi4yMC4yLjIxIiwiYXBpX2tleSI6dHJ1ZSwiYXBpZm9uaWNhX3NpZCI6Ijc1MGMxMTJiLTZmNDEtNDZhNS1hMjkwLTU0M2JmYTVmNDc3NCIsImJpbGxpbmdfbnVtYmVyIjoiMTIwMjQ1NCIsImFwaWZvbmljYV90b2tlbiI6ImF1dDk2Yzc5MjI1LTdhZDktNDBlNy04YmY0LWY5YjkwMWM4ODJmZSIsInByZWZlcnJlZF91c2VybmFtZSI6InNlcnZpY2UtYWNjb3VudC03NTBjMTEyYi02ZjQxLTQ2YTUtYTI5MC01NDNiZmE1ZjQ3NzQiLCJjdXN0b21lcl9pZCI6IjI4MzYxIiwiY2xpZW50QWRkcmVzcyI6IjE3Mi4yMC4yLjIxIn0.E7x4rUI1s3nb0saYRcE3h7hte89yDwEqLf2JewitgwyKsigfdwERWNfXOk9dm4pfmlYpwLiNm-BGhEiG41D1BX6pTTQ9jGLk48VxDkDbHeCWcThSZ2DrUNF5V3SoO6fGp9Tmgl9BiDZMJ_CSNN8cFQkkVO5PArDbVxzU7aoTtVlbxzWEI2sqFn1cU1iREKKLC3w15O9IOpM-pBMaPBT_vmCdZ_8UVBa8CD4MF4gMcdOemi8DUy3qqAdTpOvbjqP-cpNB9yhAuEqzUYE9Yb8T7yoJgNrCTKovszoINbMCBdUcFtljbSaRYisyVuI_c-nS9mePbTXaMY0Wlx9kwzdPIw'
    def _prepare_headers(self):
        if hasattr(ssl, "_create_unverified_context"):
            ssl._create_default_https_context = ssl._create_unverified_context

    def send_megafon_sms(self):
        self._prepare_headers()

        url = "https://api.exolve.ru/messaging/v1/SendSMS"
        
        payload = "{\n   \"number\": \"" + self.conf.SMS_PROVIDER_FROM + "\",\n   \"destination\": \"" +  str(self.to)[1:] + "\",\n   \"text\": \"" +  self.message+ "\"\n}"
        
        headers = {
        'Content-Type': 'text/plain',
        'Authorization': 'Bearer '+ self.token
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        return response

    def send_sms(self):
        # return ''
        return self.send_megafon_sms()
