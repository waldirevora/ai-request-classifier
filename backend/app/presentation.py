"""Public, non-secret portfolio metadata. Contact is explicit configuration only."""
import os
from urllib.parse import urlsplit
from fastapi import APIRouter,Request
from app.ai_control import configuration_error

router=APIRouter(prefix='/v2',tags=['Apresentação'])

@router.get('/presentation')
def presentation(request:Request):
    contact=os.getenv('SF_CONTACT_URL','').strip()
    try:parts=urlsplit(contact)
    except ValueError:parts=urlsplit('');contact=''
    if any(ord(char)<32 for char in contact):contact=''
    if not (parts.scheme in ('https','mailto') and not parts.username and not parts.password and not parts.query and not parts.fragment):contact=''
    if parts.scheme=='https' and not parts.netloc:contact=''
    if parts.scheme=='mailto' and ('@' not in parts.path or '\n' in parts.path):contact=''
    test_mode=os.getenv('SF_QA_MODE')=='true' and (os.getenv('PGDATABASE')=='ai_request_classifier_test' or os.getenv('GITHUB_ACTIONS')=='true')
    return {'public_demo':getattr(request.app.state,'public_demo',False),'contact_url':contact or None,'test_mode':test_mode,'ai_available':configuration_error() is None}
