import gzip
import logging

if __name__ == "__main__":
    inputs = sys.argv[1:-1]
    output = sys.argv[-1]
    processor = concat().process(inputs,output)

class concat(object):
    def process(self,inputs,output,input_gzipped=False):
        out = file(output,"w")
        for input in inputs:
            if input_gzipped:
                out.write(gzip.GzipFile(input).read())
            else:
                out.write(file(input).read())
