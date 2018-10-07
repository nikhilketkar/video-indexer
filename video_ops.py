import moviepy.editor
import pandas
import cv2

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
    for timestamp, frame_objects in framemetas:
        print timestamp
        image = movie.to_ImageClip(t=timestamp)
        image_x, image_y = image.size
        image.save_frame("/tmp/temp.png")

        image = cv2.imread("/tmp/temp.png")

        for frame_object in frame_objects:
            xmin = int(frame_object["xmin"] * image_x)
            xmax = int(frame_object["xmin"] * image_x)
            ymin = int(frame_object["ymax"] * image_y)
            ymax = int(frame_object["ymax"] * image_y)
            cv2.rectangle(image, (xmin, xmax), (ymin, ymax), (0,255,0), 4)

        cv2.imwrite(images_path + "/" + str(int(timestamp)) + ".png", image)
