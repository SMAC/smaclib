#
# Autogenerated by Thrift
#
# DO NOT EDIT UNLESS YOU ARE SURE THAT YOU KNOW WHAT YOU ARE DOING
#

from thrift.Thrift import *
import smaclib.api.module.Module
from ttypes import *
from thrift.Thrift import TProcessor
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol, TProtocol
try:
  from thrift.protocol import fastbinary
except:
  fastbinary = None

from zope.interface import Interface, implements
from twisted.internet import defer
from thrift.transport import TTwisted

class Iface(smaclib.api.module.Module.Iface):
  def analyze_video(video_id, info):
    """
    Analyze the video stream identified by asset_id to obtain segmentation
    information.

    Parameters:
     - video_id
     - info
    """
    pass

  def analyze_slideshow(slideshow_id, info):
    """
    Extract the slide images from the slideshow identified by asset_id.

    Parameters:
     - slideshow_id
     - info
    """
    pass

  def analyze_document(document_id):
    """
    Analyze the document file identified by asset_id to extract the
    relevant information.

    The analyzer to be used is chosen based on the mime-type of the
    document.

    Parameters:
     - document_id
    """
    pass

  def synchronize_slideshow(video_id, slideshow_id, video_segments, slides_file_segments, frames, slides):
    """
    Parameters:
     - video_id
     - slideshow_id
     - video_segments
     - slides_file_segments
     - frames
     - slides
    """
    pass


class Client(smaclib.api.module.Module.Client):
  implements(Iface)

  def __init__(self, transport, oprot_factory):
    smaclib.api.module.Module.Client.__init__(self, transport, oprot_factory)

  def analyze_video(self, video_id, info):
    """
    Analyze the video stream identified by asset_id to obtain segmentation
    information.

    Parameters:
     - video_id
     - info
    """
    self._seqid += 1
    d = self._reqs[self._seqid] = defer.Deferred()
    self.send_analyze_video(video_id, info)
    return d

  def send_analyze_video(self, video_id, info):
    oprot = self._oprot_factory.getProtocol(self._transport)
    oprot.writeMessageBegin('analyze_video', TMessageType.CALL, self._seqid)
    args = analyze_video_args()
    args.video_id = video_id
    args.info = info
    args.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

  def recv_analyze_video(self, iprot, mtype, rseqid):
    d = self._reqs.pop(rseqid)
    if mtype == TMessageType.EXCEPTION:
      x = TApplicationException()
      x.read(iprot)
      iprot.readMessageEnd()
      return d.errback(x)
    result = analyze_video_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.success != None:
      return d.callback(result.success)
    return d.errback(TApplicationException(TApplicationException.MISSING_RESULT, "analyze_video failed: unknown result"))

  def analyze_slideshow(self, slideshow_id, info):
    """
    Extract the slide images from the slideshow identified by asset_id.

    Parameters:
     - slideshow_id
     - info
    """
    self._seqid += 1
    d = self._reqs[self._seqid] = defer.Deferred()
    self.send_analyze_slideshow(slideshow_id, info)
    return d

  def send_analyze_slideshow(self, slideshow_id, info):
    oprot = self._oprot_factory.getProtocol(self._transport)
    oprot.writeMessageBegin('analyze_slideshow', TMessageType.CALL, self._seqid)
    args = analyze_slideshow_args()
    args.slideshow_id = slideshow_id
    args.info = info
    args.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

  def recv_analyze_slideshow(self, iprot, mtype, rseqid):
    d = self._reqs.pop(rseqid)
    if mtype == TMessageType.EXCEPTION:
      x = TApplicationException()
      x.read(iprot)
      iprot.readMessageEnd()
      return d.errback(x)
    result = analyze_slideshow_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.success != None:
      return d.callback(result.success)
    return d.errback(TApplicationException(TApplicationException.MISSING_RESULT, "analyze_slideshow failed: unknown result"))

  def analyze_document(self, document_id):
    """
    Analyze the document file identified by asset_id to extract the
    relevant information.

    The analyzer to be used is chosen based on the mime-type of the
    document.

    Parameters:
     - document_id
    """
    self._seqid += 1
    d = self._reqs[self._seqid] = defer.Deferred()
    self.send_analyze_document(document_id)
    return d

  def send_analyze_document(self, document_id):
    oprot = self._oprot_factory.getProtocol(self._transport)
    oprot.writeMessageBegin('analyze_document', TMessageType.CALL, self._seqid)
    args = analyze_document_args()
    args.document_id = document_id
    args.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

  def recv_analyze_document(self, iprot, mtype, rseqid):
    d = self._reqs.pop(rseqid)
    if mtype == TMessageType.EXCEPTION:
      x = TApplicationException()
      x.read(iprot)
      iprot.readMessageEnd()
      return d.errback(x)
    result = analyze_document_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.success != None:
      return d.callback(result.success)
    return d.errback(TApplicationException(TApplicationException.MISSING_RESULT, "analyze_document failed: unknown result"))

  def synchronize_slideshow(self, video_id, slideshow_id, video_segments, slides_file_segments, frames, slides):
    """
    Parameters:
     - video_id
     - slideshow_id
     - video_segments
     - slides_file_segments
     - frames
     - slides
    """
    self._seqid += 1
    d = self._reqs[self._seqid] = defer.Deferred()
    self.send_synchronize_slideshow(video_id, slideshow_id, video_segments, slides_file_segments, frames, slides)
    return d

  def send_synchronize_slideshow(self, video_id, slideshow_id, video_segments, slides_file_segments, frames, slides):
    oprot = self._oprot_factory.getProtocol(self._transport)
    oprot.writeMessageBegin('synchronize_slideshow', TMessageType.CALL, self._seqid)
    args = synchronize_slideshow_args()
    args.video_id = video_id
    args.slideshow_id = slideshow_id
    args.video_segments = video_segments
    args.slides_file_segments = slides_file_segments
    args.frames = frames
    args.slides = slides
    args.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

  def recv_synchronize_slideshow(self, iprot, mtype, rseqid):
    d = self._reqs.pop(rseqid)
    if mtype == TMessageType.EXCEPTION:
      x = TApplicationException()
      x.read(iprot)
      iprot.readMessageEnd()
      return d.errback(x)
    result = synchronize_slideshow_result()
    result.read(iprot)
    iprot.readMessageEnd()
    if result.success != None:
      return d.callback(result.success)
    return d.errback(TApplicationException(TApplicationException.MISSING_RESULT, "synchronize_slideshow failed: unknown result"))


class Processor(smaclib.api.module.Module.Processor, TProcessor):
  implements(Iface)

  def __init__(self, handler):
    smaclib.api.module.Module.Processor.__init__(self, Iface(handler))
    self._processMap["analyze_video"] = Processor.process_analyze_video
    self._processMap["analyze_slideshow"] = Processor.process_analyze_slideshow
    self._processMap["analyze_document"] = Processor.process_analyze_document
    self._processMap["synchronize_slideshow"] = Processor.process_synchronize_slideshow

  def process(self, iprot, oprot):
    (name, type, seqid) = iprot.readMessageBegin()
    if name not in self._processMap:
      iprot.skip(TType.STRUCT)
      iprot.readMessageEnd()
      x = TApplicationException(TApplicationException.UNKNOWN_METHOD, 'Unknown function %s' % (name))
      oprot.writeMessageBegin(name, TMessageType.EXCEPTION, seqid)
      x.write(oprot)
      oprot.writeMessageEnd()
      oprot.trans.flush()
      return defer.succeed(None)
    else:
      return self._processMap[name](self, seqid, iprot, oprot)

  def process_analyze_video(self, seqid, iprot, oprot):
    args = analyze_video_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = analyze_video_result()
    d = defer.maybeDeferred(self._handler.analyze_video, args.video_id, args.info)
    d.addCallback(self.write_results_success_analyze_video, result, seqid, oprot)
    return d

  def write_results_success_analyze_video(self, success, result, seqid, oprot):
    result.success = success
    oprot.writeMessageBegin("analyze_video", TMessageType.REPLY, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

  def process_analyze_slideshow(self, seqid, iprot, oprot):
    args = analyze_slideshow_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = analyze_slideshow_result()
    d = defer.maybeDeferred(self._handler.analyze_slideshow, args.slideshow_id, args.info)
    d.addCallback(self.write_results_success_analyze_slideshow, result, seqid, oprot)
    return d

  def write_results_success_analyze_slideshow(self, success, result, seqid, oprot):
    result.success = success
    oprot.writeMessageBegin("analyze_slideshow", TMessageType.REPLY, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

  def process_analyze_document(self, seqid, iprot, oprot):
    args = analyze_document_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = analyze_document_result()
    d = defer.maybeDeferred(self._handler.analyze_document, args.document_id)
    d.addCallback(self.write_results_success_analyze_document, result, seqid, oprot)
    return d

  def write_results_success_analyze_document(self, success, result, seqid, oprot):
    result.success = success
    oprot.writeMessageBegin("analyze_document", TMessageType.REPLY, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()

  def process_synchronize_slideshow(self, seqid, iprot, oprot):
    args = synchronize_slideshow_args()
    args.read(iprot)
    iprot.readMessageEnd()
    result = synchronize_slideshow_result()
    d = defer.maybeDeferred(self._handler.synchronize_slideshow, args.video_id, args.slideshow_id, args.video_segments, args.slides_file_segments, args.frames, args.slides)
    d.addCallback(self.write_results_success_synchronize_slideshow, result, seqid, oprot)
    return d

  def write_results_success_synchronize_slideshow(self, success, result, seqid, oprot):
    result.success = success
    oprot.writeMessageBegin("synchronize_slideshow", TMessageType.REPLY, seqid)
    result.write(oprot)
    oprot.writeMessageEnd()
    oprot.trans.flush()


# HELPER FUNCTIONS AND STRUCTURES

class analyze_video_args:
  """
  Attributes:
   - video_id
   - info
  """

  thrift_spec = (
    None, # 0
    (1, TType.STRING, 'video_id', None, None, ), # 1
    (2, TType.I16, 'info', None, None, ), # 2
  )

  def __init__(self, video_id=None, info=None,):
    self.video_id = video_id
    self.info = info

  def read(self, iprot):
    if iprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None and fastbinary is not None:
      fastbinary.decode_binary(self, iprot.trans, (self.__class__, self.thrift_spec))
      return
    iprot.readStructBegin()
    while True:
      (fname, ftype, fid) = iprot.readFieldBegin()
      if ftype == TType.STOP:
        break
      if fid == 1:
        if ftype == TType.STRING:
          self.video_id = iprot.readString();
        else:
          iprot.skip(ftype)
      elif fid == 2:
        if ftype == TType.I16:
          self.info = iprot.readI16();
        else:
          iprot.skip(ftype)
      else:
        iprot.skip(ftype)
      iprot.readFieldEnd()
    iprot.readStructEnd()

  def write(self, oprot):
    if oprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and self.thrift_spec is not None and fastbinary is not None:
      oprot.trans.write(fastbinary.encode_binary(self, (self.__class__, self.thrift_spec)))
      return
    oprot.writeStructBegin('analyze_video_args')
    if self.video_id != None:
      oprot.writeFieldBegin('video_id', TType.STRING, 1)
      oprot.writeString(self.video_id)
      oprot.writeFieldEnd()
    if self.info != None:
      oprot.writeFieldBegin('info', TType.I16, 2)
      oprot.writeI16(self.info)
      oprot.writeFieldEnd()
    oprot.writeFieldStop()
    oprot.writeStructEnd()
    def validate(self):
      return


  def __repr__(self):
    L = ['%s=%r' % (key, value)
      for key, value in self.__dict__.iteritems()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

  def __eq__(self, other):
    return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

  def __ne__(self, other):
    return not (self == other)

class analyze_video_result:
  """
  Attributes:
   - success
  """

  thrift_spec = (
    (0, TType.STRING, 'success', None, None, ), # 0
  )

  def __init__(self, success=None,):
    self.success = success

  def read(self, iprot):
    if iprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None and fastbinary is not None:
      fastbinary.decode_binary(self, iprot.trans, (self.__class__, self.thrift_spec))
      return
    iprot.readStructBegin()
    while True:
      (fname, ftype, fid) = iprot.readFieldBegin()
      if ftype == TType.STOP:
        break
      if fid == 0:
        if ftype == TType.STRING:
          self.success = iprot.readString();
        else:
          iprot.skip(ftype)
      else:
        iprot.skip(ftype)
      iprot.readFieldEnd()
    iprot.readStructEnd()

  def write(self, oprot):
    if oprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and self.thrift_spec is not None and fastbinary is not None:
      oprot.trans.write(fastbinary.encode_binary(self, (self.__class__, self.thrift_spec)))
      return
    oprot.writeStructBegin('analyze_video_result')
    if self.success != None:
      oprot.writeFieldBegin('success', TType.STRING, 0)
      oprot.writeString(self.success)
      oprot.writeFieldEnd()
    oprot.writeFieldStop()
    oprot.writeStructEnd()
    def validate(self):
      return


  def __repr__(self):
    L = ['%s=%r' % (key, value)
      for key, value in self.__dict__.iteritems()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

  def __eq__(self, other):
    return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

  def __ne__(self, other):
    return not (self == other)

class analyze_slideshow_args:
  """
  Attributes:
   - slideshow_id
   - info
  """

  thrift_spec = (
    None, # 0
    (1, TType.STRING, 'slideshow_id', None, None, ), # 1
    (2, TType.I16, 'info', None, None, ), # 2
  )

  def __init__(self, slideshow_id=None, info=None,):
    self.slideshow_id = slideshow_id
    self.info = info

  def read(self, iprot):
    if iprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None and fastbinary is not None:
      fastbinary.decode_binary(self, iprot.trans, (self.__class__, self.thrift_spec))
      return
    iprot.readStructBegin()
    while True:
      (fname, ftype, fid) = iprot.readFieldBegin()
      if ftype == TType.STOP:
        break
      if fid == 1:
        if ftype == TType.STRING:
          self.slideshow_id = iprot.readString();
        else:
          iprot.skip(ftype)
      elif fid == 2:
        if ftype == TType.I16:
          self.info = iprot.readI16();
        else:
          iprot.skip(ftype)
      else:
        iprot.skip(ftype)
      iprot.readFieldEnd()
    iprot.readStructEnd()

  def write(self, oprot):
    if oprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and self.thrift_spec is not None and fastbinary is not None:
      oprot.trans.write(fastbinary.encode_binary(self, (self.__class__, self.thrift_spec)))
      return
    oprot.writeStructBegin('analyze_slideshow_args')
    if self.slideshow_id != None:
      oprot.writeFieldBegin('slideshow_id', TType.STRING, 1)
      oprot.writeString(self.slideshow_id)
      oprot.writeFieldEnd()
    if self.info != None:
      oprot.writeFieldBegin('info', TType.I16, 2)
      oprot.writeI16(self.info)
      oprot.writeFieldEnd()
    oprot.writeFieldStop()
    oprot.writeStructEnd()
    def validate(self):
      return


  def __repr__(self):
    L = ['%s=%r' % (key, value)
      for key, value in self.__dict__.iteritems()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

  def __eq__(self, other):
    return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

  def __ne__(self, other):
    return not (self == other)

class analyze_slideshow_result:
  """
  Attributes:
   - success
  """

  thrift_spec = (
    (0, TType.STRING, 'success', None, None, ), # 0
  )

  def __init__(self, success=None,):
    self.success = success

  def read(self, iprot):
    if iprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None and fastbinary is not None:
      fastbinary.decode_binary(self, iprot.trans, (self.__class__, self.thrift_spec))
      return
    iprot.readStructBegin()
    while True:
      (fname, ftype, fid) = iprot.readFieldBegin()
      if ftype == TType.STOP:
        break
      if fid == 0:
        if ftype == TType.STRING:
          self.success = iprot.readString();
        else:
          iprot.skip(ftype)
      else:
        iprot.skip(ftype)
      iprot.readFieldEnd()
    iprot.readStructEnd()

  def write(self, oprot):
    if oprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and self.thrift_spec is not None and fastbinary is not None:
      oprot.trans.write(fastbinary.encode_binary(self, (self.__class__, self.thrift_spec)))
      return
    oprot.writeStructBegin('analyze_slideshow_result')
    if self.success != None:
      oprot.writeFieldBegin('success', TType.STRING, 0)
      oprot.writeString(self.success)
      oprot.writeFieldEnd()
    oprot.writeFieldStop()
    oprot.writeStructEnd()
    def validate(self):
      return


  def __repr__(self):
    L = ['%s=%r' % (key, value)
      for key, value in self.__dict__.iteritems()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

  def __eq__(self, other):
    return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

  def __ne__(self, other):
    return not (self == other)

class analyze_document_args:
  """
  Attributes:
   - document_id
  """

  thrift_spec = (
    None, # 0
    (1, TType.STRING, 'document_id', None, None, ), # 1
  )

  def __init__(self, document_id=None,):
    self.document_id = document_id

  def read(self, iprot):
    if iprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None and fastbinary is not None:
      fastbinary.decode_binary(self, iprot.trans, (self.__class__, self.thrift_spec))
      return
    iprot.readStructBegin()
    while True:
      (fname, ftype, fid) = iprot.readFieldBegin()
      if ftype == TType.STOP:
        break
      if fid == 1:
        if ftype == TType.STRING:
          self.document_id = iprot.readString();
        else:
          iprot.skip(ftype)
      else:
        iprot.skip(ftype)
      iprot.readFieldEnd()
    iprot.readStructEnd()

  def write(self, oprot):
    if oprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and self.thrift_spec is not None and fastbinary is not None:
      oprot.trans.write(fastbinary.encode_binary(self, (self.__class__, self.thrift_spec)))
      return
    oprot.writeStructBegin('analyze_document_args')
    if self.document_id != None:
      oprot.writeFieldBegin('document_id', TType.STRING, 1)
      oprot.writeString(self.document_id)
      oprot.writeFieldEnd()
    oprot.writeFieldStop()
    oprot.writeStructEnd()
    def validate(self):
      return


  def __repr__(self):
    L = ['%s=%r' % (key, value)
      for key, value in self.__dict__.iteritems()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

  def __eq__(self, other):
    return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

  def __ne__(self, other):
    return not (self == other)

class analyze_document_result:
  """
  Attributes:
   - success
  """

  thrift_spec = (
    (0, TType.STRING, 'success', None, None, ), # 0
  )

  def __init__(self, success=None,):
    self.success = success

  def read(self, iprot):
    if iprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None and fastbinary is not None:
      fastbinary.decode_binary(self, iprot.trans, (self.__class__, self.thrift_spec))
      return
    iprot.readStructBegin()
    while True:
      (fname, ftype, fid) = iprot.readFieldBegin()
      if ftype == TType.STOP:
        break
      if fid == 0:
        if ftype == TType.STRING:
          self.success = iprot.readString();
        else:
          iprot.skip(ftype)
      else:
        iprot.skip(ftype)
      iprot.readFieldEnd()
    iprot.readStructEnd()

  def write(self, oprot):
    if oprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and self.thrift_spec is not None and fastbinary is not None:
      oprot.trans.write(fastbinary.encode_binary(self, (self.__class__, self.thrift_spec)))
      return
    oprot.writeStructBegin('analyze_document_result')
    if self.success != None:
      oprot.writeFieldBegin('success', TType.STRING, 0)
      oprot.writeString(self.success)
      oprot.writeFieldEnd()
    oprot.writeFieldStop()
    oprot.writeStructEnd()
    def validate(self):
      return


  def __repr__(self):
    L = ['%s=%r' % (key, value)
      for key, value in self.__dict__.iteritems()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

  def __eq__(self, other):
    return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

  def __ne__(self, other):
    return not (self == other)

class synchronize_slideshow_args:
  """
  Attributes:
   - video_id
   - slideshow_id
   - video_segments
   - slides_file_segments
   - frames
   - slides
  """

  thrift_spec = (
    None, # 0
    (1, TType.STRING, 'video_id', None, None, ), # 1
    (2, TType.STRING, 'slideshow_id', None, None, ), # 2
    (3, TType.I16, 'video_segments', None, None, ), # 3
    (4, TType.I16, 'slides_file_segments', None, None, ), # 4
    (5, TType.I16, 'frames', None, None, ), # 5
    (6, TType.I16, 'slides', None, None, ), # 6
  )

  def __init__(self, video_id=None, slideshow_id=None, video_segments=None, slides_file_segments=None, frames=None, slides=None,):
    self.video_id = video_id
    self.slideshow_id = slideshow_id
    self.video_segments = video_segments
    self.slides_file_segments = slides_file_segments
    self.frames = frames
    self.slides = slides

  def read(self, iprot):
    if iprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None and fastbinary is not None:
      fastbinary.decode_binary(self, iprot.trans, (self.__class__, self.thrift_spec))
      return
    iprot.readStructBegin()
    while True:
      (fname, ftype, fid) = iprot.readFieldBegin()
      if ftype == TType.STOP:
        break
      if fid == 1:
        if ftype == TType.STRING:
          self.video_id = iprot.readString();
        else:
          iprot.skip(ftype)
      elif fid == 2:
        if ftype == TType.STRING:
          self.slideshow_id = iprot.readString();
        else:
          iprot.skip(ftype)
      elif fid == 3:
        if ftype == TType.I16:
          self.video_segments = iprot.readI16();
        else:
          iprot.skip(ftype)
      elif fid == 4:
        if ftype == TType.I16:
          self.slides_file_segments = iprot.readI16();
        else:
          iprot.skip(ftype)
      elif fid == 5:
        if ftype == TType.I16:
          self.frames = iprot.readI16();
        else:
          iprot.skip(ftype)
      elif fid == 6:
        if ftype == TType.I16:
          self.slides = iprot.readI16();
        else:
          iprot.skip(ftype)
      else:
        iprot.skip(ftype)
      iprot.readFieldEnd()
    iprot.readStructEnd()

  def write(self, oprot):
    if oprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and self.thrift_spec is not None and fastbinary is not None:
      oprot.trans.write(fastbinary.encode_binary(self, (self.__class__, self.thrift_spec)))
      return
    oprot.writeStructBegin('synchronize_slideshow_args')
    if self.video_id != None:
      oprot.writeFieldBegin('video_id', TType.STRING, 1)
      oprot.writeString(self.video_id)
      oprot.writeFieldEnd()
    if self.slideshow_id != None:
      oprot.writeFieldBegin('slideshow_id', TType.STRING, 2)
      oprot.writeString(self.slideshow_id)
      oprot.writeFieldEnd()
    if self.video_segments != None:
      oprot.writeFieldBegin('video_segments', TType.I16, 3)
      oprot.writeI16(self.video_segments)
      oprot.writeFieldEnd()
    if self.slides_file_segments != None:
      oprot.writeFieldBegin('slides_file_segments', TType.I16, 4)
      oprot.writeI16(self.slides_file_segments)
      oprot.writeFieldEnd()
    if self.frames != None:
      oprot.writeFieldBegin('frames', TType.I16, 5)
      oprot.writeI16(self.frames)
      oprot.writeFieldEnd()
    if self.slides != None:
      oprot.writeFieldBegin('slides', TType.I16, 6)
      oprot.writeI16(self.slides)
      oprot.writeFieldEnd()
    oprot.writeFieldStop()
    oprot.writeStructEnd()
    def validate(self):
      return


  def __repr__(self):
    L = ['%s=%r' % (key, value)
      for key, value in self.__dict__.iteritems()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

  def __eq__(self, other):
    return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

  def __ne__(self, other):
    return not (self == other)

class synchronize_slideshow_result:
  """
  Attributes:
   - success
  """

  thrift_spec = (
    (0, TType.STRING, 'success', None, None, ), # 0
  )

  def __init__(self, success=None,):
    self.success = success

  def read(self, iprot):
    if iprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None and fastbinary is not None:
      fastbinary.decode_binary(self, iprot.trans, (self.__class__, self.thrift_spec))
      return
    iprot.readStructBegin()
    while True:
      (fname, ftype, fid) = iprot.readFieldBegin()
      if ftype == TType.STOP:
        break
      if fid == 0:
        if ftype == TType.STRING:
          self.success = iprot.readString();
        else:
          iprot.skip(ftype)
      else:
        iprot.skip(ftype)
      iprot.readFieldEnd()
    iprot.readStructEnd()

  def write(self, oprot):
    if oprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and self.thrift_spec is not None and fastbinary is not None:
      oprot.trans.write(fastbinary.encode_binary(self, (self.__class__, self.thrift_spec)))
      return
    oprot.writeStructBegin('synchronize_slideshow_result')
    if self.success != None:
      oprot.writeFieldBegin('success', TType.STRING, 0)
      oprot.writeString(self.success)
      oprot.writeFieldEnd()
    oprot.writeFieldStop()
    oprot.writeStructEnd()
    def validate(self):
      return


  def __repr__(self):
    L = ['%s=%r' % (key, value)
      for key, value in self.__dict__.iteritems()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

  def __eq__(self, other):
    return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

  def __ne__(self, other):
    return not (self == other)
