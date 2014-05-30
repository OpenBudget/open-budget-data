import os
import tempfile
import subprocess

if __name__ == "__main__":
    inputs = sys.argv[1]
    output = sys.argv[2]
    processor = rar_to_zip().process(input,output)

class rar_to_zip(object):
    def process(self,input,output):
        outdir = tempfile.mkdtemp()
        p = subprocess.Popen(['unrar','e',os.path.abspath(input)],cwd=outdir)
        p.communicate()
        p = subprocess.Popen(['ls','-la',"*.doc"],cwd=outdir,shell=True,stdout=subprocess.PIPE)
        (o,e) = p.communicate()
        os.unlink(output)
        cmd = ['zip',os.path.abspath(output)]
        cmd.extend(o.split())
        p = subprocess.Popen(cmd,cwd=outdir)
        p.communicate()
