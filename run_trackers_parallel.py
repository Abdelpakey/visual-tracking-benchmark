import getopt
import numpy as np
from PIL import Image
import time
import itertools
from multiprocessing import *
from config import *
from scripts import *
from copy import deepcopy

def main(argv):
    t0 = time.time()
    trackers = os.listdir(TRACKER_SRC)
    #trackers = ['TEST']
    evalTypes = ['OPE', 'SRE', 'TRE']
    loadSeqs = 'ALL'
    seqs = []
    try:
        opts, args = getopt.getopt(argv, "ht:e:s:",["tracker=","evaltype="
            ,"sequence="])
    except getopt.GetoptError:
        print 'usage : run_trackers.py -t <trackers> -s <sequences>' \
            + '-e <evaltypes>'
        sys.exit(1)

    for opt, arg in opts:
        if opt == '-h':
            print 'usage : run_trackers.py -t <trackers> -s <sequences>' \
                + '-e <evaltypes>'
            sys.exit(0)
        elif opt in ("-t", "--tracker"):
            trackers = [x.strip() for x in arg.split(',')]
            # trackers = [arg]
        elif opt in ("-s", "--sequence"):
            loadSeqs = [x.strip() for x in arg.split(',')]
        elif opt in ("-e", "--evaltype"):
            evalTypes = [x.strip() for x in arg.split(',')]
            # evalTypes = [arg]

    if SETUP_SEQ:
        print 'Setup sequences ...'
        butil.setup_seqs(loadSeqs)

    shiftTypeSet = ['left','right','up','down','topLeft','topRight',
        'bottomLeft', 'bottomRight','scale_8','scale_9','scale_11','scale_12']

    print 'Starting benchmark for {0} trackers, evalTypes : {1}'.format(
        len(trackers), evalTypes)

    for evalType in evalTypes:
        if loadSeqs == 'ALL':
            seqs = butil.load_all_seq_configs()
        else:
            for seqName in loadSeqs:
                try:
                    seq = butil.load_seq_config(seqName)
                    seqs.append(seq)
                except:
                    print 'Cannot load sequence \'{0}\''.format(seqName)
                    sys.exit(1)
        trackerResults = run_trackers(
            trackers, seqs, evalType, shiftTypeSet)
        seqNames = [s.name for s in seqs]
        for tracker in trackers:
            results = trackerResults[tracker]
            if len(results) > 0:
                evalResults, attrList = butil.calc_result(tracker,
                    seqs, results, evalType)
                print "Result of Sequences\t -- '{0}'".format(tracker)
                for seq in seqs:
                    try:
                        print '\t\'{0}\'{1}'.format(
                            seq.name, " "*(12 - len(seq.name))),
                        print "\taveCoverage : {0:.3f}%".format(
                            sum(seq.aveCoverage)/len(seq.aveCoverage) * 100),
                        print "\taveErrCenter : {0:.3f}".format(
                            sum(seq.aveErrCenter)/len(seq.aveErrCenter))
                    except:
                        print '\t\'{0}\'  ERROR!!'.format(seq.name)

                print "Result of attributes\t -- '{0}'".format(tracker)
                for attr in attrList:
                    print "\t\'{0}\'".format(attr.name),
                    print "\toverlap : {0:02.1f}%".format(attr.overlap),
                    print "\tfailures : {0:.1f}".format(attr.error)

                if SAVE_RESULT : 
                    butil.save_results(tracker, evalResults, attrList, 
                        seqNames, evalType)

    t1 = time.time()

    print (t1 - t0), " Time it took to execute sequential processing"

def runParallelTrackersRun(trackers, tmpRes_path, seqs, evalType, shiftTypeSet, idxSeq):
    #print "Running the index: ", idxSeq
    s = seqs[idxSeq]
    s.len = s.endFrame - s.startFrame + 1
    s.s_frames = [None] * s.len

    for i in range(s.len):
        image_no = s.startFrame + i
        _id = s.imgFormat.format(image_no)
        s.s_frames[i] = s.path + _id

    rect_anno = s.gtRect
    numSeg = 20.0
    subSeqs, subAnno = butil.split_seq_TRE(s, numSeg, rect_anno)
    s.subAnno = subAnno
    img = Image.open(s.s_frames[0])
    (imgWidth, imgHeight) = img.size

    trackerResults = dict((t, list()) for t in trackers)
    if evalType == 'OPE':
        subS = subSeqs[0]
        subSeqs = []
        subSeqs.append(subS)

        subA = subAnno[0]
        subAnno = []
        subAnno.append(subA)

    elif evalType == 'SRE':
        subS = subSeqs[0]
        subA = subAnno[0]
        subSeqs = []
        subAnno = []
        r = subS.init_rect

        for i in range(len(shiftTypeSet)):
            subScurrent = deepcopy(subS)
            shiftType = shiftTypeSet[i]
            left = deepcopy(r)
            init_rect = butil.shift_init_BB(left, shiftType, imgH=imgHeight, imgW=imgWidth)
            subScurrent.init_rect = init_rect
            subScurrent.shiftType = shiftType
            subSeqs.append(subScurrent)
            subAnno.append(subA)
            assert subScurrent.init_rect[2] > 0
            assert subScurrent.init_rect[3] > 0

    for idxTrk in range(len(trackers)):
        t = trackers[idxTrk]
        #trackerResults[t] = list()
        if not os.path.exists(TRACKER_SRC + t):
            print '{0} does not exists'.format(t)
            sys.exit(1)
        seqResults = []
        seqLen = len(subSeqs)
        for idx in range(seqLen):
            print '{0}_{1}, {2}_{3}:{4}/{5} - {6}'.format(
                idxTrk + 1, t, idxSeq + 1, s.name, idx + 1, seqLen, \
                evalType)
            rp = tmpRes_path + '_' + t + '_' + str(idx+1) + '/'
            if SAVE_IMAGE and not os.path.exists(rp):
                os.makedirs(rp)
            subS = subSeqs[idx]
            subS.name = s.name + '_' + str(idx)
            if len(subS.init_rect) == 1:
                # matlab double to python integer
                subS.init_rect = map(int, subS.init_rect[0])

            os.chdir(TRACKER_SRC + t)
            funcName = 'run_{0}(subS, rp, SAVE_IMAGE)'.format(t)
            try:
                res = eval(funcName)
            except:
                print 'failed to execute {0} : {1}'.format(
                    t, sys.exc_info())
                sys.exit(1)
            os.chdir(WORKDIR)
            res['seq_name'] = s.name
            res['len'] = subS.len
            res['annoBegin'] = subS.annoBegin
            res['startFrame'] = subS.startFrame

            if evalType == 'SRE':
                res['shiftType'] = shiftTypeSet[idx]
            seqResults.append(res)
            #end for subseqs

        trackerResults[t].append(seqResults)
    return trackerResults

def runParallelTrackersRunOne(a_b):
    return runParallelTrackersRun(*a_b)

def run_trackers(trackers, seqs, evalType, shiftTypeSet):
    tmpRes_path = RESULT_SRC.format('tmp/{0}/'.format(evalType))
    if not os.path.exists(tmpRes_path):
        os.makedirs(tmpRes_path)

    numSeq = len(seqs)

    #
    freeze_support()
    p = Pool()
    idxSequences = range(numSeq)

    for idxSeq in range(numSeq):
        s = seqs[idxSeq]
        s.len = s.endFrame - s.startFrame + 1
        s.s_frames = [None] * s.len

        for i in range(s.len):
            image_no = s.startFrame + i
            _id = s.imgFormat.format(image_no)
            s.s_frames[i] = s.path + _id

        rect_anno = s.gtRect
        numSeg = 20.0
        subSeqs, subAnno = butil.split_seq_TRE(s, numSeg, rect_anno)
        s.subAnno = subAnno

    res = p.map(runParallelTrackersRunOne, itertools.izip(itertools.repeat(trackers),
                                                          itertools.repeat(tmpRes_path),
                                                          itertools.repeat(seqs),
                                                          itertools.repeat(evalType),
                                                          itertools.repeat(shiftTypeSet), idxSequences))
    #for idxSeq in range(numSeq):
    # res is a list of dict with sequences
    trackerResults = dict((t, list()) for t in trackers)
    for i in range(0,len(res)):
        dictWithResults = res[i]
        for t in trackers:
            r = dictWithResults[t]
            r = r[0]
            #r = r[0]
            trackerResults[t].append(r)


    return trackerResults

if __name__ == "__main__":
    main(sys.argv[1:])
