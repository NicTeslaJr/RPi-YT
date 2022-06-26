import re
import json
import subprocess
import youtube_dl

from datetime import datetime
from subprocess import CalledProcessError

class MediaPlayer():

    nowPlaying = {
        'title': None,
        'webpage_url': None,
        'duration': None,
        'view_count': None,
        'thumbnail_url': None,
        'uploader': None,
        'channel_url': None,
        'start_time': None,
    }

    cmd_mpv_play = None

    @classmethod
    def resetNowPlaying(cls):
        cls.cmd_mpv_play = None
        cls.nowPlaying['title'] = None
        cls.nowPlaying['webpage_url'] = None
        cls.nowPlaying['duration'] = None
        cls.nowPlaying['view_count'] = None
        cls.nowPlaying['thumbnail_url'] = None
        cls.nowPlaying['uploader'] = None
        cls.nowPlaying['channel_url'] = None
        cls.nowPlaying['start_time'] = None
    
    @classmethod
    def sysGetVolume(cls):
        cmd_amixer_get = subprocess.run([
            '/usr/bin/amixer', 'get', 'Headphone'
        ], capture_output=True, text=True)
        return int(re.search(r'\[([0-9]*)%\]', cmd_amixer_get.stdout).groups()[0])
    
    @classmethod
    def sysSetVolume(cls, step: int, mute: bool=False):
        cmd_amixer_set = subprocess.run([
            '/usr/bin/amixer', 'set', 'Headphone', '--', f'{cls.sysGetVolume() + step if not mute else 0}%'
        ], capture_output=True, text=True)
        return int(re.search(r'\[([0-9]*)%\]', cmd_amixer_set.stdout).groups()[0])
    
    @classmethod
    def mpvGetNowPlaying(cls):
        if cls.cmd_mpv_play:
            returncode = cls.cmd_mpv_play.poll()
            if returncode is not None:
                cls.resetNowPlaying()
                return (False, cls.nowPlaying)
            return (True, cls.nowPlaying)
        return (False, cls.nowPlaying)
    
    @classmethod
    def mpvPlay(cls, query: str):
        # TODO: cmd_mpv_play.wait()/poll() here? will help in queue?
        ytdl_opts = {
            'default_search': 'ytsearch',
            'quiet': True,
            'warnings': 'no-warnings'
        }
        with youtube_dl.YoutubeDL(ytdl_opts) as ytdl:
            info = ytdl.extract_info(query, download=False)

        cls.nowPlaying['title'] = info['entries'][0]['title']
        cls.nowPlaying['webpage_url'] = info['entries'][0]['webpage_url']
        cls.nowPlaying['duration'] = info['entries'][0]['duration']
        cls.nowPlaying['view_count'] = info['entries'][0]['view_count']
        cls.nowPlaying['thumbnail_url'] = info['entries'][0]['thumbnails'][0]['url']
        cls.nowPlaying['uploader'] = info['entries'][0]['uploader']
        cls.nowPlaying['channel_url'] = info['entries'][0]['channel_url']
        cls.nowPlaying['start_time'] = str(datetime.now())

        # TODO: can we get progress from cmd_mpv_play.communicate() ? or something similar?
        cls.cmd_mpv_play = subprocess.Popen([
            '/usr/bin/mpv', '--no-video', '--no-terminal', '--input-ipc-server=/tmp/mpvsocket_rpi-yt', cls.nowPlaying['webpage_url']
        ], stdout=subprocess.DEVNULL)
        
        return (True, cls.nowPlaying)
    
    @classmethod
    def mpvTogglePause(cls):
        cmd_mpv_toggle_pause = subprocess.run([
            '/usr/bin/socat', '-', '/tmp/mpvsocket_rpi-yt'
        ], input='cycle pause\n', capture_output=True, text=True)
        try:
            cmd_mpv_toggle_pause.check_returncode()
        except CalledProcessError:
            return (False, cmd_mpv_toggle_pause)
        cmd_mpv_pause_property = subprocess.run([
            '/usr/bin/socat', '-', '/tmp/mpvsocket_rpi-yt'
        ], input='{ "command": ["get_property", "pause"] }\n', capture_output=True, text=True)
        return (True, json.loads(cmd_mpv_pause_property.stdout[:-1])['data'])
    
    @classmethod
    def mpvQuit(cls):
        cmd_mpv_quit = subprocess.run([
            '/usr/bin/socat', '-', '/tmp/mpvsocket_rpi-yt'
        ], input='quit\n', capture_output=True, text=True)
        try:
            cmd_mpv_quit.check_returncode()
        except CalledProcessError:
            return (False, cmd_mpv_quit)
        cls.resetNowPlaying()
        return (True, cmd_mpv_quit)