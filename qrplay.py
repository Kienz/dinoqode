#!/usr/bin/env python
# coding: utf8

#
# Copyright (c) 2019 Stefan Kienzle
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import argparse
import json
import os
import subprocess
from time import sleep
import urllib.parse
import urllib.request
import http.client
import re
import traceback

try:
    use_blinkt = True
    import blinkt
except ImportError:
    use_blinkt = False


# Parse the command line arguments
arg_parser = argparse.ArgumentParser(description='Translates QR codes detected by a camera into Sonos® commands.')
arg_parser.add_argument('--default-volume', default='25', help='the volume of your default device')
arg_parser.add_argument('--default-device', default='Büro', help='the name of your default device/room')
arg_parser.add_argument('--hostname', default='0.0.0.0', help='the hostname or IP address of the machine running `node-sonos-http-api`')
arg_parser.add_argument('--skip-load', action='store_true', help='skip loading of the music library (useful if the server has already loaded it)', default=True)
arg_parser.add_argument('--debug-file', help='read commands from a file instead of launching scanner')
arg_parser.add_argument('--speak-welcome', action='store_true', help='should dinoqode speak welcome messages on startup', default=False)
args = arg_parser.parse_args()
print(args)

# Call http request
def perform_request(url):
    global last_qrcode_success

    print(url)
    try:
        response = urllib.request.urlopen(url)
        result = response.read().decode('utf-8')
        parsed_json = json.loads(result)

        try:
            if (parsed_json['status'] == 'error'):
                last_qrcode_success = False
            else:
                last_qrcode_success = True
        except KeyError:
            last_qrcode_success = True
            print('Key "status" not found in response - QRCode is marked as successful')

        print(result)
    except (IOError, http.client.HTTPException):
        print('Error')
        last_qrcode_success = False


# Perform global request (run on all rooms)
def perform_global_request(path):
    perform_request(base_url + '/' + path)

# Perform room specific request
def perform_room_request(path, room):
    qdevice = urllib.parse.quote(room)
    perform_request(base_url + '/' + qdevice + '/' + path)

# Switch to specific room and save the room in last-device file
def switch_to_room(room):
    global current_device
    last_qrcode = ''

    perform_room_request('pause', current_device)
    perform_room_request('volume/' + args.default_volume, room)
    current_device = room
    with open(".last-device", "w") as device_file:
        device_file.write(current_device)

# Perform speak command
def speak(phrase, room=None):
    if room is None:
        room = current_device

    print('SPEAKING: \'{0}\''.format(phrase))
    perform_room_request('say/' + urllib.quote(phrase) + '/de', room)

# Flash led lights (onboard or Blinkt! leds)
def blink_led(type):
    if use_blinkt == True:
        # Causes the Blinkt! led bar to blink
        if type == 'pulse-green':
            blinkt_subp = subprocess.Popen(["python3", os.path.join(current_dir, "blinkt_led_pulse.py"), "--brightness", "1", "--color", "0,128,0"])
            sleep(4)
        elif type == 'pulse-red':
            blinkt_subp = subprocess.Popen(["python3", os.path.join(current_dir, "blinkt_led_pulse.py"), "--brightness", "1", "--color", "255,0,0"])
            sleep(4)
        elif type == 'rainbow':
            blinkt_subp = subprocess.Popen(["python3", os.path.join(current_dir, "blinkt_led_rainbow.py")])
            sleep(4)

        blinkt_subp.kill()
        sleep(0.1)
        blinkt.clear()
        blinkt.show()

# Handling QR command
# If QR code is defined the Blinkt! led bar is flashing green otherwise red
def handle_command(qrcode):
    global current_playmode
    global last_qrcode_success

    room = current_device

    last_qrcode_success = True

    print('HANDLING COMMAND: ' + qrcode)

    if qrcode == 'cmd:playpause':
        perform_room_request('playpause', room)
        phrase = None

    elif qrcode == 'cmd:next':
        perform_room_request('next', room)
        perform_room_request('play', room)
        phrase = None

    elif qrcode == 'cmd:previous':
        perform_room_request('previous', room)
        phrase = None

    elif qrcode == 'cmd:queue':
        current_playmode = Mode.BUILD_QUEUE;
        phrase = None
        room = current_device

        with open(".last-playmode", "w") as playmode_file:
            playmode_file.write(current_playmode)

    elif qrcode == 'cmd:unqueue':
        current_playmode = Mode.PLAY_AND_CLEAR;
        phrase = None
        room = current_device
        perform_room_request('clearqueue', room)

        with open(".last-playmode", "w") as playmode_file:
            playmode_file.write(current_playmode)

    elif qrcode == 'cmd:playqueue':
        current_playmode = Mode.PLAY_AND_QUEUE;
        phrase = None
        room = current_device

        with open(".last-playmode", "w") as playmode_file:
            playmode_file.write(current_playmode)

    elif qrcode.startswith('cmd:room'):
        room = re.split('\\|', qrcode)[1]
        switch_to_room(room)
        phrase = None

    elif qrcode.startswith('cmd:say'):
        split = re.split('\\|', qrcode)
        room = split[1]
        phrase = split[2]

    elif len(qrcode.split(':')) == 3:
        split = re.split('\\:', qrcode)
        perform_room_request(split[1] + '/' + split[2], room)
        phrase = None
    else:
        last_qrcode_success = False

    if phrase:
        speak(phrase, room)


def handle_library_item(qrcode):
    if not qrcode.startswith('lib:'):
        return

    print('PLAYING FROM LIBRARY: ' + qrcode)

    search = re.split('\\|', qrcode)[1]

    if qrcode.startswith('lib:album'):
        action = 'album'
    else:
        action = 'song'

    perform_room_request('musicsearch/library/{0}/{1}'.format(action, urllib.quote(search)), current_device)


def handle_spotify_item(qrcode):
    print('PLAYING FROM SPOTIFY: ' + qrcode)

    if current_playmode == Mode.BUILD_QUEUE:
        action = 'queue'
    else:
        action = 'now'

    perform_room_request('spotify/{0}/{1}'.format(action, qrcode.replace('spotify:', '')), current_device)

def handle_applemusic_item(qrcode):
    print('PLAYING FROM APPLE MUSIC: ' + qrcode)

    if current_playmode == Mode.BUILD_QUEUE:
        action = 'queue'
    else:
        action = 'now'

    perform_room_request('applemusic/{0}/{1}'.format(action, qrcode.replace('applemusic:', '')), current_device)


def handle_amazonmusic_item(qrcode):
    print('PLAYING FROM AMAZON MUSIC: ' + qrcode)

    if current_playmode == Mode.BUILD_QUEUE:
        action = 'queue'
    else:
        action = 'now'

    perform_room_request('amazonmusic/{0}/{1}'.format(action, qrcode.replace('amazonmusic:', '')), current_device)

def handle_aldilife_item(qrcode):
    print('PLAYING FROM ALDI LIFE (NAPSTER): ' + qrcode)

    if current_playmode == Mode.BUILD_QUEUE:
        action = 'queue'
    else:
        action = 'now'

    perform_room_request('aldilifemusic/{0}/{1}'.format(action, qrcode.replace('aldilife:', '')), current_device)

def handle_napster_item(qrcode):
    print('PLAYING FROM NAPSTER: ' + qrcode)

    if current_playmode == Mode.BUILD_QUEUE:
        action = 'queue'
    else:
        action = 'now'

    perform_room_request('napster/{0}/{1}'.format(action, qrcode.replace('napster:', '')), current_device)

def handle_favorite_playlist_item(qrcode):
    print('PLAYING FROM SONOS FAVORITE/PLAYLIST: ' + qrcode)

    split = re.split('\\:', qrcode);

    perform_room_request('{0}/{1}'.format(split[0], urllib.quote(split[1])), current_device)


def handle_tunein_item(qrcode):
    print('PLAYING FROM TUNEIN: ' + qrcode)

    split = re.split('\\:', qrcode);

    perform_room_request('{0}/{1}/{2}'.format(split[0], split[1], split[2]), current_device)


def handle_qrcode(qrcode):
    global last_qrcode
    global last_qrcode_success

    # Ignore redundant codes, except for commands like "playpause", where you might
    # want to perform it multiple times
    if qrcode == last_qrcode and not qrcode.startswith('cmd:'):
        print('IGNORING REDUNDANT QRCODE: ' + qrcode)
        return

    print('HANDLING QRCODE: ' + qrcode)

    if qrcode.startswith('cmd:'):
        handle_command(qrcode)
    elif qrcode.startswith('applemusic:'):
        if current_playmode == Mode.PLAY_AND_CLEAR:
            perform_room_request('clearqueue', current_device)

        handle_applemusic_item(qrcode)
    elif qrcode.startswith('amazonmusic:'):
        if current_playmode == Mode.PLAY_AND_CLEAR:
            perform_room_request('clearqueue', current_device)

        handle_amazonmusic_item(qrcode)
    elif qrcode.startswith('spotify:'):
        if current_playmode == Mode.PLAY_AND_CLEAR:
            perform_room_request('clearqueue', current_device)

        handle_spotify_item(qrcode)
    elif qrcode.startswith('napster:'):
        if current_playmode == Mode.PLAY_AND_CLEAR:
            perform_room_request('clearqueue', current_device)

        handle_napster_item(qrcode)
    elif qrcode.startswith('aldilife:'):
        if current_playmode == Mode.PLAY_AND_CLEAR:
            perform_room_request('clearqueue', current_device)

        handle_aldilife_item(qrcode)
    elif qrcode.startswith('favorite:') or qrcode.startswith('playlist:'):
        if current_playmode == Mode.PLAY_AND_CLEAR:
            perform_room_request('clearqueue', current_device)

        handle_favorite_playlist_item(qrcode)
    elif qrcode.startswith('tunein:'):
        if current_playmode == Mode.PLAY_AND_CLEAR:
            perform_room_request('clearqueue', current_device)

        handle_tunein_item(qrcode)
    elif qrcode.startswith('lib'):
        if current_playmode == Mode.PLAY_AND_CLEAR:
            perform_room_request('clearqueue', current_device)

        handle_library_item(qrcode)
    else:
        last_qrcode_success = False

    if last_qrcode_success:
        last_qrcode = qrcode
        blink_led('pulse-green')
    else:
        last_qrcode = ''
        blink_led('pulse-red')


# Monitor the output of the QR code scanner.
def start_scan():
    while True:
        data = p.stdout.readline()

        if data:
            data = data.decode('utf-8').encode('sjis').decode('utf-8')

        qrcode = str(data)[8:]
        if qrcode:
            qrcode = qrcode.rstrip()
            handle_qrcode(qrcode)


# Read from the `debug.txt` file and handle one code at a time.
def read_debug_script():
    # Read codes from `debug.txt`
    with open(args.debug_file) as f:
        debug_codes = f.readlines()

    # Handle each code followed by a short delay
    for code in debug_codes:
        # Remove any trailing comments and newline (and ignore any empty or comment-only lines)
        code = code.split("#")[0]
        code = code.strip()
        if code:
            handle_qrcode(code)
            sleep(10)


# #############################################################################
# Startup program
# #############################################################################
class Mode:
    PLAY_AND_CLEAR = 'play_and_clear'
    BUILD_QUEUE = 'build_queue'
    PLAY_AND_QUEUE = 'play_and_queue'

# Load the most recently used device, if available, otherwise fall back on the `default-device` argument
try:
    with open('.last-device', 'r') as device_file:
        current_device = device_file.read().replace('\n', '')
        print('Defaulting to last used room: ' + current_device)
except:
    current_device = args.default_device
    print('Initial room: ' + current_device)

# Load the last save play mode, if available, otherwise fall back on the `PLAY_AND_QUEUE` argument
# PLAY_AND_QUEUE = Play current album/song and don't clear the queue
# PLAY_AND_CLEAR = Play current album/song and clear the queue
# BUILD_QUEUE = Add current album/song to the queue

try:
    with open('.last-playmode', 'r') as playmode_file:
        current_playmode = playmode_file.read().replace('\n', '')
        print('Defaulting to last used play mode: ' + current_playmode)
except:
    current_playmode = Mode.PLAY_AND_QUEUE
    print('Play mode: ' + current_playmode)

# Keep track of the last-seen code
last_qrcode = ''
last_qrcode_success = True

base_url = 'http://' + args.hostname + ':5005'
current_dir = os.path.dirname(os.path.abspath(__file__))

perform_room_request('pause', current_device)
perform_room_request('volume/' + args.default_volume, current_device)

if args.speak_welcome:
    speak('Hallo, ich bin dinoqode.')

if not args.skip_load:
    # Preload library on startup (it takes a few seconds to prepare the cache)
    print('Indexing the library...')
    if args.speak_welcome:
        speak('Musik Bibliothek indizieren')

    perform_room_request('musicsearch/library/load', current_device)
    print('Indexing complete!')

    if args.speak_welcome:
        speak('Jetzt bin ich bereit!')

if args.speak_welcome:
    speak('Zeig mir eine Karte!')


if args.debug_file:
    # Run through a list of codes from a local file
    read_debug_script()
else:
    # Start the QR code reader
    p = subprocess.Popen('/usr/bin/zbarcam --prescale=500x500 --nodisplay', shell=True, stdout=subprocess.PIPE)

    try:
        blink_led('rainbow')
        start_scan()
    except KeyboardInterrupt:
        print('Stopping scanner...')
        blink_led('pulse-red')
    finally:
        print('Closed')
        if use_blinkt == True:
            blinkt.clear()
            blinkt.show()

        traceback.print_exc()
        p.kill()
