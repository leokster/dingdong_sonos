import click
import os
from soco import SoCo
from soco.data_structures import DidlMusicTrack, DidlResource
import subprocess
import socket
import time


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't need to be reachable, this just gets the IP of the preferred outbound socket
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    finally:
        s.close()
    return local_ip


def start_http_server(port="8001"):
    media_folder = os.path.join(os.path.dirname(__file__), "media")
    httpserver = subprocess.Popen(
        ["python", "-m", "http.server", str(port)], cwd=media_folder
    )
    return httpserver


@click.command()
@click.argument("sonos_ip")
@click.option("--port", default="8001", help="Port to run the HTTP server on")
@click.option("--volume", default=5, help="Volume to play the sound at")
def main(sonos_ip, port, volume):
    # Get the IP of this machine in the local network
    host_address = f"{get_local_ip()}:{port}"

    # Specify the path to the MP3 file on your computer
    path_to_mp3 = f"http://{host_address}/school-bell-sound.mp3"

    # Specify the IP address of the Sonos speaker

    # Start the HTTP server
    httpserver = start_http_server(port)

    # Create a SoCo instance
    sonos = SoCo(sonos_ip)

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

    sonos.volume = volume
    # Play the queue (i.e., the MP3 file we just added)
    sonos.play_from_queue(0)

    # wait 3 seconds
    time.sleep(3)

    # Stop the HTTP server
    httpserver.terminate()

    print(path_to_mp3)


if __name__ == "__main__":
    main()
