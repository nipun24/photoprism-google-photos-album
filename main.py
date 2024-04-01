import requests
import hashlib
import json
from traceback import format_exc
from conf import *


def calculate_sha1(fname):
    return hashlib.sha1(open(fname, 'rb').read()).hexdigest()


if __name__ == '__main__':
    albums = []
    headers = {}

    res = requests.request('POST', URL + '/api/v1/session', json={'username': USERNAME, 'password': PASSWORD})
    session_id = res.json()['id']
    headers['X-Session-ID'] = session_id

    # find all metadata.json files and extract albums
    try:
        print('Found the following albums:')
        for i in TAKEOUT_FOLDER.glob('**/metadata.json'):
            metadata = json.loads(open(i, 'r').read())
            if metadata['title']:
                metadata['takeout_file_path'] = i.parent
                albums.append(metadata)
                print(metadata["title"])
    except Exception as e:
        print(format_exc())

    print('\n')

    proceed = input('continue? (y/n):')
    if proceed == 'n':
        exit(0)

    try:
        for i in albums:
            album_data = {}
            photos = []
            # create album in photoprism
            res = requests.request('POST', URL + '/api/v1/albums', headers=headers, json={'Title': i['title']})
            if res.status_code == 200:
                print('Created Album -', i['title'])
                album_data = res.json()

            for j in i['takeout_file_path'].glob('*'):
                file_hash = calculate_sha1(j)
                res = requests.request('GET', URL + '/api/v1/files/' + file_hash, headers=headers)
                if res.status_code == 200:
                    photo_uid = res.json()['PhotoUID']
                    print(f'Found {photo_uid} in photoprism. Adding to batch')
                    photos.append(photo_uid)

            # add photos to the album
            try:
                res = requests.request('POST', URL + '/api/v1/albums/' + album_data['UID'] + '/photos',
                                       headers=headers, json={'photos': photos})
                if res.status_code != 200:
                    raise ()
                print(f"Added {len(photos)} photos in album {i['title']}.")
            except Exception as e:
                print(f"Added to to album {i['title']} failed!!!")
                print(format_exc())

    except Exception as e:
        print(format_exc())

    res = requests.request('DELETE', URL + f'/api/v1/session/{session_id}')
    if res.status_code == 200:
        print('Deleted Session')
    else:
        print(f'session deletion failed!!')
        print(res.text)
