# Copyright (c) 2020 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import cv2

from paddle.io import Dataset

__all__ = ["DatasetFolder", "ImageFolder"]


def has_valid_extension(filename, extensions):
    """Checks if a file is a vilid extension.

    Args:
        filename (str): path to a file
        extensions (tuple of str): extensions to consider (lowercase)

    Returns:
        bool: True if the filename ends with one of given extensions
    """
    return filename.lower().endswith(extensions)


def make_dataset(dir, class_to_idx, extensions, is_valid_file=None):
    images = []
    dir = os.path.expanduser(dir)

    if extensions is not None:

        def is_valid_file(x):
            return has_valid_extension(x, extensions)

    for target in sorted(class_to_idx.keys()):
        d = os.path.join(dir, target)
        if not os.path.isdir(d):
            continue
        for root, _, fnames in sorted(os.walk(d, followlinks=True)):
            for fname in sorted(fnames):
                path = os.path.join(root, fname)
                if is_valid_file(path):
                    item = (path, class_to_idx[target])
                    images.append(item)

    return images


class DatasetFolder(Dataset):
    """A generic data loader where the samples are arranged in this way:

        root/class_a/1.ext
        root/class_a/2.ext
        root/class_a/3.ext

        root/class_b/123.ext
        root/class_b/456.ext
        root/class_b/789.ext

    Args:
        root (string): Root directory path.
        loader (callable|optional): A function to load a sample given its path.
        extensions (tuple[str]|optional): A list of allowed extensions.
            both extensions and is_valid_file should not be passed.
        transform (callable|optional): A function/transform that takes in
            a sample and returns a transformed version.
        is_valid_file (callable|optional): A function that takes path of a file
            and check if the file is a valid file (used to check of corrupt files)
            both extensions and is_valid_file should not be passed.

     Attributes:
        classes (list): List of the class names.
        class_to_idx (dict): Dict with items (class_name, class_index).
        samples (list): List of (sample path, class_index) tuples
        targets (list): The class_index value for each image in the dataset

    Example:

        .. code-block:: python

            import os
            import cv2
            import tempfile
            import shutil
            import numpy as np
            from paddle.vision.datasets import DatasetFolder

            def make_fake_dir():
                data_dir = tempfile.mkdtemp()

                for i in range(2):
                    sub_dir = os.path.join(data_dir, 'class_' + str(i))
                    if not os.path.exists(sub_dir):
                        os.makedirs(sub_dir)
                    for j in range(2):
                        fake_img = (np.random.random((32, 32, 3)) * 255).astype('uint8')
                        cv2.imwrite(os.path.join(sub_dir, str(j) + '.jpg'), fake_img)
                return data_dir

            temp_dir = make_fake_dir()
            data_folder = DatasetFolder(temp_dir)

            for items in data_folder:
                break
                
            shutil.rmtree(temp_dir)
    """

    def __init__(self,
                 root,
                 loader=None,
                 extensions=None,
                 transform=None,
                 is_valid_file=None):
        self.root = root
        self.transform = transform
        if extensions is None:
            extensions = IMG_EXTENSIONS
        classes, class_to_idx = self._find_classes(self.root)
        samples = make_dataset(self.root, class_to_idx, extensions,
                               is_valid_file)
        if len(samples) == 0:
            raise (RuntimeError(
                "Found 0 files in subfolders of: " + self.root + "\n"
                "Supported extensions are: " + ",".join(extensions)))

        self.loader = cv2_loader if loader is None else loader
        self.extensions = extensions

        self.classes = classes
        self.class_to_idx = class_to_idx
        self.samples = samples
        self.targets = [s[1] for s in samples]

    def _find_classes(self, dir):
        """
        Finds the class folders in a dataset.

        Args:
            dir (string): Root directory path.

        Returns:
            tuple: (classes, class_to_idx) where classes are relative to (dir), 
                    and class_to_idx is a dictionary.

        """
        if sys.version_info >= (3, 5):
            # Faster and available in Python 3.5 and above
            classes = [d.name for d in os.scandir(dir) if d.is_dir()]
        else:
            classes = [
                d for d in os.listdir(dir)
                if os.path.isdir(os.path.join(dir, d))
            ]
        classes.sort()
        class_to_idx = {classes[i]: i for i in range(len(classes))}
        return classes, class_to_idx

    def __getitem__(self, index):
        """
        Args:
            index (int): Index

        Returns:
            tuple: (sample, target) where target is class_index of the target class.
        """
        path, target = self.samples[index]
        sample = self.loader(path)
        if self.transform is not None:
            sample = self.transform(sample)

        return sample, target

    def __len__(self):
        return len(self.samples)


IMG_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.ppm', '.bmp', '.pgm', '.tif',
                  '.tiff', '.webp')


def cv2_loader(path):
    return cv2.imread(path)


class ImageFolder(Dataset):
    """A generic data loader where the samples are arranged in this way:

        root/1.ext
        root/2.ext
        root/sub_dir/3.ext

    Args:
        root (string): Root directory path.
        loader (callable, optional): A function to load a sample given its path.
        extensions (tuple[string], optional): A list of allowed extensions.
            both extensions and is_valid_file should not be passed.
        transform (callable, optional): A function/transform that takes in
            a sample and returns a transformed version.
        is_valid_file (callable, optional): A function that takes path of a file
            and check if the file is a valid file (used to check of corrupt files)
            both extensions and is_valid_file should not be passed.

     Attributes:
        samples (list): List of sample path

    Example:

        .. code-block:: python

            import os
            import cv2
            import tempfile
            import shutil
            import numpy as np
            from paddle.vision.datasets import ImageFolder

            def make_fake_dir():
                data_dir = tempfile.mkdtemp()

                for i in range(2):
                    sub_dir = os.path.join(data_dir, 'class_' + str(i))
                    if not os.path.exists(sub_dir):
                        os.makedirs(sub_dir)
                    for j in range(2):
                        fake_img = (np.random.random((32, 32, 3)) * 255).astype('uint8')
                        cv2.imwrite(os.path.join(sub_dir, str(j) + '.jpg'), fake_img)
                return data_dir

            temp_dir = make_fake_dir()
            data_folder = ImageFolder(temp_dir)

            for items in data_folder:
                break
                
            shutil.rmtree(temp_dir)
     """

    def __init__(self,
                 root,
                 loader=None,
                 extensions=None,
                 transform=None,
                 is_valid_file=None):
        self.root = root
        if extensions is None:
            extensions = IMG_EXTENSIONS

        samples = []
        path = os.path.expanduser(root)

        if extensions is not None:

            def is_valid_file(x):
                return has_valid_extension(x, extensions)

        for root, _, fnames in sorted(os.walk(path, followlinks=True)):
            for fname in sorted(fnames):
                f = os.path.join(root, fname)
                if is_valid_file(f):
                    samples.append(f)

        if len(samples) == 0:
            raise (RuntimeError(
                "Found 0 files in subfolders of: " + self.root + "\n"
                "Supported extensions are: " + ",".join(extensions)))

        self.loader = cv2_loader if loader is None else loader
        self.extensions = extensions
        self.samples = samples
        self.transform = transform

    def __getitem__(self, index):
        """
        Args:
            index (int): Index

        Returns:
            tuple: (sample, target) where target is class_index of the target class.
        """
        path = self.samples[index]
        sample = self.loader(path)
        if self.transform is not None:
            sample = self.transform(sample)
        return [sample]

    def __len__(self):
        return len(self.samples)
