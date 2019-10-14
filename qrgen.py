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
import os.path
import shutil
import subprocess
import re


# Parse the command line arguments
arg_parser = argparse.ArgumentParser(description='Generates an HTML page containing cards with embedded QR codes that can be interpreted by `qrplay`.')
arg_parser.add_argument('--input', help='the file containing the list of commands and songs to generate')
arg_parser.add_argument('--generate-images', action='store_true', help='generate an individual PNG image for each card')
arg_parser.add_argument('--print-dublex', action='store_true', help='generate cards optimized for duplex print', default=False)
args = arg_parser.parse_args()
print(args)


def process_command(line, index):
    split = re.split('\\|', line)

    if line.startswith('cmd:say'):
        (cmdname, arturl, qrcode) = (split[2], split[3], (split[0] + '|' + split[1] + '|' + split[2]))
    elif line.startswith('cmd:room'):
        (cmdname, arturl, qrcode) = (split[1], split[2], (split[0] + '|' + split[1]))
    else:
        (cmdname, arturl, qrcode) = (split[1], split[2], split[0])

    # Determine the output image file names
    qrout = 'out/{0}qr.png'.format(index)
    artout = 'out/{0}art.png'.format(index)

    # Create a QR code from the command URI
    print(subprocess.check_output(['qrencode', '-s', '100', '-o', qrout, qrcode]))

    # Fetch the artwork and save to the output directory
    print(subprocess.check_output(['curl', arturl, '-o', artout]))

    return (cmdname, None, None)


def process_tunein(line, index):
    split = re.split('\\|', line)

    (cmdname, arturl, qrcode) = (split[1], split[2], split[0])

    # Determine the output image file names
    qrout = 'out/{0}qr.png'.format(index)
    artout = 'out/{0}art.png'.format(index)

    # Create a QR code from the command URI
    print(subprocess.check_output(['qrencode', '-s', '100', '-o', qrout, qrcode]))

    # Fetch the artwork and save to the output directory
    print(subprocess.check_output(['curl', arturl, '-o', artout]))

    return (cmdname, None, None)

def process_playlist_favorite(line, index):
    split = re.split('\\|', line)

    (cmdname, arturl, qrcode) = (split[1], split[2], split[0])

    # Determine the output image file names
    qrout = 'out/{0}qr.png'.format(index)
    artout = 'out/{0}art.png'.format(index)

    # Create a QR code from the command URI
    print(subprocess.check_output(['qrencode', '-s', '100', '-o', qrout, qrcode]))

    # Fetch the artwork and save to the output directory
    print(subprocess.check_output(['curl', arturl, '-o', artout]))

    return (cmdname, None, None)


def process_track(line, index):
    split = re.split('\\|', line)

    service = re.split('\\:', line)[0]

    if ':album:' in line:
        album = split[1]
        song = None
        artist = split[2]
        arturl = split[3]
    else:
        album = split[2]
        song = split[1]
        artist = split[3]
        arturl = split[4]

    # Determine the output image file names
    qrout = 'out/{0}qr.png'.format(index)
    artout = 'out/{0}art.png'.format(index)

    # Create a QR code from the track URI
    print(subprocess.check_output(['qrencode', '-s', '100', '-o', qrout, split[0]]))

    # Fetch the artwork and save to the output directory
    print(subprocess.check_output(['curl', arturl, '-o', artout]))

    return (song, album, artist, service)


# Return the HTML content for a single card.
def card_content_html(index, artist, album, song, service):
    qrimg = '{0}qr.png'.format(index)
    artimg = '{0}art.png'.format(index)
    serviceimg = '{0}.png'.format(service)

    html = ''
    html += '  <img src="{0}" class="art"/>\n'.format(artimg)
    html += '  <img src="{0}" class="qrcode"/>\n'.format(qrimg)
    html += '  <div class="labels track-info">\n'
    html += '    <p class="song">{0}</p>\n'.format(song or album)
    if artist:
        html += '    <p class="artist"><span class="small">von</span> {0}</p>\n'.format(artist)
    if album and song is not None:
        html += '    <p class="album"><span class="small">Album </span> {0}</p>\n'.format(album)
    html += '  </div>\n'
    if service:
        html += '  <div class="labels music-service">\n'
        html += '    <img src="{0}" class="logo"/>\n'.format(serviceimg)
        html += '  </div>\n'

    return html


# Generate a PNG version of an individual card (with no dashed lines).
def generate_individual_card_image(index, artist, album, song, service):
    # First generate an HTML file containing the individual card
    html = '''
<!DOCTYPE html>
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="cards.css">
</head>
<body>
  <div class="card">
'''
    html += card_content_html(index, artist, album, song, service)
    html += '''
</div>
</body>
</html>
'''

    html_filename = 'out/{0}.html'.format(index)
    with open(html_filename, 'w') as f:
        f.write(html)

    # Then convert the HTML to a PNG image (beware the hardcoded values; these need to align
    # with the dimensions in `cards.css`)
    png_filename = 'out/{0}'.format(index)
    print(subprocess.check_output(['webkit2png', html_filename, '--scale=1.0', '--clipped', '--clipwidth=720', '--clipheight=640', '--delay=2' ,'-o', png_filename]))

    # Rename the file to remove the extra `-clipped` suffix that `webkit2png` includes by default
    os.rename(png_filename + '-clipped.png', png_filename + 'card.png')


def generate_cards():
    service = ''
    duplex = args.print_dublex
    htmlarr = []

    def print_card_back():
        html = ''
        if duplex and len(htmlarr) > 0:
            html += '<br style="clear: both;"/>\n'
            html += '<div class="back">'
            for back in htmlarr:
                html += back

            html += '</div>'
            del htmlarr[:]
            html += '<br style="clear: both;"/>\n'

        return html

    # Create the output directory
    dirname = os.getcwd()
    outdir = os.path.join(dirname, 'out')
    print(outdir)
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    os.mkdir(outdir)

    # Read the file containing the list of commands and songs to generate
    with open(args.input) as f:
        lines = f.readlines()

    # The index of the current item being processed
    index = 0

    # Copy the CSS file into the output directory.  (Note the use of 'page-break-inside: avoid'
    # in `cards.css`; this prevents the card divs from being spread across multiple pages
    # when printed.)
    shutil.copyfile('cards/cards.css', 'out/cards.css')
    shutil.copyfile('cards/amazonmusic.png', 'out/amazonmusic.png')
    shutil.copyfile('cards/applemusic.png', 'out/applemusic.png')
    shutil.copyfile('cards/spotify.png', 'out/spotify.png')
    shutil.copyfile('cards/aldilife.png', 'out/aldilife.png')
    shutil.copyfile('cards/napster.png', 'out/napster.png')
    shutil.copyfile('cards/lib.png', 'out/lib.png')

    # Begin the HTML template
    html = '''
<!DOCTYPE html>
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="cards.css">
</head>
'''
    if duplex:
        html += '<body class="duplex">'
    else:
        html += '<body>'

    for line in lines:
        # Trim newline
        line = line.strip()

        # Remove any trailing comments and newline (and ignore any empty or comment-only lines)
        line = line.split('#')[0]
        line = line.strip()
        if not line:
            continue

        if line.startswith('cmd:'):
            (song, album, artist) = process_command(line, index)
        elif line.startswith('applemusic:') or line.startswith('amazonmusic:') or line.startswith('spotify:') or  line.startswith('aldilife:') or line.startswith('napster:') or line.startswith('lib:') :
            (song, album, artist, service) = process_track(line, index)
        elif line.startswith('tunein:'):
            (song, album, artist) = process_tunein(line, index)
        elif line.startswith('favorite:') or line.startswith('playlist:'):
            (song, album, artist) = process_playlist_favorite(line, index)
        else:
            print('Failed to handle URI: ' + line)
            continue

        # Append the HTML for this card
        cardhtml = '<div class="card">\n'
        cardhtml += card_content_html(index, artist, album, song, service)
        cardhtml += '</div>\n'

        if args.generate_images:
            # Also generate an individual PNG for the card
            generate_individual_card_image(index, artist, album, song, service)

        if duplex:
            if index % 4 == 3:
                cardhtml += '<br style="clear: both;"/>\n'
        else:
            if index % 2 == 1:
                cardhtml += '<br style="clear: both;"/>\n'

        html += cardhtml

        if duplex:
            htmlarr.append(cardhtml)

            if index % 12 == 11:
                html += print_card_back()

        index += 1

    html += print_card_back()
    html += '</body>\n'
    html += '</html>\n'

    print(html)

    with open('out/index.html', 'w') as f:
        f.write(html)


generate_cards()
