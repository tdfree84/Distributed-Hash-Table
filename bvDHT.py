#!/usr/bin/python3
from socket import *
import sys
import os
import time
import threading
import random
from net_functions import *
from hash_functions import *
from peerProfile import *

menu = "--MENU--\nChoose 1 for: insert.\nChoose 2 for: remove.\nChoose 3 for: get.\nChoose 4 for: exists.\nChoose 5 for: owns.\nChoose 6 for: disconnect.\n"


####################
# Helper functions #
####################

def owns(number):
    ''' Find the closest person to the hash number requested. '''
    hashes = list(myProfile.fingerTable.keys())
    hashes.sort(reverse=True)
    print("Number: " + str(number))
    for i in range(len(hashes)):
        if number > hashes[i]:
            #if i == 0:
                #return myProfile.fingerTable[hashes[i]]
            return myProfile.fingerTable[hashes[i]]

    return myProfile.fingerTable[hashes[0]]

def insertFile():
    ''' Inserts file into the DHT. '''

    fileName = input("What is the file called on your system? ")
    try:
        f = open('fileName','r')
    except:
        print("Oops..can't find that file?")
        return

#################
# Peer handling #
#################

def handlePeer(peerInfo):
    ''' handlePeer receives commands from a client sending requests. '''

    #handle a new client that connects
    print("I have connected with someone.")
    peerConn, peerAddr = peerInfo
    conMsg = recvAll(peerConn, 3)
    conMsg = conMsg.decode()
    print(conMsg)
    while conMsg != "DIS":
        if conMsg == "CON":
            peerIP, peerPort = recvAddress(peerConn)
            print(peerIP + ":" + str(peerPort))
            print(myProfile.myAddrString())
            if owns(getHashIndex((peerIP, peerPort))) == myProfile.myAddrString():
                #####################
                #CONNECTION PROTOCOL#
                #####################

                #sending them a T if we own they space they want
                print("T")
                peerConn.send('T'.encode())
                #update our fingertable
                fingerTable = {}
                fingerTable[getHashIndex((peerIP,peerPort))] = str(peerIP + ":" +str(peerPort))
                fingerTable[getHashIndex(myProfile.myAddress)] = myProfile.myAddrString()
                for i in range(5):
                    randKeyRange = random.randint(0, keySpaceRanges)
                    who = owns(randKeyRange)
                    print("Owns: ",who)
                    who_spl = who.split(':')
                    who_tup = (who_spl[0],int(who_spl[1]))
                    #fingerTable[getHashIndex(who_tup)] = who
                    fingerTable[randKeyRange] = who
                    randKeyRange += randKeyRange

                myProfile.fingerTable = fingerTable
                print("My finger table is",myProfile.fingerTable)



                #send the address of our successor
                successor = myProfile.successor.split(":")
                successorIP = successor[0]
                successorPort = successor[1]

                sendAddress(peerConn, (successorIP, int(successorPort)))

                #send the number of items from their hash
                #get file names from repo
                fNameList = os.listdir('repo')
                listToSend = []
                for n in fNameList:
                    nInt = int(n)
                    if nInt < getHashIndex((successorIP, int(successorPort))) and nInt > getHashIndex((peerIP, int(peerPort))):
                        listToSend.append(n)

                sendInt(peerConn, len(listToSend))

                #for number of items, send [key][valSize][val] to peer
                for n in listToSend:
                    f = open('/repo/' + n, 'rb')
                    fBytes = f.read()
                    sendKey(peerConn, int(n))
                    sendVal(peerConn, fBytes) 
                    f.close()


                #receive a T from the client to say everything was received
                tf = recvAll(peerConn, 1)
                if tf = 'T':
                    #set successor to person who just connected to us
                    #they are now our new successor
                    #once done, we no longer own that keyspace, so update
                    #our keyspace ranges
                    myProfile.successor = peerIP + ":" + str(peerPort)
                    
            else:
                #send this if we don't own the space they want
                print("N")
                peerConn.send('N'.encode())

        conMsg = recvAll(peerConn, 3)
        conMsg = conMsg.decode()


def waitForPeerConnections(listener):
    ''' waitForPeerConnections listens for other peers to connect to us and spawns off a new thread for each peer that connects. '''

    while running:
        peerInfo = listener.accept()
        threading.Thread(target=handlePeer, args = (peerInfo,), daemon=True).start()

listener = socket(AF_INET, SOCK_STREAM)
listener.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
listener.bind(('', 0))
listener.listen(32)
port = listener.getsockname()[1]
print("I am: " + getLocalIPAddress() + ":" + str(port))

running = True

#to populate fingerTable, after owns is implemented, we can call
#owns on the offsets we find in the key range to find peers to communicate with
#and populate the fingerTable automatically
fingerTable = {}
keySpaceRanges = 2**160/5
#get random number in keyRange for offset
randKeyRange = random.randint(0, keySpaceRanges)
#all the keyspace we own
myKeySpaceRange = [0,0]
# THIS client's profile
myProfile = ''

# Seed client is len == 1
if len(sys.argv) == 1:
    #set up our own thread to start listening for clients
    print("This is a the seed client")
    threading.Thread(target=waitForPeerConnections, args = (listener,), daemon=True).start()
    addr = getLocalIPAddress() + ":" + str(port)
    fingerTable[getHashIndex((getLocalIPAddress(), int(port)))] = addr
    fingerTable[0] = addr

    print(menu)
    ourHash = getHashIndex((getLocalIPAddress(), int(port)))
    myKeySpaceRange[0] = ourHash
    myKeySpaceRange[1] = ourHash-1
    print(myKeySpaceRange)

    # Initializing my peer profile
    myProfile = PeerProfile((getLocalIPAddress(),int(port)),myKeySpaceRange[0],myKeySpaceRange[1],fingerTable,addr,addr)

    for i in range(5):
        who = owns(randKeyRange)
        print("Owns: ",who)
        who_spl = who.split(':')
        who_tup = (who_spl[0],int(who_spl[1]))
        #fingerTable[getHashIndex(who_tup)] = who
        fingerTable[randKeyRange] = who
        randKeyRange += randKeyRange

    myProfile.fingerTable = fingerTable
    print("My finger table is",myProfile.fingerTable)



    userInput = input("Command?")
    while userInput != "disconnect":
        print("Running")
        print(menu)

        if userInput == "1":
            ###INSERT###


        

        userInput = input("Command?\n")
    

    #this will be for the initial person connecting

# Connecting client passes arguments of ip and port
elif len(sys.argv) == 3:
    #this is for any peer trying to connect to another peer
    #set up our own thread to start listening for clients
    threading.Thread(target=waitForPeerConnections, args = (listener,), daemon=True).start()

    # Continue connecting to peer the user chose
    peerIP = sys.argv[1]
    peerPort = int(sys.argv[2])
    peerConn = socket(AF_INET, SOCK_STREAM)
    peerConn.connect( (peerIP, peerPort) )

    #send the client we connected to our connection protocol
    peerConn.send("CON".encode())
    peerAddress = (getLocalIPAddress(), port)
    sendAddress(peerConn, peerAddress)

    tf = recvAll(peerConn, 1)
    tf = tf.decode()
    
    if(tf == "T"):
       
        # Gathering info for our profile
        addr = getLocalIPAddress() + ":" + str(port)
        # Add ourselves to the finger table
        fingerTable[getHashIndex((getLocalIPAddress(), int(port)))] = addr 
        # Add who we just connected to
        fingerTable[getHashIndex((peerIP, int(peerPort)))] = peerIP +":"+ str(peerPort)
        
        # Set our keyspace (THIS IS WRONG AND NEES TO CHANGE)
        ourHash = getHashIndex((getLocalIPAddress(), int(port)))
        myKeySpaceRange[0] = ourHash
        myKeySpaceRange[1] = ourHash-1
        
        # Finish out rest of connection protocol after we have the ok to continue #
        peerSuccessor = recvAddress(peerConn)
        peerSuccessor = peerSuccessor[0]+":"+str(peerSuccessor[1])

        numItems = recvInt(peerConn)
        if numItems == 0:
            print("Received zero")
            # Send peer we acknowledge we are supposed to receive nothing
            sendVal(peerConn, "T".encode())
        for i in range(numItems):
            print("Receiving file..")
        # End connection protocol #

        # Initializing my peer profile
        myProfile = PeerProfile((getLocalIPAddress(),int(port)),myKeySpaceRange[0],myKeySpaceRange[1],fingerTable,peerSuccessor,peerSuccessor)

        for i in range(5):
            who = owns(randKeyRange)
            #print("Owns: ",who)
            who_spl = who.split(':')
            who_tup = (who_spl[0],int(who_spl[1]))
            #fingerTable[getHashIndex(who_tup)] = who
            fingerTable[randKeyRange] = who
            randKeyRange += randKeyRange

        myProfile.fingerTable = fingerTable
        print("My finger table is",myProfile.fingerTable)

        #recv all protocol messages from peer we connected to
        print(menu)
        userInput = input("Command?\n")
        while userInput != "disconnect":
            print(menu)

            if userInput == "1":
                pass
                ###INSERT###

            userInput = input("Command?\n")
    else:
        pass
        #run owns on our hash
else:
    print("What you doing?")







