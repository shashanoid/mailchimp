# -*- coding: utf-8 -*-
import json
import os
import sys

from flask import Flask, make_response, request
from mailchimp3 import MailChimp


class Handler:
    app = Flask(__name__)
    
    def __init__(self) -> None:
     self.client = MailChimp(mc_api=os.getenv('API_KEY'), mc_user=os.getenv('USERNAME'))
    
    def add_to_list(self):
     req = request.get_json()
     list_name = req['list_name']
     user_email = req['user_email']
     status = req['status']
     first_name = req['first_name']
     last_name = req['last_name']
     try:
      list_id = self.get_list_id(list_name)
     except Exception as e:
      return self.end({'success': False, 'error': str(e)})

     try:
       self.client.lists.members.create(list_id, {
       'email_address': user_email,
       'status': status,
       'merge_fields': {
       'FNAME': first_name,
       'LNAME': last_name,
       },})
       return self.end({'success': True})
     except Exception as e:
       return self.end({'success': False, 'error_code': e.args[0]['status'], 'error': e.args[0]['detail']})
    
      
      
    def delete_from_list(self):
     req = request.get_json()
     list_name = req['list_name']
     user_email = req['user_email']
     try:
      list_id = self.get_list_id(list_name)
     except Exception as e:
      return self.end({'success': False, 'error_code': 404, 'error': str(e)})
     try:
      user_id = self.get_user_id(list_id, user_email)
     except Exception as e:
      return self.end({'success': False, 'error_code': 404, 'error': str(e)})
   
     try:
       self.client.lists.members.delete(list_id, user_id)
       return self.end({'success': True})
     except Exception as e:
       return self.end({'success': False, 'error_code': e.args[0]['status'], 'error': e.args[0]['detail']})
        
    def add_tags(self):
     req = request.get_json()
     list_name = req['list_name']
     user_email = req['user_email']
     tag_name = req['tag']
     data = {'tags': [{'name': tag_name, 'status': 'active'}]}
     try:
      list_id = self.get_list_id(list_name)
     except Exception as e:
      return self.end({'success': False,'error_code': 404,'error': str(e)})
     try:
      user_id = self.get_user_id(list_id, user_email)
     except Exception as e:
      return self.end({'success': False,'error_code': 404,'error': str(e)})
     
     try:
       self.client.lists.members.tags.update(list_id, user_id, data)
       return self.end({'success': True})
     except Exception as e:
       return self.end({'success': False, 'error_code': e.args[0]['status'], 'error': e.args[0]['detail']})
    
      
    
    def update_subscriber(self):
     req = request.get_json()
     list_name = req['list_name']
     user_email = req['user_email']      
     try:
      list_id = self.get_list_id(list_name)
     except Exception as e:
      return self.end({'success': False,'error_code': 404,'error': str(e)})
     try:
      user_id = self.get_user_id(list_id, user_email)
     except Exception as e:
      return self.end({'success': False,'error_code': 404,'error': str(e)})
     data = {}
     merge_field_data = {}
   
     key_map = {
       'status': 'status',
       'first_name': 'FNAME', 
       'last_name': 'LNAME',
       'new_email': 'email_address',
       'address': 'ADDRESS',
       'phone': 'PHONE'
     }
   
     merge_field_exclusive = ['first_name', 'last_name', 'address', 'phone']
   
     for key, val in req.items():
       if key and key != 'list_name' and key != 'user_email' and key not in merge_field_exclusive:
         data.update({key_map[key]:val})
       elif key and key != 'list_name' and key != 'user_email':
         merge_field_data.update({key_map[key]:val})
   
     data.update({'merge_fields': merge_field_data})
   
     try:
       self.client.lists.members.update(list_id, user_id, data)
       return self.end({'success': True})
     except Exception as e:
       return self.end({'success': False, 'error_code': e.args[0]['status'], 'error': e.args[0]['detail']})

    # Helper Functions 
    def get_list_id(self, list_name):
     found = False
     for x in self.client.lists.all(get_all=True, fields="lists.name,lists.id")['lists']:
       if(x['name'] == list_name):
         return x['id']
         found = True
     
     if not found:
      raise Exception('Invalid List Name')


    def get_user_id(self, list_id, user_email):
     found = False
     for x in self.client.lists.members.all(list_id, get_all=True, \
       fields="members.email_address,members.id")['members']:
       if (x['email_address'] == user_email):
         return x['id']
         found = True
     if not found:
      raise Exception("User not found !")


    def end(self, res):
     resp = make_response(json.dumps(res))
     resp.headers['Content-Type'] = 'application/json; charset=utf-8'
     return resp


if __name__ == '__main__':
  if os.getenv('API_KEY') is None or os.getenv('USERNAME') is None:
    print('API Key and Username not found')
    sys.exit(1)

  handler = Handler()
  handler.app.add_url_rule('/add', 'add', handler.add_to_list, methods=['post'])
  handler.app.add_url_rule('/delete', 'delete', handler.delete_from_list, methods=['post'])
  handler.app.add_url_rule('/addtag', 'addtag', handler.add_tags, methods=['post'])
  handler.app.add_url_rule('/updatesubscriber', 'updatesubscriber', handler.update_subscriber, \
  methods=['post'])

  handler.app.run(host='0.0.0.0', port=8000)
