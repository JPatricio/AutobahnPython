###############################################################################
##
##  Copyright (C) 2011-2013 Tavendo GmbH
##
##  Licensed under the Apache License, Version 2.0 (the "License");
##  you may not use this file except in compliance with the License.
##  You may obtain a copy of the License at
##
##      http://www.apache.org/licenses/LICENSE-2.0
##
##  Unless required by applicable law or agreed to in writing, software
##  distributed under the License is distributed on an "AS IS" BASIS,
##  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
##  See the License for the specific language governing permissions and
##  limitations under the License.
##
###############################################################################

from ranstring import randomByteString
from zope.interface import implementer
from twisted.internet import reactor, interfaces

from autobahn.twisted.websocket import WebSocketClientFactory, \
                                       WebSocketClientProtocol, \
                                       connectWS


# 2^63 - This is the maximum imposed by the WS protocol
FRAME_SIZE = 0x7FFFFFFFFFFFFFFF


@implementer(interfaces.IPushProducer)
class RandomByteStreamProducer:
   """
   A Twisted Push Producer generating a stream of random octets sending out data
   in a WebSockets message frame.
   """

   def __init__(self, proto):
      self.proto = proto
      self.started = False
      self.paused = False

   def pauseProducing(self):
      self.paused = True

   def resumeProducing(self):
      self.paused = False

      if not self.started:
         self.proto.beginMessage(isBinary = True)
         self.proto.beginMessageFrame(FRAME_SIZE)
         self.started = True

      while not self.paused:
         data = randomByteString(1024)
         if self.proto.sendMessageFrameData(data) <= 0:
            self.proto.beginMessageFrame(FRAME_SIZE)
            print("new frame started!")

   def stopProducing(self):
      pass


class StreamingProducerHashClientProtocol(WebSocketClientProtocol):
   """
   Streaming WebSockets client that generates stream of random octets
   sent to streaming WebSockets server, which computes a running SHA-256,
   which it will send every BATCH_SIZE octets back to us. This example
   uses a Twisted producer to produce the byte stream as fast as the
   receiver can consume, but not faster. Therefor, we don't need the
   application-level flow control as with the other examples.
   """

   def onOpen(self):
      self.count = 0
      producer = RandomByteStreamProducer(self)
      self.registerProducer(producer, True)
      producer.resumeProducing()

   def onMessage(self, payload, isBinary):
      print("Digest for batch {} computed by server: {}".format(self.count, payload.decode('utf8')))
      self.count += 1


if __name__ == '__main__':

   factory = WebSocketClientFactory("ws://localhost:9000")
   factory.protocol = StreamingProducerHashClientProtocol
   connectWS(factory)
   reactor.run()
