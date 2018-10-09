import os
import subprocess
import shutil
import random
import re
from PIL import Image

def which(program):
    """Function to check for presence of executable/installed program
       Used for checking presense of ffmpeg/avconv"""
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

class ExtractException(BaseException):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

class extract(object):
    def __init__(self, path, fps = None, size = None, quality = None,
                 output_directory = None, output_fn_format = '%d.jpg',
                 preserve_output = False):
        """
        Extract frames from a video using ffmpeg (or avconv). Provide access to
        those frames via a collection of PIL.Image objects.

        Args:
            path (str): the file path to the video to extract frames from.
            fps (int): ask ffmpeg to extract images at a specific frame rate.
                If None, then let ffmpeg follow its default behavior, which is
                to use the FPS indicated in the video.
            size (2-item tuple of ints): ask ffmpeg to resize the image to a
                specific frame size, in pixels. Note that this does not
                preserve aspect ratio.
            quality (int): a value between 2 and 31, the represents the
                level of lossy compression to use on the resulting JPEG frame.
                2 is the least compression, highest quality. 31 is the most
                compression and loss. If None, then let ffmpeg do its default
                thing (which appears to be 2, but may be ffmpeg-dependent).
            output_directory (str): If None, then create a random directory
                in /tmp with a name starting with 'pyvsion-ffmpeg-' and then
                a random number. Else, use the string as given, creating the
                directory if it is not already present.
            output_fn_format (str): an 'ffmpeg' filename specification
                string, with the default of '%d.jpg'. See
                https://ffmpeg.org/ffmpeg.html, which says, "The syntax
                `foo-%03d.jpeg` specifies to use a decimal number composed of
                three digits padded with zeroes to express the sequence
                number. It is the same syntax supported by the C printf
                function, but only formats accepting a normal integer are
                suitable." Also, note that ffmpeg will work to infer the
                image file format based on this name, `jpg` creating JPEG
                image files, and `png` creating PNG image files.
        """
        self.starting_frame = 1
        if not output_directory:
            self.key = int(random.random() * 1000000000)
            self.key = "pyvision-ffmpeg-{0}".format(self.key)
            self.output = "/tmp/{0}".format(self.key)
        else:
            self.output = output_directory
        self.preserve = preserve_output
        self.output_fn_format = output_fn_format
        self.path = path
        try:
            os.makedirs(self.output) 
        except:
            pass

        subp_cmd = []
        if which("ffmpeg") is not None:
            subp_cmd.append('ffmpeg')
        else:
            subp_cmd.append('avconv')
        subp_cmd.append('-i')
        subp_cmd.append(path)
        subp_cmd.append('-b')
        subp_cmd.append('10000k')
        if fps:
            subp_cmd.append('-r')
            subp_cmd.append('{}'.format(int(fps)))
        if size:
            w, h = size
            subp_cmd.append('-s')
            subp_cmd.append('{1}x{2}'.format(int(w), int(h)))
        if quality:
            # quality should be an int between 2 and 31. 2 is BEST, 31 is WORST
            subp_cmd.append('-q')
            subp_cmd.append('{}'.format(int(quality)))

        subp_cmd.append("{}/{}".format(self.output, self.output_fn_format))
        #print "Command: {}".format(" ".join(subp_cmd))
        sp = subprocess.Popen(subp_cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        out, err = sp.communicate()
        self.original_dimensions = None
        regexp = re.compile(r',\s*(\d+x\d+),')
        for line in err.splitlines():
            if 'Stream #0' in line:
                m = regexp.search(line)
                if m:
                    self.original_dimensions = m.group(1)
        if sp.returncode != 0:
            raise ExtractException("ffmpeg returned ono-zero return code {}.\n{}".format(sp.returncode, err))


    def __del__(self):
        if self.output and not self.preserve:
            shutil.rmtree(self.output)

    def __getitem__(self, k):
        return Image.open(self.getframepath(k))

    def getframepath(self, k):
        return os.path.join(self.output, self.output_fn_format % (k + self.starting_frame))

    def __len__(self):
        f = 1
        while True:
            if not os.path.exists(self.getframepath(f)):
                return f
            f += 1

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]
