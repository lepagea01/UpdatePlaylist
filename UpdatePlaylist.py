import os
from urllib.parse import unquote, quote

import jellyfish
from lxml import etree


def get_song_names(path):
    excluded_prefixes = ('.')
    included_suffixes = ('.mp3', '.m4a', '.m4p')
    song_names = {}
    for root, dirs, files in os.walk(path, topdown=True, onerror=None, followlinks=False):
        files = [f for f in files if
                 not f.lower().startswith(excluded_prefixes) and f.lower().endswith(included_suffixes)]
        for filename in files:
            song_names['/'.join(os.path.join(root, filename).split('/')[-3:])] = 'file://' + quote(
                os.path.abspath(os.path.join(root, filename)))
    return song_names


def match(x, y, treshold=0, limit=1):
    matched_value = None
    score = 0
    for i in y:
        i_score = jellyfish.jaro_winkler(x, i)
        if i_score > score and i_score >= treshold:
            matched_value = i
            score = i_score
            if score >= limit:
                break
    return matched_value


# Prompt user:
playlist = input("Playlist to update: ")
path = input("Music library path: ")
targetDir = input("Target directory: ")
treshold = input("Matching treshold: ")

# Set default values:
default_path = '/Volumes/Music/My Music/Alex\'s Music/iTunes/iTunes Music'
if path == '':
    path = default_path
default_treshold = 0.85
if treshold == '':
    treshold = default_treshold

song_names = get_song_names(path)
root = etree.parse(playlist).getroot()
locations = root.xpath('.//string[contains(text(),"file://localhost")]')
locations = [l for l in locations if not l.getprevious().text == 'Music Folder']
for location in locations:
    for sib in location.itersiblings(preceding=True):
        if not sib.text == 'Location' and not sib.text == 'Track ID' and not sib.text == sib.getparent().getprevious().text:
            sib.getparent().remove(sib)
    for sib in location.itersiblings(preceding=False):
        sib.getparent().remove(sib)
    song = '/'.join(unquote(location.text).split('/')[-3:])
    matched = match(song, list(song_names.keys()), treshold)
    if matched is not None:
        location.text = song_names[matched]

etree.ElementTree(root).write(targetDir + '/' + os.path.basename(playlist), pretty_print=True, xml_declaration=True,
                              encoding='UTF-8')
