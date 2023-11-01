import logging
import os
import socket
import socketserver
import subprocess
import sys
import time

import click
from gtts import gTTS
import soco
from soco import SoCo
from soco.data_structures import DidlMusicTrack, DidlResource


def get_free_port():
    with socketserver.TCPServer(("localhost", 0), None) as s:
        return s.server_address[1]


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't need to be reachable, this just gets the IP of the preferred outbound socket
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    finally:
        s.close()
    return local_ip


def start_http_server(port):
    media_folder = os.path.join(os.path.dirname(__file__), "media")
    # no output
    httpserver = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port)], cwd=media_folder
    )
    return httpserver


def get_allowed_files():
    media_folder = os.path.join(os.path.dirname(__file__), "media")

    allowed_files = [
        f.replace(".mp3", "") for f in os.listdir(media_folder) if f.endswith(".mp3")
    ]
    return allowed_files


def group_all_sonos():
    # Discover all Sonos speakers
    speakers = list(soco.discover())

    # Get the first speaker as the coordinator
    coordinator = speakers[0].group.coordinator

    # Join all other speakers to the coordinator
    for speaker in speakers:
        if speaker == coordinator:
            continue
        speaker.join(coordinator)

    # Print the group information
    print("Sonos speakers grouped successfully.")


def save_text_to_speech(text: str) -> None:
    media_folder = os.path.join(os.path.dirname(__file__), "media")
    myobj = gTTS(text=text, lang="en", slow=False)
    file_path = os.path.join(media_folder, "text-to-speech.mp3")
    myobj.save(file_path)
    return None


@click.command()
@click.option(
    "--sonos_ip",
    default=None,
    help="IP address of the Sonos speaker, default is to us ALL speakers",
)
@click.option("--port", default=None, help="Port to run the HTTP server on")
@click.option("--volume", default=60, help="Volume to play the sound at")
@click.option(
    "--sound",
    default="school-bell-sound",
    help="Sound to play",
)
@click.option("--text-to-speech", default=None, help="Text to speech to play")
def main(sonos_ip, port, volume, sound, text_to_speech):
    if not port:
        port = get_free_port()

    # Get the IP of this machine in the local network
    host_address = f"{get_local_ip()}:{port}"

    if text_to_speech:
        save_text_to_speech(text_to_speech)
        path_to_mp3 = f"http://{host_address}/text-to-speech.mp3"
    else:
        if sound not in get_allowed_files():
            allowed = "\n".join([f" - {x}" for x in get_allowed_files()])
            logging.error(f"Sound {sound} not in allowed. Choose from: \n{allowed}")
            exit(1)

        # Specify the path to the MP3 file on your computer
        path_to_mp3 = f"http://{host_address}/{sound}.mp3"

    # Specify the IP address of the Sonos speaker

    # Start the HTTP server
    httpserver = start_http_server(port)

    if sonos_ip:
        sonos = SoCo(sonos_ip)
        sonos.volume = volume
    else:
        group_all_sonos()
        sonos = list(soco.discover())[0].group.coordinator
        sonos.group.volume = volume

    # Create a Resource object for the MP3 file
    mp3_resource = DidlResource(
        uri=path_to_mp3, protocol_info="http-get:*:audio/mpeg:*"
    )

    # Create a DidlMusicTrack object for the MP3 file
    mp3_item = DidlMusicTrack(
        title="My Audio", parent_id="Audio", item_id="0", resources=[mp3_resource]
    )

    # # Stop what's currently playing
    sonos.stop()

    # Clear the queue
    sonos.clear_queue()

    # Add the MP3 file to the Sonos speaker's queue
    sonos.add_to_queue(mp3_item)

    # Play the queue (i.e., the MP3 file we just added)
    sonos.play_from_queue(0)

    # wait 3 seconds
    time.sleep(3)

    # Stop the HTTP server
    httpserver.terminate()

    print(path_to_mp3)

    if text_to_speech:
        os.remove(
            os.path.join(os.path.dirname(__file__), "media", "text-to-speech.mp3")
        )


if __name__ == "__main__":
    main()
