
import os

if not os.environ.get('NO_EVENTLET_MONKEYPATCH'):
    import eventlet
    eventlet.monkey_patch(all=True, thread=True)
