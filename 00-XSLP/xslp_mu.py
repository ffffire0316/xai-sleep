from tframe import Classifier
from tframe import mu
from tframe.layers import Activation
from tframe.layers.hyper.dense import Dense
from tframe.configs.config_base import Config

from xslp_core import th


def init_model(flatten=False):
  model = Classifier(mark=th.mark)
  model.add(mu.Input(sample_shape=th.input_shape))
  if flatten: model.add(mu.Flatten())
  return model

def output_and_build(model):
  assert isinstance(model, Classifier)
  assert isinstance(th, Config)
  # Add output layer
  model.add(Dense(num_neurons=th.output_dim))
  model.add(Activation('softmax'))
  # Build model and return
  model.build(metric='accuracy', batch_metric='accuracy')
  return model

def conv1d(kernel_size, filters, strides=1):
  """Conv1D layer"""
  return mu.Conv1D(filters, kernel_size, strides,
                   use_batchnorm=th.use_batchnorm,
                   activation=th.activation)

def dilation_conv1d(kernel_size, filters, strides=1):
  """Conv1D layer"""
  return mu.Conv1D(filters, kernel_size, strides,
                   use_batchnorm=th.use_batchnorm,
                   activation=th.activation,
                   dilation_rate=5)

def maxpool(pool_size, strides):
  """Maxpool layer"""
  return mu.MaxPool1D(pool_size, strides)

def dropout():
  """Dropout"""
  return mu.Dropout(0.5)

def flatten():
  return mu.Flatten()

def feature_extracting_net(name, n=32):
  return mu.ForkMergeDAG(vertices=[
    [conv1d(50, 2*n, 6), maxpool(8, 8), dropout(), conv1d(8, 4*n),
     conv1d(8, 4*n), conv1d(8, 4*n), maxpool(4, 4), flatten()],
    [conv1d(400, 2*n, 50), maxpool(4, 4), dropout(), conv1d(6, 4*n),
     conv1d(6, 4*n), conv1d(6, 4*n), maxpool(2, 2), flatten()],
    [mu.Merge.Concat(axis=1), dropout()]],
    edges='1;10;011', name=name)

def xslp_net(name, n=32):
  return mu.ForkMergeDAG(vertices=[
    [conv1d(50, 2*n, 6), maxpool(8, 8), dropout(), conv1d(8, 4*n),
     conv1d(8, 4*n), conv1d(8, 4*n), maxpool(4, 4)],
    [conv1d(400, 2*n, 50), maxpool(4, 4), dropout(), conv1d(6, 4*n),
     conv1d(6, 4*n), conv1d(6, 4*n), maxpool(2, 2)],
    [mu.Merge.Concat(axis=1), dropout()],
    [dilation_conv1d(6, n), dilation_conv1d(6, 2*n), dilation_conv1d(6, 4*n), dropout()],
    [mu.Merge.Sum()]], edges='1;10;011;0001;00011', name=name)

# add confusion metrics to notes
def add_cm_to_note(trainer):
  model = trainer.model
  assert isinstance(model, Classifier)
  cm = model.evaluate_pro(trainer.test_set)
  model.agent.add_to_note_misc('confusion_m', cm)

def get_model():
  model = init_model()
  model.add(xslp_net('xslp_net'))
  model.add(flatten())
  return output_and_build(model)

