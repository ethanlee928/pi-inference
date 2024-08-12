import gi

# Import necessary GStreamer modules
gi.require_version("Gst", "1.0")
from gi.repository import GstRtspServer


def launch_rtsp_server(
    rtsp_port=8554,
    udp_port=5000,
    codec="H264",
    clock_rate=90000,
    payload=96,
    endpoint="base",
):
    """Set up and run an RTSP server with configurable parameters.

    Args:
        rtsp_port (int): Port for the RTSP server.
        udp_port (int): Port for the UDP source.
        codec (str): Video codec to be used.
        clock_rate (int): Clock rate for the stream.
        payload (int): Payload type for the stream.
        endpoint (str): Endpoint for the stream. e.g., rtsp://@:8554/base
    """
    server = GstRtspServer.RTSPServer()
    server.set_property("service", str(rtsp_port))

    factory = GstRtspServer.RTSPMediaFactory()
    factory.set_shared(True)

    pipeline = (
        "( udpsrc port={udp_port} name=pay0 "
        "caps=application/x-rtp,media=video,clock-rate={clock_rate},"
        "encoding-name=(string){codec},payload={payload} )"
    ).format(udp_port=udp_port, codec=codec, clock_rate=clock_rate, payload=payload)

    factory.set_launch(pipeline)
    mount_points = server.get_mount_points()
    mount_points.add_factory(f"/{endpoint}", factory)
    server.attach(None)
