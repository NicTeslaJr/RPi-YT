from sanic import Sanic
from sanic.response import json
from sanic.blueprints import Blueprint

from mediaplayer import MediaPlayer as mp

app = Sanic('RPi-YT')

mpvc = Blueprint('mpvControl', url_prefix='/mpv')
sysc = Blueprint('sysControl', url_prefix='/sys')
cgrp = Blueprint.group([mpvc, sysc], url_prefix='/api')

@sysc.get('/getVolume')
async def sys_get_volume(request):
    return json({
        'status': True,
        'code': 200,
        'data': {
            'currVol': mp.sysGetVolume()
        }
    })

@sysc.get('/changeVolume')
async def sys_change_volume(request):
    try:
        control = request.args.get('control')
        if control not in ['up', 'down', 'mute']: raise ValueError
        if control != 'mute': step = abs(int(request.args.get('step')))
    except (TypeError, ValueError):
        return json({
            'status': False,
            'code': 400,
            'data': {
                'message': f'Bad Request. Expected Endpoint: {app.url_for("sysControl.sys_change_volume")}?control={{up|down|mute}}&step={{int}}'
            }
        }, status=400)
    if control == 'mute':
        currVol = mp.sysSetVolume(0, mute=True)
    elif control == 'down':
        currVol = mp.sysSetVolume(-step)
    else:
        currVol = mp.sysSetVolume(step)
    return json({
        'status': True,
        'code': 200,
        'data': {
            'currVol': currVol  
        }
    })

@mpvc.get('/getNowPlaying')
async def mpv_now_playing(request):
    mpvNowPlaying = mp.mpvGetNowPlaying()
    return json({
        'status': True,
        'code': 200,
        'data': {
            'isPlaying': True if mpvNowPlaying[0] else False,
            'mediaInfo': mpvNowPlaying[1]
        }
    })

@mpvc.get('/play')
async def mpv_play(request):
    try:
        query = request.args.get('q')
        if not query: raise ValueError
    except ValueError:
        return json({
            'status': False,
            'code': 400,
            'data': {
                'message': f'Bad Request. Expected Endpoint: {app.url_for("mpvControl.mpv_play")}?q={{str}}'
            }
        }, status=400)
    nowPlaying = mp.mpvPlay(query)
    return json({
        'status': True,
        'code': 200,
        'data': {
            'mediaInfo': nowPlaying[1]
        }
    })

@mpvc.get('/directPlay')
async def mpv_direct_play(request):
    try:
        query = request.args.get('q')
        if not query: raise ValueError
    except ValueError:
        return json({
            'status': False,
            'code': 400,
            'data': {
                'message': f'Bad Request. Expected Endpoint: {app.url_for("mpvControl.mpv_direct_play")}?q={{str}}'
            }
        }, status=400)
    nowPlaying = mp.mpvDirectPlay(query)
    return json({
        'status': True,
        'code': 200,
        'data': {
            'mediaInfo': nowPlaying[1]
        }
    })

@mpvc.get('/search')
async def ytdl_search(request):
    try:
        limit = abs(int(request.args.get('limit')))
        query = request.args.get('q')
        if not query: raise ValueError
    except (TypeError, ValueError):
        return json({
            'status': False,
            'code': 400,
            'data': {
                'message': f'Bad Request. Expected Endpoint: {app.url_for("mpvControl.ytdl_search")}?q={{str}}&limit={{int}}'
            }
        }, status=400)
    results = mp.ytdlSearch(query, limit)
    return json({
        'status': True,
        'code': 200,
        'data': {
            'results': results
        }
    })

@mpvc.get('/resume')
@mpvc.get('/pause')
async def mpv_pause(request):
    pause_tup = mp.mpvTogglePause()
    if not pause_tup[0]:
        return json({
            'status': False,
            'code': 500,
            'data': {
                'message': 'subprocess.CalledProcessError (Maybe mpv not running?)',
                'stderr': pause_tup[1].stderr,
                'stdout': pause_tup[1].stdout,
                'returncode': pause_tup[1].returncode
            }
        }, status=500)
    else:
        return json({
            'status': True,
            'code': 200,
            'data': {
                'isPaused': pause_tup[1],
                'message': 'Player Paused/Resumed'
            }
        })

@mpvc.get('/quit')
async def mpv_quit(request):
    quit_tup = mp.mpvQuit()
    if not quit_tup[0]:
        return json({
            'status': False,
            'code': 500,
            'data': {
                'message': 'subprocess.CalledProcessError (Maybe mpv not running?)',
                'stderr': quit_tup[1].stderr,
                'stdout': quit_tup[1].stdout,
                'returncode': quit_tup[1].returncode
            }
        }, status=500)
    else:
        return json({
            'status': True,
            'code': 200,
            'data': {
                'message': 'MPV Quit.'
            }
        })

app.blueprint(cgrp)