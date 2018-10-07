from invoke import task
import yaml
import os
import shutil
import pandas
import video_ops

def init(message = False):
    with open("./config.yaml") as config_file:
        config = yaml.load(config_file)
    vi = video_ops.VideoIndexer(config["data_path"])
    if message:
        print("Video Indexer initialised at " + config["data_path"])
    return vi

@task
def init_safe(c):
    """
    init_safe() -> Initialise DB, fail if exists
    """
    with open("./config.yaml") as config_file:
        config = yaml.load(config_file)
    if os.path.isdir(config["data_path"]):
        print("Video Indexer already exists at " + config["data_path"] + " aready exisits, use init-override to purge and recreate.")
    else:
        init(True)

@task
def init_override(c):
    """
    init_safe() -> Initialise DB, purge and recreate if exists
    """
    with open("./config.yaml") as config_file:
        config = yaml.load(config_file)
    if os.path.isdir(config["data_path"]):
        shutil.rmtree(config["data_path"])
    init(True)

@task
def index_video(c, video_path, meta_path):
    """
    index-video(video_path, meta_path) -> Index the video
    video_path: Path of video
    meta_path: Path of meta data (.csv)
    """
    vi = init()
    vi.index_video(video_path, meta_path)

@task
def list_videos(c):
    """
    list_videos() -> [video_file]
    """
    vi = init()
    df = pandas.DataFrame(vi.list_videos())
    df.columns = ["Video"]
    print(df)

@task
def search_object(c, object_type):
    """
    search_object(object_type) -> [video_file, id, position]
    object_type: Name of object type (elephant, zebra etc.)
    """
    vi = init()
    df = pandas.DataFrame(vi.search_object(object_type))
    df.columns = ["Video", "Object ID", "Position"]
    print(df)

@task
def search_video(c, video_name, start, stop):
    """
    search_video(video_name, pos, output_path) -> [object, position] 
    video_name: Name of the video
    start: Time in seconds on where to start the search
    end: Time in seconfs on where to stop the search
    """
    vi = init()
    df = pandas.DataFrame(vi.search_video(video_name, float(start), float(stop)))
    df.columns = ["Object Type", "Object Id", "Position"]
    print(df)
                          
@task
def export_object(c, video_name, pos, output_path):
    """
    export_object(video_name, pos, output_path) -> exported_video_file 
    video_name: Name of the video
    pos: Export around this position in seconds
    output_path: Output path, where to export the video
    """
    vi = init()
    vi.generate_object(video_name, float(pos), output_path)

@task()
def export_segment(c, video_name, start, stop, output_path):
    """
    export_segment(video_name, start, end, output_path) -> exported_video_file 
    video_name: Name of the video
    start: Time in seconds on where to start the export
    end: Time in seconfs on where to stop the export
    output_path: Output path, where to export the video
    """
    vi = init()
    vi.generate_segment(video_name, float(start), float(stop), output_path)

