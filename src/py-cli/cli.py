import logging
import logging.config
from optparse import OptionParser
import os
import string
import sys

import libsmbios_c

def getStdOptionParser(usage, version):
    parser = OptionParser(usage=usage, version=version)
    return addStdOptions(parser)

def addStdOptions(parser):
    parser.add_option("-v", "--verbose", action="count", dest="verbosity", default=1, help=_("Display more verbose output."))
    parser.add_option("-q", "--quiet", action="store_const", const=0, dest="verbosity", help=_("Minimize program output. Only errors and warnings are displayed."))
    parser.add_option("--trace", action="store_true", dest="trace", default=False, help=_("Enable verbose function tracing."))
    parser.add_option("--logconfig", action="store", default=os.path.join(libsmbios_c.pkgconfdir, "logging.conf"), help=_("Specify alternate config log."))

    parser.add_option('--security-key', action="store", dest="security_key", help=_("BIOS pre-calculated security key."))
    parser.add_option('--password', action="store", dest="password",
                      help=_("BIOS Setup password for set/activate operations."))
    parser.add_option('-r', '--rawpassword', action="store_true", dest="raw", default=False,
                      help=_("Do not auto-convert password to scancodes."))

    parser.add_option('--memory-dat', action="store", type="string", dest="memory_dat",
                      help=_("Path to a memory dump file to use instead of real RAM"),
                      default=None)
    parser.add_option('--cmos-dat', action="store", type="string", dest="cmos_dat",
                      help=_("Path to a CMOS dump file to use instead of real CMOS"),
                      default=None)
    return parser

def setup_std_options(options):
    if options.memory_dat is not None:
        import libsmbios_c.memory as mem
        mem.MemoryAccess( flags= mem.MEMORY_GET_SINGLETON | mem.MEMORY_UNIT_TEST_MODE, factory_args=(options.memory_dat,))

    if options.cmos_dat is not None:
        import libsmbios_c.cmos as cmos
        cmos.CmosAccess( flags= cmos.CMOS_GET_SINGLETON | cmos.CMOS_UNIT_TEST_MODE, factory_args=(options.cmos_dat,))

    options.password_scancode = None
    if options.password is not None:
        options.password_scancode = braindead_asc_to_scancode(options.password)
    options.password_ascii = options.password
    if options.raw:
        options.password_scancode = options.password

    if options.security_key:
        options.security_key = int(options.security_key, 0)


    setupLogging(options.logconfig, options.verbosity, options.trace)


def setupLogging(configFile, verbosity=1, trace=0):
    # set up logging
    logging.basicConfig()
    logging.raiseExceptions = 0
    if configFile:
        logging.config.fileConfig(configFile)

    root_log    = logging.getLogger()
    log         = logging.getLogger("libsmbios_c")
    verbose_log = logging.getLogger("verbose")
    trace_log   = logging.getLogger("trace")

    log.propagate = 0
    trace_log.propagate = 0
    verbose_log.propagate = 0

    if verbosity >= 1:
        log.propagate = 1
    if verbosity >= 2:
        verbose_log.propagate = 1
    if verbosity >= 3:
        for hdlr in root_log.handlers:
            hdlr.setLevel(logging.DEBUG)
    if trace:
        trace_log.propagate = 1


def wrap(s, line_len=80, indent=0, first_line_indent=0, first_line_start=0):
    sys.stdout.write(" "*first_line_indent)
    chars_printed = first_line_start
    for c in s:
        sys.stdout.write(c)
        chars_printed = chars_printed + 1
        if chars_printed > line_len:
            sys.stdout.write("\n")
            chars_printed=indent
            sys.stdout.write(" "*indent)

def makePrintable(s):
    printable = 1
    for ch in s:
        if ch not in string.printable:
            printable=0

    if printable:
        return s

    else:
        retstr=""
        i = 0
        for ch in s:
            i = i+1
            retstr = retstr + "0x%02x" % ord(ch)
        return retstr

def getSecurityKey(options):
    if options.security_key is None:
        fmt = libsmbios_c.smi.password_format(libsmbios_c.smi.DELL_SMI_PASSWORD_ADMIN)
        passToTry = options.password_ascii
        if fmt == libsmbios_c.smi.DELL_SMI_PASSWORD_FMT_SCANCODE:
            passToTry = options.password_scancode

        options.security_key = libsmbios_c.smi.get_security_key( passToTry )
    return options.security_key

# for testing only. It only does en_US, which is just wrong.
def braindead_asc_to_scancode(s):
    return "".join([ chr(asc_to_scancode_map[ord(i)]) for i in s ])

asc_to_scancode_map = [
        0x03, 0x1E, 0x30, 0x46,  0x20, 0x12, 0x21, 0x22,
        0x0E, 0x0F, 0x1C, 0x25,  0x26, 0x1C, 0x31, 0x18,
        0x19, 0x10, 0x13, 0x1F,  0x14, 0x16, 0x2F, 0x11,
        0x2D, 0x15, 0x2C, 0x1A,  0x2B, 0x1B, 0x07, 0x0C,
        0x39, 0x02, 0x28, 0x04,  0x05, 0x06, 0x08, 0x28,
        0x0A, 0x0B, 0x09, 0x0D,  0x33, 0x0C, 0x34, 0x35,
        0x0B, 0x02, 0x03, 0x04,  0x05, 0x06, 0x07, 0x08,
        0x09, 0x0A, 0x27, 0x27,  0x33, 0x0D, 0x34, 0x35,
        0x03, 0x1E, 0x30, 0x2E,  0x20, 0x12, 0x21, 0x22,
        0x23, 0x17, 0x24, 0x25,  0x26, 0x32, 0x31, 0x18,
        0x19, 0x10, 0x13, 0x1F,  0x14, 0x16, 0x2F, 0x11,
        0x2D, 0x15, 0x2C, 0x1A,  0x2B, 0x1B, 0x07, 0x0C,
        0x29, 0x1E, 0x30, 0x2E,  0x20, 0x12, 0x21, 0x22,
        0x23, 0x17, 0x24, 0x25,  0x26, 0x32, 0x31, 0x18,
        0x19, 0x10, 0x13, 0x1F,  0x14, 0x16, 0x2F, 0x11,
        0x2D, 0x15, 0x2C, 0x1A,  0x2B, 0x1B, 0x29, 0x0E,
        0x00, 0x00, 0x00, 0x00,  0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,  0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,  0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,  0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,  0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,  0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,  0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,  0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,  0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,  0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,  0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,  0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,  0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,  0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,  0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,  0x00, 0x00, 0x00, 0x00
    ]
