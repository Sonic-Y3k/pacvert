#  This file is part of Pacvert.

import pacvert
import logger
from operator import attrgetter

class Queue:
    # class variables
    active = None
    scanned = None
    pending = None
    finished = None
    error = None

    def __init__(self):
        """
        """
        self.active = []
        self.pending = []
        self.finished = []
        self.error = []

    def sort(self, queue):
        return sorted(queue, key=attrgetter('status', 'finished'))

    def getActive(self, all=False):
        if len(self.active) >= 0 and all == True:
            return self.active
        elif len(self.active) > 0 and all == False:
            return self.active.pop(0)
        else:
            return None

    def getPending(self, all=False):
        if len(self.pending) >= 0 and all == True:
            return self.pending
        elif len(self.pending) > 0 and all == False:
            return self.pending.pop(0)
        else:
            return None

    def getFinished(self, all=False):
        if len(self.finished) >= 0 and all == True:
            return self.finished
        elif len(self.finished) > 0 and all == False:
            return self.finished.pop(0)
        else:
            return None

    def getError(self, all=False):
        if len(self.error) >= 0 and all == True:
            return self.error
        elif len(self.error) > 0 and all == False:
            return self.error.pop(0)
        else:
            return None

    def getMerged(self, status=-1):
        if (status == -1):
            merged = self.getActive(True) + self.getPending(True) + self.getFinished(True) + self.getError(True)
            return merged
        elif (status == 0):
            return self.getActive(True)
        elif (status == 2):
            return self.getPending(True)
        elif (status == 3):
            return self.getFinished(True)
        else:
            return self.getError(True)


    def addActive(self, queueElement):
        logger.debug("Adding '"+queueElement.fullpath+"' to active.")
        self.active.append(self.updateStatus(queueElement, 0))
        #return self.active[-1]

    def addPending(self, queueElement):
        logger.debug("Adding '"+queueElement.fullpath+"' to pending.")
        self.pending.append(self.updateStatus(queueElement, 2))
        #return self.active[-1]

    def addFinished(self, queueElement):
        logger.debug("Adding '"+queueElement.fullpath+"' to finished.")
        self.finished.append(self.updateStatus(queueElement, 3))
        #return self.finished[-1]

    def addFailed(self, queueElement):
        logger.debug("Adding '"+queueElement.fullpath+"' to failed.")
        self.error.append(self.updateStatus(queueElement, 4))
        #return self.error[-1]

    def lenActive(self):
        return len(self.active)

    def lenPending(self):
        return len(self.pending)

    def lenFinished(self):
        return len(self.finished)

    def lenFailed(self):
        return len(self.failed)

    def updateStatus(self, queueElement, newStatus):
        tempQueueElement = queueElement
        tempQueueElement.updateStatus(newStatus)
        return tempQueueElement

    def getIndexFromItemID(self, itemID):
        result = -1
        for i in self.getPending(True):
            if i.fileid == itemID:
                result = self.pending.index(i)

        return result

    def movePending(self, itemID, position):
        currentID = self.getIndexFromItemID(itemID)
        newIndex = currentID
        if position > 0:
            # we are moving down the list (increasing index)
            if (currentID + position) <= self.lenPending():
                newIndex = currentID + position
        else:
            if (currentID + position) >= 0:
                newIndex = currentID + position

        self.pending[currentID], self.pending[newIndex] = self.pending[newIndex], self.pending[currentID]

    def deletePending(self, itemID):
        currentID = self.getIndexFromItemID(itemID)
        if currentID >= 0:
            pacvert.IGNORE_QUEUE.append(self.pending.pop(currentID).fullpath)
