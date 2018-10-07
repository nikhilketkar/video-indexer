import os
import shutil 
import moviepy.editor
import pandas
import numpy
import cv2
import shelve

def process_meta(meta_path):
    df = pandas.read_csv(meta_path)
    df.columns = ["timestamp_ms", "class_name", "object_id", "object_presence", "xmin", "xmax", "ymin", "ymax"]
    df["timestamp"] = df["timestamp_ms"]/1000.0
    df = df[df["object_presence"] == "present"]
    result = []
    for name, group in df.groupby(["timestamp"]):
        curr_result = []
        for row, data in group.iterrows():
            curr_result.append(data.to_dict())
        result.append((name, curr_result))
    return result

def index_video(video_path, meta_path, images_path):
    framemetas = process_meta(meta_path)
    movie = moviepy.editor.VideoFileClip(video_path)
    index = []
    padding = 0.0
    for timestamp, frame_objects in framemetas:
        image = movie.to_ImageClip(t=timestamp)
        image_x, image_y = image.size
        image.save_frame("/tmp/temp.png")

        image = cv2.imread("/tmp/temp.png")

        for frame_object in frame_objects:
            if frame_object["object_presence"] == "present":
                print("Indexed " + frame_object["class_name"] + "," + str(frame_object["object_id"]) + " at timestamp " + str(timestamp))
                xmin = int(frame_object["xmin"] * image_x)
                xmax = int(frame_object["xmin"] * image_x)
                ymin = int(frame_object["ymax"] * image_y)
                ymax = int(frame_object["ymax"] * image_y)
                cv2.rectangle(image, (xmin, xmax), (ymin, ymax), (0,255,0), 4)
                cv2.putText(image,
                           "(" + frame_object["class_name"] + "," + str(frame_object["object_id"]) + ")",
                           (xmin, ymin), cv2.FONT_HERSHEY_SIMPLEX,0.8, (0, 255, 0), 2, cv2.LINE_AA)

                padding += 1.0
                index.append((frame_object["class_name"], frame_object["object_id"], timestamp + 0.5 * padding))
        cv2.imwrite(images_path + "/" + str(int(timestamp)) + ".png", image)
    return index
        
def build_video(video_path, index_path, output_path):
    print("Building anotated video, this will take some time...")
    images_list = [index_path + "/" + i for i in sorted(os.listdir(index_path), key = lambda x: int(x.replace(".png", "")))]

    labeled_clips = []
    for i in images_list:
        labelled_clip = moviepy.editor.CompositeVideoClip([moviepy.editor.ImageClip(i)]).set_duration(0.5)
        labeled_clips.append(labelled_clip)
    
    timestamps = [float(i.replace(".png", "")) for i in sorted(os.listdir(index_path), key = lambda x: int(x.replace(".png", "")))]
    
    clips = []
    first = True

    for i in range(0, len(timestamps)):
        if first:
            first = False
            curr_clip = moviepy.editor.VideoFileClip(video_path).subclip(0.0, timestamps[i])
        else:
            curr_clip = moviepy.editor.VideoFileClip(video_path).subclip(timestamps[i - 1], timestamps[i])

        clips.append(curr_clip)
        clips.append(labeled_clips[i])

    maxd = moviepy.editor.VideoFileClip(video_path).duration
    curr_clip = moviepy.editor.VideoFileClip(video_path).subclip(timestamps[-1], maxd)
    clips.append(curr_clip)
    
    result_clip = moviepy.editor.concatenate_videoclips(clips)
    result_clip.write_videofile(output_path)

def anotate_video(input_video_path, input_meta_path, output_video_path):
    os.mkdir("/tmp/video-index")
    index = index_video(input_video_path, input_meta_path, "/tmp/video-index")
    build_video(input_video_path, "/tmp/video-index", output_video_path)
    shutil.rmtree("/tmp/video-index")
    print("Indexing Completed")
    return index

def subclip_around(input_video_path, pos, output_video_path):
    result_clip = moviepy.editor.VideoFileClip(input_video_path).subclip(float(pos - 1), float(pos + 1))
    result_clip.write_videofile(output_video_path)

def subclip(input_video_path, start, stop, output_video_path):
    result_clip = moviepy.editor.VideoFileClip(input_video_path).subclip(float(start), float(stop))
    result_clip.write_videofile(output_video_path)

class VideoIndexer(object):
    def __init__(self, data_path):
        self.data_path = data_path
        
        if not os.path.isdir(data_path):
            os.mkdir(data_path)
            os.mkdir(data_path + "/raw")
            os.mkdir(data_path + "/anotated")
            self.db = shelve.open(data_path + "/meta")
            self.db["videos"] = []
            self.db.close()

        self.db = shelve.open(data_path + "/meta")
        self.raw = data_path + "/raw"
        self.anotated = data_path + "/anotated"

    def index_video(self, video_path, meta_path):

        if not (os.exists(video_path) and os.exists(meta_path)):
            print("Cannot find either " + video_path + " or " + meta_path)
            return
        
        video_name = video_path.split("/")[-1]
        
        videos = self.db["videos"]

        if not video_name in set(videos):        
            videos.append(video_name)
            self.db["videos"] = videos

            shutil.copy(video_path, self.raw + "/" + video_name)

            index = anotate_video(video_path, meta_path, self.anotated + "/" + video_name)
            self.db[video_name] = index

            for object_type, object_id, position in index:
                if not self.db.has_key(object_type):
                    self.db[object_type] = []

                curr = self.db[object_type]
                curr.append((video_name, object_id, position))
                self.db[object_type] = curr
        else:
            print("A video named " + video_name + " already exists, not performing any operation.")    
            
    def list_videos(self):
        return self.db["videos"]

    def search_object(self, object_type):
        if self.db.has_key(object_type):
            return self.db[object_type]

    def search_video(self, video_name, start, stop):
        result = []
        videos = set(self.db["videos"])
        if video_name in videos:
            video_contents = self.db[video_name]
            for object_type, object_id, time_stamp in video_contents:
                if time_stamp > start and time_stamp < stop:
                    result.append((object_type, object_id, time_stamp))
        return result

    def generate_segment(self, video_name, start, stop, output_video_path):
        subclip(self.anotated + "/" + video_name, start, stop, output_video_path)

    def generate_object(self, video_name, pos, output_video_path):
        subclip_around(self.anotated + "/" + video_name, pos, output_video_path)

    
    
    


            
        
