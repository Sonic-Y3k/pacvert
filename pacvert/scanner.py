#  This file is part of Pacvert.

from os import path, walk

import pacvert
import logger
from queue_element import QueueElement

def scan():
    """
    Scan given directory for new files.
    """
    try:
        for root, directories, filenames in walk(pacvert.CONFIG.SCAN_DIRECTORIES_PATH):
            for filename in sorted(filenames):
                full_path = path.join(root,filename)
                if full_path not in pacvert.IGNORE_QUEUE:
                    test_file = QueueElement(full_path)
                    
                    if test_file.file_validity() and test_file.file_configure():
                        pacvert.IGNORE_QUEUE.append(full_path)
                        pacvert.QUEUE.append('pending', test_file)
                    else:
                        logger.error('can\'t add file \''+full_path+'\' to queue (probably to young).')
    except Exception as e:
        logger.error('scanning directory \''+pacvert.CONFIG.SCAN_DIRECTORIES_PATH+'\' failed with: '+e.message)