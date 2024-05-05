from vlc import Instance, EventType
from time import time, sleep
import threading
import os

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setmode(GPIO.BCM)

vlci = Instance()

default_media_list = 0

rootpath = '/mnt/link_to_medias'
pin_button_feedback = 2
pin_button_led = 3
pin_strip_led = 4

GPIO.setup(pin_button_feedback, GPIO.IN)
GPIO.setup(pin_button_led, GPIO.OUT)
GPIO.setup(pin_strip_led, GPIO.OUT)

list_player = vlci.media_list_player_new()

filenames_playlists = os.listdir(rootpath)
filenames_playlists.sort()

media_lists = []

for filename_playlist in filenames_playlists[::-1]:
  if filename_playlist.lower() in ('.ds_store', 'system volume information'):
    continue
  media_list = vlci.media_list_new()

  playlist_path = os.path.join(rootpath, filename_playlist)

  filenames_videos = os.listdir(playlist_path)
  filenames_videos.sort()

  for filename_video in filenames_videos:
    media_list.add_media(vlci.media_new(os.path.join(playlist_path, filename_video)))

  media_lists.append(media_list)

current_media_list = 0

def play_default_list():
  list_player.set_media_list(media_lists[default_media_list])
  list_player.play()
  current_media_list = 0

play_default_list()

# On playlist end logic
def handle_events():
  events = list_player.event_manager()
  events.event_attach(EventType.MediaPlayerListStopped, play_default_list)

threading.Thread(target=handle_events, daemon=True).join()

# Button logic
prev_state = GPIO.input(pin_button_feedback)

is_next_playlist = False

pending_action = None

def tick():
  sleep(0.01)
  return True

while tick():
  curr_state = GPIO.input(pin_button_feedback)

  if curr_state != prev_state:
    prev_state = curr_state
    if curr_state: # keydown event
      time_limit = time() + 0.5
      prev_state_inner = curr_state
      pending_action = 'next_video'
      while tick() and time() < time_limit:
        curr_state_inner = GPIO.input(pin_button_feedback)

        if curr_state_inner != prev_state_inner:
          if curr_state_inner:
            pending_action = 'next_playlist'
            break
          prev_state_inner = curr_state_inner

      while GPIO.input(pin_button_feedback):
        pass

      if pending_action == 'next_video':
        list_player.next()
      elif pending_action == 'next_playlist':
        current_media_list += 1
        list_player.set_media_list(media_lists[current_media_list])

    else: # keyup event
      pass

    prev_state = curr_state

