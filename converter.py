#!/usr/local/bin/python
#encoding:utf8
'''
Converter: convert from .wv format to svm/arff/cluto...
'''
from __future__ import with_statement
import sys
import os
import codecs

class WVConverter(object):
    '''word vector file format converter'''
    def __init__(self, fninput, fnoutput):
        self.word_vector_filename = fninput
        self.output_filename = fnoutput
        self.default_encoding = 'utf8'

    def _read_label(self, fnlabel):
        '''read label file'''
        docid2label = {}
        if fnlabel and os.path.exists(fnlabel):
            # format: docid,label
            with open(fnlabel, 'r') as flabel:
                for line in flabel:
                    line = line.strip()
                    parts = line.split(",")
                    if len(parts) == 2:
                        docid2label[int(parts[0])] = parts[1]
        return docid2label

    def to_svm(self, fnlabel=None):
        '''to libsvm format'''
        docid2label = self._read_label(fnlabel)
        with open(self.output_filename, 'w') as foutput:
            with open(self.word_vector_filename, 'r') as finput:
                for line in finput:
                    parts = line.strip().split()
                    foutput.write("%s %s\n" %(docid2label.get(int(parts[0]), 0), ' '.join(parts[1:])))

    def to_triplet(self, fnlabel=None):
        '''to libsvm format'''
        with open(self.output_filename, 'w') as foutput:
            with open(self.word_vector_filename, 'r') as finput:
                for line in finput:
                    parts = line.strip().split()
                    rowid = int(parts[0])
                    colvals = [(int(item.split(':')[0]), float(item.split(':')[1])) for item in parts[1:]]
                    foutput.write('\n'.join(['%d,%d,%f' % (rowid, item[0], item[1]) for item in colvals]))
                    foutput.write('\n')

    def _read_dic(self, fndict):
        '''read dictionary, word->id'''
        lexicon = {}
        with codecs.open(fndict, 'r', encoding=self.default_encoding, errors='strict') as fdict:
            for index, line in enumerate(fdict):
                if isinstance(line, str):
                    line = line.decode(self.default_encoding, 'strict')
                lexicon[line.strip()] = index
        return lexicon

    def to_arff(self, fndict, fnlabel=None):
        '''to weka arff format'''
        #import pdb; pdb.set_trace()
        docid2label = self._read_label(fnlabel)
        lexicon = self._read_dic(fndict)
        with open(self.output_filename, 'w') as foutput:
            # write relation name
            foutput.write("@relation '%s'\n\n" % ("%s-%s" % (self.word_vector_filename, self.output_filename)))
            # write attributes
            for word in lexicon:
                foutput.write("@attribute %s numeric\n" % word.encode(self.default_encoding))
            labels = ",".join(["%s" % l for l in set(docid2label.values())])
            foutput.write("@attribute __label {%s}\n" % ("0" if not labels else labels))
            # label index: len(lexicon)-1+1
            foutput.write("\n@data\n")
            # write data
            with open(self.word_vector_filename, 'r') as finput:
                for line in finput:
                    parts = line.strip().split()
                    foutput.write("{%s,%d %s}\n" 
                            % (",".join([part.replace(":", " ") for part in parts[1:]]), 
                                len(lexicon), 
                                docid2label.get(int(parts[0]), 0)))

def getopts():
    '''parse options'''
    from optparse import OptionParser
    usage = "dumping the details of similarity calculation"
    parser = OptionParser(usage=usage)
    parser.add_option("-i", "--input",
                      dest="input", default="",
                      help="input file")
    parser.add_option("-o", "--output",
                      dest="output", default="",
                      help="output file")
    parser.add_option("-f", "--format",
                      dest="format", default="",
                      help="convert to format: svm/arff/cluto/triplet")
    parser.add_option("-l", "--label",
                      dest="label", default="",
                      help="label file")
    parser.add_option("-d", "--dict",
                      dest="dict", default="",
                      help="dict file")
    parser.add_option("-e", "--encoding", dest="encoding", default="utf8", 
            help="default system encoding, utf8 by default")
    parser.add_option("-p", "--psyco", action='store_true', 
                    dest="psyco", default=False,
                    help="to enable psyco")
    options = parser.parse_args()[0]
    if not options.input or not options.output or not options.format:
        print "-h to see usage"
        sys.exit(-1)
    if options.psyco:
        import psyco
        psyco.full()
    return options.input, options.output, options.format, options.label, options.dict, options.encoding

def main():
    '''main entry'''
    fninput, fnoutput, toformat, fnlabel, fndict, encoding = getopts()
    toformat = toformat.lower()
    converter = WVConverter(fninput, fnoutput)
    converter.default_encoding = encoding
    if toformat == 'svm':
        converter.to_svm(fnlabel)
    elif toformat == 'arff':
        converter.to_arff(fndict, fnlabel)
    elif toformat == 'triplet':
        converter.to_triplet()
    else:
        pass

if __name__ == "__main__":
    main()
