Used for going through a Wordpress uploads directory and generating thumbnails at a single specific size, instead of regenerating all the thumbs at all the sizes.

Runs through a given directory looking for filenames that don't end in  "-WidthxHeight.ext" (-1074x483.jpg, for example), resizes, and then crops to the desired dimensions.

**Usage**:

`./generate.py --directory='/path-to-images' --width=500 --height=500 --gravity='center'`

**Command Line Flags**:
```
"-d", "--directory", "Path to input directory. Defaults to current directory"`
"-w", "--width", "Target width"
"-h", "--height", "Target height"
"-g", "--gravity", "Crop focus. Options include NorthWest, North, NorthEast, West, Center, East, SouthWest, South, SouthEast"
"-r", "--recursive", "Recurse through the directory tree"
```
