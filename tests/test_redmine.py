from tests import unittest, mock, json_response, Redmine, URL


class TestRedmine(unittest.TestCase):
    def setUp(self):
        self.url = URL
        self.redmine = Redmine(self.url)

    def test_default_attributes(self):
        self.assertEqual(self.redmine.url, self.url)
        self.assertEqual(self.redmine.key, None)
        self.assertEqual(self.redmine.ver, None)
        self.assertEqual(self.redmine.username, None)
        self.assertEqual(self.redmine.password, None)
        self.assertEqual(self.redmine.requests, {})
        self.assertEqual(self.redmine.impersonate, None)
        self.assertEqual(self.redmine.date_format, '%Y-%m-%d')
        self.assertEqual(self.redmine.datetime_format, '%Y-%m-%dT%H:%M:%SZ')
        self.assertEqual(self.redmine.raise_attr_exception, True)
        self.assertEqual(self.redmine.custom_resource_paths, None)

    def test_set_attributes_through_kwargs(self):
        self.redmine = Redmine(
            self.url,
            key='123',
            version='1.0',
            username='john',
            password='qwerty',
            impersonate='jsmith',
            date_format='format',
            datetime_format='format',
            requests={'foo': 'bar'},
            raise_attr_exception=False,
            custom_resource_paths='foo.bar.baz'
        )
        self.assertEqual(self.redmine.url, self.url)
        self.assertEqual(self.redmine.key, '123')
        self.assertEqual(self.redmine.ver, '1.0')
        self.assertEqual(self.redmine.username, 'john')
        self.assertEqual(self.redmine.password, 'qwerty')
        self.assertEqual(self.redmine.impersonate, 'jsmith')
        self.assertEqual(self.redmine.date_format, 'format')
        self.assertEqual(self.redmine.datetime_format, 'format')
        self.assertEqual(self.redmine.requests['foo'], 'bar')
        self.assertEqual(self.redmine.raise_attr_exception, False)
        self.assertEqual(self.redmine.custom_resource_paths, 'foo.bar.baz')


class TestRedmineRequest(unittest.TestCase):
    def setUp(self):
        self.url = URL
        self.redmine = Redmine(self.url)
        self.response = mock.Mock()
        patcher_get = mock.patch('requests.get', return_value=self.response)
        patcher_post = mock.patch('requests.post', return_value=self.response)
        patcher_put = mock.patch('requests.put', return_value=self.response)
        patcher_get.start()
        patcher_post.start()
        patcher_put.start()
        self.addCleanup(patcher_get.stop)
        self.addCleanup(patcher_post.stop)
        self.addCleanup(patcher_put.stop)

    def test_successful_response_via_username_password(self):
        self.redmine.username = 'john'
        self.redmine.password = 'qwerty'
        self.response.status_code = 200
        self.response.json = json_response({'success': True})
        self.assertEqual(self.redmine.request('get', self.url)['success'], True)

    def test_successful_response_via_api_key(self):
        self.redmine.key = '123'
        self.response.status_code = 200
        self.response.json = json_response({'success': True})
        self.assertEqual(self.redmine.request('get', self.url)['success'], True)

    def test_successful_response_via_put_method(self):
        self.response.status_code = 200
        self.response.content = ''
        self.assertEqual(self.redmine.request('put', self.url), True)

    @mock.patch('redmine.open', mock.mock_open(), create=True)
    def test_successful_file_upload(self):
        self.response.status_code = 201
        self.response.json = json_response({'upload': {'token': '123456'}})
        self.assertEqual(self.redmine.upload('foo'), '123456')

    def test_file_upload_no_file_exception(self):
        from redmine.exceptions import NoFileError
        self.assertRaises(NoFileError, lambda: self.redmine.upload('foo',))

    def test_file_upload_not_supported_exception(self):
        from redmine.exceptions import VersionMismatchError
        self.redmine.ver = '1.0.0'
        self.assertRaises(VersionMismatchError, lambda: self.redmine.upload('foo',))

    def test_conflict_error_exception(self):
        from redmine.exceptions import ConflictError
        self.response.status_code = 409
        self.assertRaises(ConflictError, lambda: self.redmine.request('put', self.url))

    def test_auth_error_exception(self):
        from redmine.exceptions import AuthError
        self.response.status_code = 401
        self.assertRaises(AuthError, lambda: self.redmine.request('get', self.url))

    def test_impersonate_error_exception(self):
        from redmine.exceptions import ImpersonateError
        self.redmine.impersonate = 'not_exists'
        self.response.status_code = 412
        self.assertRaises(ImpersonateError, lambda: self.redmine.request('get', self.url))

    def test_server_error_exception(self):
        from redmine.exceptions import ServerError
        self.response.status_code = 500
        self.assertRaises(ServerError, lambda: self.redmine.request('post', self.url))

    def test_request_entity_too_large_error_exception(self):
        from redmine.exceptions import RequestEntityTooLargeError
        self.response.status_code = 413
        self.assertRaises(RequestEntityTooLargeError, lambda: self.redmine.request('post', self.url))

    def test_validation_error_exception(self):
        from redmine.exceptions import ValidationError
        self.response.status_code = 422
        self.response.json = json_response({'errors': ['foo', 'bar']})
        self.assertRaises(ValidationError, lambda: self.redmine.request('post', self.url))

    def test_not_found_error_exception(self):
        from redmine.exceptions import ResourceNotFoundError
        self.response.status_code = 404
        self.assertRaises(ResourceNotFoundError, lambda: self.redmine.request('get', self.url))

    def test_unknown_error_exception(self):
        from redmine.exceptions import UnknownError
        self.response.status_code = 888
        self.assertRaises(UnknownError, lambda: self.redmine.request('get', self.url))

    def test_auth(self):
        self.redmine.username = 'john'
        self.redmine.password = 'qwerty'
        self.response.status_code = 200
        self.response.json = json_response({'user': {'firstname': 'John', 'lastname': 'Smith', 'id': 1}})
        self.assertEqual(self.redmine.auth().firstname, 'John')
