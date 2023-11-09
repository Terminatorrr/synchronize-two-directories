# synchronize-two-directories

Simple app that synchronizes destination directory with the source directory every N seconds

Requires 4 parameters:

- source_directory
- destination_directory
- frequency_starting_in_second
- log_file

sample:

python main.py H:/source_dir H:/destination_dir 60 H:/my_log_file.log