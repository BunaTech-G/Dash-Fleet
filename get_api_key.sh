#!/bin/bash
cd /opt/dashfleet
sqlite3 data/fleet.db 'SELECT key FROM api_keys WHERE revoked=0 LIMIT 1;'
