# Copyright 2013 John Reese
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import uuid

from flask import g, request, session

from core import app, mc, mcdict 
from models import User

def destroy():
    """Delete the current session from memcache."""
    if 'session-key' in session:
        mc.delete(session['session-key'])

def new():
    """Generate a new session, and remove the old session from memcache."""
    destroy()

    session_key = 'session-' + uuid.uuid4().hex

    g.session = mcdict(session_key)
    g.session['remote_addr'] = request.remote_addr
    g.session['user_agent'] = str(request.user_agent)

    session['session-key'] = session_key

@app.before_request
def user_before_request():
    """Pull user data from session if found, or use anonymous user otherwise."""
    g.session = None
    g.user = None
    g.device = None

    if 'session-key' in session:
        session_key = session['session-key']
        if mc.get(session_key) is not None:
            g.session = mcdict(session_key)

    if g.session is not None:
        if ('remote_addr' in g.session and 'user_agent' in g.session and
            request.remote_addr != g.session['remote_addr'] and
            str(request.user_agent) != g.session['user_agent']):

            app.logger.warning('Potential session hijack detected: '
                               'remote_addr %s => %s, '
                               'user_agent "%s" => %s"',
                               g.session['remote_addr'], request.remote_addr,
                               g.session['user_agent'], str(request.user_agent),
                              )
            destroy()
            g.session = None

    if g.session is None:
        new()

    if 'user' not in g.session:
        g.session['user'] = User()
    g.user = g.session['user']

    if g.user.id == None:
        g.account_links = [
            {'href': '/account/register', 'title': 'Register'},
            {'href': '/account/login', 'title': 'Login'},
        ]
    else:
        g.account_links = [
            {'href': '/account', 'title': g.user.email},
            {'href': '/account/logout', 'title': 'Logout'},
        ]
