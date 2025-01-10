import unittest
from flask import Flask
from io import BytesIO
from PIL import Image
import json

from app import app, collection

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Upload Images', response.data)

    def test_upload_single_image(self): 
        image = Image.new("RGB", (100, 100), color="white")
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)
        
        data = {
            'images': (img_byte_arr, 'test_image.png')
        }
        
        response = self.client.post('/upload', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 500)  

   
    def test_upload_multiple_images(self):
        image1 = Image.new("RGB", (100, 100), color="white")
        img_byte_arr1 = BytesIO()
        image1.save(img_byte_arr1, format="PNG")
        img_byte_arr1.seek(0)
        
        image2 = Image.new("RGB", (100, 100), color="white")
        img_byte_arr2 = BytesIO()
        image2.save(img_byte_arr2, format="PNG")
        img_byte_arr2.seek(0)

        data = {
            'images': [
                (img_byte_arr1, 'test_image1.png'),
                (img_byte_arr2, 'test_image2.png')
            ]
        }
        
        response = self.client.post('/upload', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 302)# Redirect to search record page

    def test_upload_no_images(self):
        response = self.client.post('/upload', data={}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'No images provided', response.data)

    def test_search_get(self):
        response = self.client.get('/search')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Search Extracted Data', response.data)  

    
    def test_search_post(self):
        mock_data = {
            "company_name": "Test Corp",
            "name": "John Doe",
            "profession": "Software Developer",
            "email": "johndoe@example.com",
            "address": "123 Test St",
            "phone_number": "+1234567890",
            "website": "www.test.com"
        }
        collection.insert_one(mock_data)
        
        response = self.client.post('/search', data={'search_query': 'Test Corp'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Corp', response.data)

    def test_search_no_results(self):
        response = self.client.post('/search', data={'search_query': 'Nonexistent Company'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'No matching records found.', response.data)  
    def test_search_missing_query(self):
        response = self.client.post('/search', data={'search_query': ''})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Please provide a keyword to search', response.data)

if __name__ == '__main__':
    unittest.main()
