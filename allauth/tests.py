# -*- coding: utf-8 -*-

import requests
from django.test import TestCase
from django.core.exceptions import ValidationError
from models import BannedUsername

import utils

class MockedResponse(object):
    def __init__(self, status_code, content, headers={}):
        self.status_code = status_code
        self.content = content
        self.headers = headers

    def json(self):
        import json
        return json.loads(self.content)

class mocked_response:
    def __init__(self, *responses):
        self.responses = list(responses)

    def __enter__(self):
        self.orig_get = requests.get
        self.orig_post = requests.post

        def mockable_request(f):
            def new_f(*args, **kwargs):
                if self.responses:
                    return self.responses.pop(0)
                return f(*args, **kwargs)
            return new_f
        requests.get = mockable_request(requests.get)
        requests.post = mockable_request(requests.post)

    def __exit__(self, type, value, traceback):
        requests.get = self.orig_get
        requests.post = self.orig_post

class BasicTests(TestCase):

    def test_generate_unique_username(self):
        examples = [('a.b-c@gmail.com', 'a.b-c'),
                    (u'Üsêrnamê', 'username'),
                    ('', 'user')]
        for input, username in examples:
            self.assertEquals(utils.generate_unique_username(input),
                              username)

    def test_email_validation(self):
        s = 'unfortunately.django.user.email.max_length.is.set.to.75.which.is.too.short@bummer.com'
        self.assertEquals(None, utils.valid_email_or_none(s))
        s = 'this.email.address.is.a.bit.too.long.but.should.still.validate.ok@short.com'
        self.assertEquals(s, utils.valid_email_or_none(s))
        s = 'x' + s
        self.assertEquals(None, utils.valid_email_or_none(s))
        self.assertEquals(None, utils.valid_email_or_none("Bad ?"))

    def test_creating_and_saving_bannedusernames(self):
        banned_username = BannedUsername()
        banned_username.expression = 'account'
        banned_username.save()

        # Retrieve it
        all_bu = BannedUsername.objects.all()
        self.assertEquals(len(all_bu), 1)
        only_bu = all_bu[0]
        self.assertEquals(only_bu, banned_username)

        # Check if the fields are the same
        self.assertEquals(banned_username.expression, only_bu.expression)

    def test_bannedusername_validation(self):
        bad_bu = BannedUsername()
        bad_bu.expression = '('
        try:
            bad_bu.full_clean()
            self.fail('Validation not working')
        except ValidationError:
            pass
