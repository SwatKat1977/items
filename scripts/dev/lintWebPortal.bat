@echo off
set PYTHONPATH=services/web_portal_svc;items/shared;common
pylint services/web_portal_svc
