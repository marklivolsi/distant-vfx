import os
import binpacking


class Chunker:

    def __init__(self):
        pass

    def chunk(self, root_path, chunk_size):
        """
        Public facing method to chunk files in a directory into relatively constant size bins.
        :param root_path: The directory to scan (items in the root_path directory will be chunked into bins).
        :param chunk_size: The target size (bytes) for each bin.
        :return: A list of lists, each sublist representing a bin of roughly constant size.
        """
        items = self._get_item_sizes(root_path)
        return self._chunk_items(items, chunk_size)

    @staticmethod
    def _chunk_items(items, chunk_size):
        """
        Use binpacking library to chunk a set of files/directories into relatively constant volume bins.
        :param items: A dict formatted as {filepath: size in bytes}
        :param chunk_size: The optimal size (in bytes) to target for each bin.
        :return: A list of lists, each sublist representing a bin of roughly constant size.
        """
        result = []
        bins = binpacking.to_constant_volume(items, chunk_size)
        for item in bins:
            result.append(list(item.keys()))
        return result

    def _get_item_sizes(self, root_path):
        """
        Get the size of each item in the root path directory.
        :param root_path: The directory to scan.
        :return: A dictionary of items in the directory in the format {filepath: size in bytes}
        """
        size_dict = {}
        items = os.scandir(root_path)
        for item in items:
            item_size = 0
            if item.is_file():
                item_size = os.path.getsize(item.path)
            elif item.is_dir():
                item_size = self._get_dir_size(item.path)
            size_dict[item.path] = item_size
        return size_dict

    @staticmethod
    def _get_dir_size(dir_path):
        """
        Recursively walk a directory to get the total directory size.
        :param dir_path: The root directory path to traverse.
        :return: The total size of the directory in bytes.
        """
        total_size = 0
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                filepath = os.path.join(root, file)
                if not os.path.islink(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size
