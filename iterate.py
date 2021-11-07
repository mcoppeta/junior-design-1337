import os


class SampleFiles:

    def __iter__(self):
        self.directory = 'sample-files'
        self.file_list = []
        for filename in os.listdir(self.directory):
            f = os.path.join(self.directory, filename)
            self.file_list.append(f)

        self.index = 0
        return self

    def __next__(self):
        if self.index < len(self.file_list):
            self.index += 1
            return self.file_list[self.index-1]
        else:
            raise StopIteration
