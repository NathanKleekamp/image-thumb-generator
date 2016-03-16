#!/usr/bin/env python
from __future__ import division
from __future__ import print_function

import os
import re
import argparse

from wand.image import Image
from wand.exceptions import CoderError, CoderFatalError, CorruptImageError, \
                            CorruptImageFatalError, CorruptImageWarning, \
                            FileOpenError, FileOpenFatalError, FileOpenWarning,\
                            ImageError, ImageFatalError, ImageWarning


parser = argparse.ArgumentParser(add_help=False)

parser.add_argument("-d", "--directory",
    help="Path to input directory. Defaults to current directory")
parser.add_argument("-r", "--recursive",
    help="Recurse through the file system and process images.",
    action='store_true')
parser.add_argument("-w", "--width",
    help="Target width")
parser.add_argument("-h", "--height",
    help="Target height")
parser.add_argument("-g", "--gravity",
    help="Crop focus. Options include NorthWest, North, NorthEast, West,"
         "Center, East, SouthWest, South, SouthEast")

args = parser.parse_args()


class ProcessImages(object):
    '''
    Runs through a given directory looking for filenames that don't end in
    "-WidthxHeight.ext" (-1074x483.jpg, for example), resizes, and then crops
    to the desired dimensions.

    Usage:
    ./generate.py --directory='/path-to-images' --width=500 --height=500 --gravity='center'
    '''
    def __init__(self, input_directory, target_width, target_height,
            output_directory='', gravity=''):
        self.input_directory = os.path.abspath(input_directory)
        self.output_directory = self.input_directory
        self.target_width = target_width
        self.target_height = target_height
        self.gravity = gravity
        self.all_images = []
        self.uncropped = []
        self.execute();


    def get_images(self):
        '''
        Get all the image paths in the given directory.
        '''
        all_images = []
        files = os.listdir(self.input_directory)
        formats = ['.jpg', '.jpeg', '.png', '.gif', 'tiff', 'bmp']

        for f in files:
            file_ext = os.path.splitext(f)[1]
            if file_ext in formats:
                self.all_images.append(f)


    def remove_previously_processed(self):
        '''
        Remove all the previously cropped images to get the original image.
        Matches everything after the hyphen in the filename. For example,
        "-300x275.jpg" in this file: "timeline7-300x275.jpg"
        '''
        pattern = re.compile(
            '([a-zA-Z0-9\.\-\_+])+(-([0-9]+)x([0-9]+)(.jpg|.png|.jpeg|.gif))'
        )

        for image in self.all_images:
            if not pattern.match(image):
                image = '{0}/{1}'.format(self.input_directory, image)
                self.uncropped.append(image)


    def aspect_ratio(self, width, height):
        '''Returns the aspect ratio'''
        return width / height


    def get_orientation(self, image):
        '''Determine image orientation'''
        if self.aspect_ratio(image.width, image.height) >= 1:
            return "landscape"
        else:
            return "portrait"


    def calculate_height(self, width, aspect_ratio):
        '''Calcuates the height to preserve aspect ratio'''
        return width / aspect_ratio


    def calculate_width(self, height, aspect_ratio):
        '''Calcuates the width to preserve aspect ratio'''
        return height * aspect_ratio


    def calculate_landscape_dimensions(self, min_width, min_height, aspect_ratio):
        '''
        Caluculate landscape dimensions so that the min_width and min_height are
        not exceeded
        '''
        dimensions = {}
        dimensions['width'] = self.calculate_width(min_height, aspect_ratio)

        if dimensions['width'] >= min_width:
            dimensions['height'] = self.calculate_height(dimensions['width'],
                aspect_ratio)
        else:
            dimensions['width'] = min_width
            dimensions['height'] = self.calculate_height(dimensions['width'],
                aspect_ratio)

        dimensions['width'] = int(round(dimensions['width']))
        dimensions['height'] = int(round(dimensions['height']))

        return dimensions


    def calculate_portrait_dimensions(self, min_width, min_height, aspect_ratio):
        '''
        Caluculate portrait dimensions so that the min_width and min_height are
        not exceeded
        '''
        dimensions = {}
        dimensions['height'] = self.calculate_height(min_width, aspect_ratio)

        if dimensions['height'] >= min_height:
            dimensions['width'] = self.calculate_width(dimensions['height'],
                aspect_ratio)
        else:
            dimensions['height'] = min_height
            dimensions['width'] = self.calculate_width(dimensions['height'],
                aspect_ratio)

        dimensions['width'] = int(round(dimensions['width']))
        dimensions['height'] = int(round(dimensions['height']))

        return dimensions


    def scale_image(self, image, min_width, min_height):
        '''
        Get scale dimensions, resize, and return the image instance
        '''
        aspect_ratio = self.aspect_ratio(image.width, image.height)

        if self.get_orientation(image) == "landscape":
            dimensions = self.calculate_landscape_dimensions(min_width,
                min_height, aspect_ratio)
        else:
            dimensions = self.calculate_portrait_dimensions(min_width,
                min_height, aspect_ratio)

        image.resize(dimensions['width'], dimensions['height'])

        return image


    def crop_image(self, image, width, height):
        '''
        Checks if the image is larger than the desired dimensions, then crops
        '''
        if image.width >= width and image.height >= height:
            image.crop(width=width, height=height, gravity=self.gravity)
            return image


    def scale_crop_save_images(self):
        '''Scale, crop, and save the images'''
        for img in self.uncropped:
            image_name = os.path.splitext(os.path.split(img)[1])[0]
            image_ext = os.path.splitext(os.path.split(img)[1])[1]

            print("Processing:", img)

            try:
                with Image(filename=img) as image:
                    with image.clone() as clone:
                        scaled = self.scale_image(clone, self.target_width,
                            self.target_height)
                        cropped = self.crop_image(scaled, width=self.target_width,
                            height=self.target_height)
                        cropped.save(filename='{0}/{1}-{2}x{3}{4}'.format(
                            self.output_directory, image_name, self.target_width,
                            self.target_height, image_ext))
                        cropped.size
            except (CoderError, CoderFatalError, CorruptImageError, \
                    CorruptImageFatalError, CorruptImageWarning, FileOpenError, \
                    FileOpenFatalError, FileOpenWarning, ImageError, \
                    ImageFatalError, ImageWarning) as error:
                print("Error: {0}".format(error))
            except:
                print("Unexpected error: {0}".format(sys.exc_info()[0]))


    def execute(self):
        '''Execute on instantiation'''
        self.get_images()
        self.remove_previously_processed()
        self.scale_crop_save_images()


def check_gravity(gravity):
    '''Type check gravity'''
    gravity_types = ["northwest", "north", "northeast", "west", "center",
                     "east", "southwest", "south", "southeast"]
    gravity = gravity.lower()

    if not gravity in gravity_types:
        raise ValueError


def main():
    '''Do some error checking before getting too far'''
    try:
        width = int(args.width)
    except ValueError as error:
        print("Width must be a number \n")
    except TypeError as error:
        print("Width must be a number \n")
        return

    try:
        height = int(args.height)
    except ValueError as error:
        print("Height must be a number \n")
    except TypeError as error:
        print("Height must be a number \n")
        return

    try:
        if args.directory:
            if os.path.isdir(os.path.abspath(args.directory)):
                input_directory = args.directory
            else:
                raise IOError
        else:
           input_directory = os.curdir
    except IOError as error:
        print("IOError: Pass a valid directory. \n")
        return

    try:
        if args.gravity:
            gravity = check_gravity(args.gravity)
        else:
            gravity = 'center'
    except ValueError as error:
        print("Gravity must be northwest, north, northeast, west, center, east,"
              " southwest, south, southeast \n")
        return

    if args.recursive:
        input_directories = []
        for path, directories, files in os.walk(input_directory):
            input_directories.append(os.path.abspath(path))

        for input_directory in input_directories:
            process_images = ProcessImages(input_directory, width, height,
                                           gravity=gravity)
    else:
        process_images = ProcessImages(input_directory, width, height,
                                       gravity=gravity)


if __name__ == '__main__':
    main()
