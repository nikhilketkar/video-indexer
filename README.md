```
> invoke --list
Available tasks:

 export-object    export_object(video_name, pos, output_path) -> exported_video_file
 export-segment   export_segment(video_name, start, end, output_path) -> exported_video_file
 index-video      index-video(video_path, meta_path) -> Index the video
 init-override    init_safe() -> Initialise DB, purge and recreate if exists
 init-safe        init_safe() -> Initialise DB, fail if exists
 list-videos      list_videos() -> [video_file]
 search-object    search_object(object_type) -> [video_file, id, position]
 search-video     search_video(video_name, pos, output_path) -> [object, position]

```