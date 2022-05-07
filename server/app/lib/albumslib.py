"""
This library contains all the functions related to albums.
"""
from copy import deepcopy
import random
import urllib
from typing import List

from app import api
from app import instances
from app import models
from app.lib import taglib
from app.lib import trackslib
from progress.bar import Bar

from app import helpers


def get_all_albums() -> List[models.Album]:
    """
    Returns a list of album objects for all albums in the database.
    """
    print("Getting all albums...")

    albums: List[models.Album] = []

    db_albums = instances.album_instance.get_all_albums()

    _bar = Bar("Creating albums", max=len(db_albums))
    for album in db_albums:
        aa = models.Album(album)
        albums.append(aa)
        _bar.next()

    _bar.finish()

    return albums


def create_everything() -> List[models.Track]:
    """
    Creates album objects for all albums and returns
    a list of track objects
    """
    albums: list[models.Album] = get_all_albums()

    api.ALBUMS = albums
    api.ALBUMS.sort(key=lambda x: x.hash)

    tracks = trackslib.create_all_tracks()

    api.TRACKS.clear()
    api.TRACKS.extend(tracks)
    api.TRACKS.sort(key=lambda x: x.title)


def find_album(albumtitle: str, artist: str) -> int or None:
    """
    Finds an album by album title and artist.
    """

    left = 0
    right = len(api.ALBUMS) - 1
    iter = 0

    while left <= right:
        iter += 1
        mid = (left + right) // 2
        hash = helpers.create_album_hash(albumtitle, artist)

        try:
            if api.ALBUMS[mid].hash == hash:
                return mid
        except:
            print(api.ALBUMS[mid])

        if api.ALBUMS[mid].hash < hash:
            left = mid + 1
        else:
            right = mid - 1

    return None


def get_album_duration(album: List[models.Track]) -> int:
    """
    Gets the duration of an album.
    """

    album_duration = 0

    for track in album:
        album_duration += track.length

    return album_duration


def use_defaults() -> str:
    """
    Returns a path to a random image in the defaults directory.
    """
    path = "defaults/" + str(random.randint(0, 20)) + ".webp"
    return path


def gen_random_path() -> str:
    """
    Generates a random image file path for an album image.
    """
    choices = "abcdefghijklmnopqrstuvwxyz0123456789"
    path = "".join(random.choice(choices) for i in range(20))
    path += ".webp"

    return path


def get_album_image(album: list) -> str:
    """
    Gets the image of an album.
    """

    for track in album:
        img_p = gen_random_path()

        exists = taglib.extract_thumb(track["filepath"], webp_path=img_p)

        if exists:
            return img_p

    return use_defaults()


class GetAlbumTracks:
    """
    Finds all the tracks that match a specific album, given the album title
    and album artist.
    """

    def __init__(self, album: str, artist: str) -> None:
        self.hash = helpers.create_album_hash(album, artist)
        self.tracks = api.DB_TRACKS
        self.tracks.sort(key=lambda x: x["albumhash"])

    def find_tracks(self):
        tracks = []
        index = trackslib.find_track(self.tracks, self.hash)

        while index is not None:
            track = self.tracks[index]
            tracks.append(track)
            self.tracks.remove(track)
            index = trackslib.find_track(self.tracks, self.hash)

        api.DB_TRACKS.extend(tracks)
        return tracks


def get_album_tracks(album: str, artist: str) -> List:
    return GetAlbumTracks(album, artist).find_tracks()


def create_album(track) -> models.Album:
    """
    Generates and returns an album object from a track object.
    """
    album = {
        "title": track["album"],
        "artist": track["albumartist"],
    }

    album_tracks = get_album_tracks(album["title"], album["artist"])

    album["date"] = album_tracks[0]["date"]

    album["artistimage"] = urllib.parse.quote_plus(
        album_tracks[0]["albumartist"] + ".webp"
    )

    album["image"] = get_album_image(album_tracks)

    return album


def search_albums_by_name(query: str) -> List[models.Album]:
    """
    Searches albums by album name.
    """
    title_albums: List[models.Album] = []
    artist_albums: List[models.Album] = []

    for album in api.ALBUMS:
        if query.lower() in album.title.lower():
            title_albums.append(album)

    for album in api.ALBUMS:
        if query.lower() in album.artist.lower():
            artist_albums.append(album)

    return [*title_albums, *artist_albums]
