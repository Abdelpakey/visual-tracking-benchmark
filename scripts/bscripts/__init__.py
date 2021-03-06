from run_ASLA import *
from run_BSBT import *
from run_CPF import *
from run_CT import *
from run_CXT import *
from run_DFT import *
from run_Frag import *
from run_IVT import *
from run_KMS import *
from run_L1APG import *
from run_LOT import *
from run_LSK import *
from run_MIL import *
from run_MTT import *
from run_OAB import *
from run_ORIA import *
from run_SBT import *
from run_SCM import *
from run_SMS import *
from run_Struck import *
from run_TLD import *
from run_TEST import *
try:
    from run_RobStruck import *
    from run_RawDeepStruck import *
    from run_ObjStruck import *
    from run_ObjStruck_e0_5 import *
    from run_MBestStruckGauss import *
    from run_MBestStruckDeep import *
except ImportError:
    print "Couldn't import antrack module. Antrack-based trackers are not avaliable. Compile antrack first."

#from run_DeepStruck import *
