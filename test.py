import math
import os
import uuid
import time

from matplotlib import cm
import matplotlib.animation as animation
import matplotlib.pyplot as plt

import numpy as np
from IPython.display import HTML
import itertools
import tensorflow as tf

from google.protobuf import text_format
from waymo_open_dataset.metrics.ops import py_metrics_ops
from waymo_open_dataset.metrics.python import config_util_py as config_util
from waymo_open_dataset.protos import motion_metrics_pb2

# Example field definition
roadgraph_features = {
    'roadgraph_samples/dir':
        tf.io.FixedLenFeature([20000, 3], tf.float32, default_value=None),
    'roadgraph_samples/id':
        tf.io.FixedLenFeature([20000, 1], tf.int64, default_value=None),
    'roadgraph_samples/type':
        tf.io.FixedLenFeature([20000, 1], tf.int64, default_value=None),
    'roadgraph_samples/valid':
        tf.io.FixedLenFeature([20000, 1], tf.int64, default_value=None),
    'roadgraph_samples/xyz':
        tf.io.FixedLenFeature([20000, 3], tf.float32, default_value=None),
}

# Features of other agents.
state_features = {
    'state/id':
        tf.io.FixedLenFeature([128], tf.float32, default_value=None),
    'state/type':
        tf.io.FixedLenFeature([128], tf.float32, default_value=None),
    'state/is_sdc':
        tf.io.FixedLenFeature([128], tf.int64, default_value=None),
    'state/tracks_to_predict':
        tf.io.FixedLenFeature([128], tf.int64, default_value=None),
    'state/current/bbox_yaw':
        tf.io.FixedLenFeature([128, 1], tf.float32, default_value=None),
    'state/current/height':
        tf.io.FixedLenFeature([128, 1], tf.float32, default_value=None),
    'state/current/length':
        tf.io.FixedLenFeature([128, 1], tf.float32, default_value=None),
    'state/current/timestamp_micros':
        tf.io.FixedLenFeature([128, 1], tf.int64, default_value=None),
    'state/current/valid':
        tf.io.FixedLenFeature([128, 1], tf.int64, default_value=None),
    'state/current/vel_yaw':
        tf.io.FixedLenFeature([128, 1], tf.float32, default_value=None),
    'state/current/velocity_x':
        tf.io.FixedLenFeature([128, 1], tf.float32, default_value=None),
    'state/current/velocity_y':
        tf.io.FixedLenFeature([128, 1], tf.float32, default_value=None),
    'state/current/width':
        tf.io.FixedLenFeature([128, 1], tf.float32, default_value=None),
    'state/current/x':
        tf.io.FixedLenFeature([128, 1], tf.float32, default_value=None),
    'state/current/y':
        tf.io.FixedLenFeature([128, 1], tf.float32, default_value=None),
    'state/current/z':
        tf.io.FixedLenFeature([128, 1], tf.float32, default_value=None),
    'state/future/bbox_yaw':
        tf.io.FixedLenFeature([128, 80], tf.float32, default_value=None),
    'state/future/height':
        tf.io.FixedLenFeature([128, 80], tf.float32, default_value=None),
    'state/future/length':
        tf.io.FixedLenFeature([128, 80], tf.float32, default_value=None),
    'state/future/timestamp_micros':
        tf.io.FixedLenFeature([128, 80], tf.int64, default_value=None),
    'state/future/valid':
        tf.io.FixedLenFeature([128, 80], tf.int64, default_value=None),
    'state/future/vel_yaw':
        tf.io.FixedLenFeature([128, 80], tf.float32, default_value=None),
    'state/future/velocity_x':
        tf.io.FixedLenFeature([128, 80], tf.float32, default_value=None),
    'state/future/velocity_y':
        tf.io.FixedLenFeature([128, 80], tf.float32, default_value=None),
    'state/future/width':
        tf.io.FixedLenFeature([128, 80], tf.float32, default_value=None),
    'state/future/x':
        tf.io.FixedLenFeature([128, 80], tf.float32, default_value=None),
    'state/future/y':
        tf.io.FixedLenFeature([128, 80], tf.float32, default_value=None),
    'state/future/z':
        tf.io.FixedLenFeature([128, 80], tf.float32, default_value=None),
    'state/past/bbox_yaw':
        tf.io.FixedLenFeature([128, 10], tf.float32, default_value=None),
    'state/past/height':
        tf.io.FixedLenFeature([128, 10], tf.float32, default_value=None),
    'state/past/length':
        tf.io.FixedLenFeature([128, 10], tf.float32, default_value=None),
    'state/past/timestamp_micros':
        tf.io.FixedLenFeature([128, 10], tf.int64, default_value=None),
    'state/past/valid':
        tf.io.FixedLenFeature([128, 10], tf.int64, default_value=None),
    'state/past/vel_yaw':
        tf.io.FixedLenFeature([128, 10], tf.float32, default_value=None),
    'state/past/velocity_x':
        tf.io.FixedLenFeature([128, 10], tf.float32, default_value=None),
    'state/past/velocity_y':
        tf.io.FixedLenFeature([128, 10], tf.float32, default_value=None),
    'state/past/width':
        tf.io.FixedLenFeature([128, 10], tf.float32, default_value=None),
    'state/past/x':
        tf.io.FixedLenFeature([128, 10], tf.float32, default_value=None),
    'state/past/y':
        tf.io.FixedLenFeature([128, 10], tf.float32, default_value=None),
    'state/past/z':
        tf.io.FixedLenFeature([128, 10], tf.float32, default_value=None),
}

traffic_light_features = {
    'traffic_light_state/current/state':
        tf.io.FixedLenFeature([1, 16], tf.int64, default_value=None),
    'traffic_light_state/current/valid':
        tf.io.FixedLenFeature([1, 16], tf.int64, default_value=None),
    'traffic_light_state/current/x':
        tf.io.FixedLenFeature([1, 16], tf.float32, default_value=None),
    'traffic_light_state/current/y':
        tf.io.FixedLenFeature([1, 16], tf.float32, default_value=None),
    'traffic_light_state/current/z':
        tf.io.FixedLenFeature([1, 16], tf.float32, default_value=None),
    'traffic_light_state/past/state':
        tf.io.FixedLenFeature([10, 16], tf.int64, default_value=None),
    'traffic_light_state/past/valid':
        tf.io.FixedLenFeature([10, 16], tf.int64, default_value=None),
    'traffic_light_state/past/x':
        tf.io.FixedLenFeature([10, 16], tf.float32, default_value=None),
    'traffic_light_state/past/y':
        tf.io.FixedLenFeature([10, 16], tf.float32, default_value=None),
    'traffic_light_state/past/z':
        tf.io.FixedLenFeature([10, 16], tf.float32, default_value=None),
}

features_description = {}
features_description.update(roadgraph_features)
features_description.update(state_features)
features_description.update(traffic_light_features)

FILENAME = 'dataset/uncompressed_tf_example_training_training_tfexample.tfrecord-00000-of-01000'

dataset = tf.data.TFRecordDataset(FILENAME, compression_type='')
data = next(dataset.as_numpy_iterator())
parsed = tf.io.parse_single_example(data, features_description)

def create_figure_and_axes(size_pixels):
  """Initializes a unique figure and axes for plotting."""
  fig, ax = plt.subplots(1, 1, num=uuid.uuid4())

  # Sets output image to pixel resolution.
  dpi = 100
  size_inches = size_pixels / dpi
  fig.set_size_inches([size_inches, size_inches])
  fig.set_dpi(dpi)
  fig.set_facecolor('white')
  ax.set_facecolor('white')
  ax.xaxis.label.set_color('black')
  ax.tick_params(axis='x', colors='black')
  ax.yaxis.label.set_color('black')
  ax.tick_params(axis='y', colors='black')
  fig.set_tight_layout(True)
  ax.grid(False)
  return fig, ax


def fig_canvas_image(fig):
  """Returns a [H, W, 3] uint8 np.array image from fig.canvas.tostring_rgb()."""
  # Just enough margin in the figure to display xticks and yticks.
  fig.subplots_adjust(
      left=0.08, bottom=0.08, right=0.98, top=0.98, wspace=0.0, hspace=0.0)
  fig.canvas.draw()
  data = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
  return data.reshape(fig.canvas.get_width_height()[::-1] + (3,))


def get_colormap(num_agents):
  """Compute a color map array of shape [num_agents, 4]."""
  colors = cm.get_cmap('jet', num_agents)
  colors = colors(range(num_agents))
  np.random.shuffle(colors)
  return colors


def get_viewport(all_states, all_states_mask):
  """Gets the region containing the data.

  Args:
    all_states: states of agents as an array of shape [num_agents, num_steps,
      2].
    all_states_mask: binary mask of shape [num_agents, num_steps] for
      `all_states`.

  Returns:
    center_y: float. y coordinate for center of data.
    center_x: float. x coordinate for center of data.
    width: float. Width of data.
  """
  valid_states = all_states[all_states_mask]
  all_y = valid_states[..., 1]
  all_x = valid_states[..., 0]

  center_y = (np.max(all_y) + np.min(all_y)) / 2
  center_x = (np.max(all_x) + np.min(all_x)) / 2

  range_y = np.ptp(all_y)
  range_x = np.ptp(all_x)

  width = max(range_y, range_x)

  return center_y, center_x, width


def visualize_one_step(states,
                       mask,
                       roadgraph,
                       title,
                       center_y,
                       center_x,
                       width,
                       color_map,
                       size_pixels=1000):
  """Generate visualization for a single step."""

  # Create figure and axes.
  fig, ax = create_figure_and_axes(size_pixels=size_pixels)

  # Plot roadgraph.
  rg_pts = roadgraph[:, :2].T
  ax.plot(rg_pts[0, :], rg_pts[1, :], 'k.', alpha=1, ms=2)

  masked_x = states[:, 0][mask]
  masked_y = states[:, 1][mask]
  colors = color_map[mask]

  # Plot agent current position.
  ax.scatter(
      masked_x,
      masked_y,
      marker='o',
      linewidths=3,
      color=colors,
  )

  # Title.
  ax.set_title(title)

  # Set axes.  Should be at least 10m on a side and cover 160% of agents.
  size = max(10, width * 1.0)
  ax.axis([
      -size / 2 + center_x, size / 2 + center_x, -size / 2 + center_y,
      size / 2 + center_y
  ])
  ax.set_aspect('equal')

  image = fig_canvas_image(fig)
  plt.close(fig)
  return image


def visualize_all_agents_smooth(
    decoded_example,
    size_pixels=1000,
):
  """Visualizes all agent predicted trajectories in a serie of images.

  Args:
    decoded_example: Dictionary containing agent info about all modeled agents.
    size_pixels: The size in pixels of the output image.

  Returns:
    T of [H, W, 3] uint8 np.arrays of the drawn matplotlib's figure canvas.
  """
  # [num_agents, num_past_steps, 2] float32.
  past_states = tf.stack(
      [decoded_example['state/past/x'], decoded_example['state/past/y']],
      -1).numpy()
  past_states_mask = decoded_example['state/past/valid'].numpy() > 0.0

  # [num_agents, 1, 2] float32.
  current_states = tf.stack(
      [decoded_example['state/current/x'], decoded_example['state/current/y']],
      -1).numpy()
  current_states_mask = decoded_example['state/current/valid'].numpy() > 0.0

  # [num_agents, num_future_steps, 2] float32.
  future_states = tf.stack(
      [decoded_example['state/future/x'], decoded_example['state/future/y']],
      -1).numpy()
  future_states_mask = decoded_example['state/future/valid'].numpy() > 0.0

  # [num_points, 3] float32.
  roadgraph_xyz = decoded_example['roadgraph_samples/xyz'].numpy()

  num_agents, num_past_steps, _ = past_states.shape
  num_future_steps = future_states.shape[1]

  color_map = get_colormap(num_agents)

  # [num_agens, num_past_steps + 1 + num_future_steps, depth] float32.
  all_states = np.concatenate([past_states, current_states, future_states], 1)

  # [num_agens, num_past_steps + 1 + num_future_steps] float32.
  all_states_mask = np.concatenate(
      [past_states_mask, current_states_mask, future_states_mask], 1)

  center_y, center_x, width = get_viewport(all_states, all_states_mask)

  images = []

  # Generate images from past time steps.
  for i, (s, m) in enumerate(
      zip(
          np.split(past_states, num_past_steps, 1),
          np.split(past_states_mask, num_past_steps, 1))):
    im = visualize_one_step(s[:, 0], m[:, 0], roadgraph_xyz,
                            'past: %d' % (num_past_steps - i), center_y,
                            center_x, width, color_map, size_pixels)
    images.append(im)

  # Generate one image for the current time step.
  s = current_states
  m = current_states_mask

  im = visualize_one_step(s[:, 0], m[:, 0], roadgraph_xyz, 'current', center_y,
                          center_x, width, color_map, size_pixels)
  images.append(im)

  # Generate images from future time steps.
  for i, (s, m) in enumerate(
      zip(
          np.split(future_states, num_future_steps, 1),
          np.split(future_states_mask, num_future_steps, 1))):
    im = visualize_one_step(s[:, 0], m[:, 0], roadgraph_xyz,
                            'future: %d' % (i + 1), center_y, center_x, width,
                            color_map, size_pixels)
    images.append(im)

  return images


images = visualize_all_agents_smooth(parsed)
# print(len(images))
# for image in images:
#     plt.imshow(image)
#     plt.show()



def create_animation(images):
  """ Creates a Matplotlib animation of the given images.

  Args:
    images: A list of numpy arrays representing the images.

  Returns:
    A matplotlib.animation.Animation.

  Usage:
    anim = create_animation(images)
    anim.save('/tmp/animation.avi')
    HTML(anim.to_html5_video())
  """

  plt.ioff()
  fig, ax = plt.subplots()
  dpi = 100
  size_inches = 1000 / dpi
  fig.set_size_inches([size_inches, size_inches])
  plt.ion()

  def animate_func(i):
    ax.imshow(images[i])
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid('off')

  anim = animation.FuncAnimation(
      fig, animate_func, frames=len(images) // 2, interval=100)
  plt.close(fig)
  return anim


anim = create_animation(images[::5])
anim.save('animation.avi')

'''

def _parse(value):
  decoded_example = tf.io.parse_single_example(value, features_description)

  past_states = tf.stack([
      decoded_example['state/past/x'], decoded_example['state/past/y'],
      decoded_example['state/past/length'], decoded_example['state/past/width'],
      decoded_example['state/past/bbox_yaw'],
      decoded_example['state/past/velocity_x'],
      decoded_example['state/past/velocity_y']
  ], -1)

  cur_states = tf.stack([
      decoded_example['state/current/x'], decoded_example['state/current/y'],
      decoded_example['state/current/length'],
      decoded_example['state/current/width'],
      decoded_example['state/current/bbox_yaw'],
      decoded_example['state/current/velocity_x'],
      decoded_example['state/current/velocity_y']
  ], -1)

  input_states = tf.concat([past_states, cur_states], 1)[..., :2]

  future_states = tf.stack([
      decoded_example['state/future/x'], decoded_example['state/future/y'],
      decoded_example['state/future/length'],
      decoded_example['state/future/width'],
      decoded_example['state/future/bbox_yaw'],
      decoded_example['state/future/velocity_x'],
      decoded_example['state/future/velocity_y']
  ], -1)

  gt_future_states = tf.concat([past_states, cur_states, future_states], 1)

  past_is_valid = decoded_example['state/past/valid'] > 0
  current_is_valid = decoded_example['state/current/valid'] > 0
  future_is_valid = decoded_example['state/future/valid'] > 0
  gt_future_is_valid = tf.concat(
      [past_is_valid, current_is_valid, future_is_valid], 1)

  # If a sample was not seen at all in the past, we declare the sample as
  # invalid.
  sample_is_valid = tf.reduce_any(
      tf.concat([past_is_valid, current_is_valid], 1), 1)

  inputs = {
      'input_states': input_states,
      'gt_future_states': gt_future_states,
      'gt_future_is_valid': gt_future_is_valid,
      'object_type': decoded_example['state/type'],
      'tracks_to_predict': decoded_example['state/tracks_to_predict'] > 0,
      'sample_is_valid': sample_is_valid,
  }
  return inputs


def _default_metrics_config():
  config = motion_metrics_pb2.MotionMetricsConfig()
  config_text = """
  track_steps_per_second: 10
  prediction_steps_per_second: 2
  track_history_samples: 10
  track_future_samples: 80
  speed_lower_bound: 1.4
  speed_upper_bound: 11.0
  speed_scale_lower: 0.5
  speed_scale_upper: 1.0
  step_configurations {
    measurement_step: 5
    lateral_miss_threshold: 1.0
    longitudinal_miss_threshold: 2.0
  }
  step_configurations {
    measurement_step: 9
    lateral_miss_threshold: 1.8
    longitudinal_miss_threshold: 3.6
  }
  step_configurations {
    measurement_step: 15
    lateral_miss_threshold: 3.0
    longitudinal_miss_threshold: 6.0
  }
  max_predictions: 6
  """
  text_format.Parse(config_text, config)
  return config


class SimpleModel(tf.keras.Model):
  """A simple one-layer regressor."""

  def __init__(self, num_agents_per_scenario, num_states_steps,
               num_future_steps):
    super(SimpleModel, self).__init__()
    self._num_agents_per_scenario = num_agents_per_scenario
    self._num_states_steps = num_states_steps
    self._num_future_steps = num_future_steps
    self.regressor = tf.keras.layers.Dense(num_future_steps * 2)

  def call(self, states):
    states = tf.reshape(states, (-1, self._num_states_steps * 2))
    pred = self.regressor(states)
    pred = tf.reshape(
        pred, [-1, self._num_agents_per_scenario, self._num_future_steps, 2])
    return pred


class MotionMetrics(tf.keras.metrics.Metric):
  """Wrapper for motion metrics computation."""

  def __init__(self, config):
    super().__init__()
    self._prediction_trajectory = []
    self._prediction_score = []
    self._ground_truth_trajectory = []
    self._ground_truth_is_valid = []
    self._prediction_ground_truth_indices = []
    self._prediction_ground_truth_indices_mask = []
    self._object_type = []
    self._metrics_config = config

  def reset_state():
    self._prediction_trajectory = []
    self._prediction_score = []
    self._ground_truth_trajectory = []
    self._ground_truth_is_valid = []
    self._prediction_ground_truth_indices = []
    self._prediction_ground_truth_indices_mask = []
    self._object_type = []

  def update_state(self, prediction_trajectory, prediction_score,
                   ground_truth_trajectory, ground_truth_is_valid,
                   prediction_ground_truth_indices,
                   prediction_ground_truth_indices_mask, object_type):
    self._prediction_trajectory.append(prediction_trajectory)
    self._prediction_score.append(prediction_score)
    self._ground_truth_trajectory.append(ground_truth_trajectory)
    self._ground_truth_is_valid.append(ground_truth_is_valid)
    self._prediction_ground_truth_indices.append(
        prediction_ground_truth_indices)
    self._prediction_ground_truth_indices_mask.append(
        prediction_ground_truth_indices_mask)
    self._object_type.append(object_type)

  def result(self):
    # [batch_size, num_preds, 1, 1, steps, 2].
    # The ones indicate top_k = 1, num_agents_per_joint_prediction = 1.
    prediction_trajectory = tf.concat(self._prediction_trajectory, 0)
    # [batch_size, num_preds, 1].
    prediction_score = tf.concat(self._prediction_score, 0)
    # [batch_size, num_agents, gt_steps, 7].
    ground_truth_trajectory = tf.concat(self._ground_truth_trajectory, 0)
    # [batch_size, num_agents, gt_steps].
    ground_truth_is_valid = tf.concat(self._ground_truth_is_valid, 0)
    # [batch_size, num_preds, 1].
    prediction_ground_truth_indices = tf.concat(
        self._prediction_ground_truth_indices, 0)
    # [batch_size, num_preds, 1].
    prediction_ground_truth_indices_mask = tf.concat(
        self._prediction_ground_truth_indices_mask, 0)
    # [batch_size, num_agents].
    object_type = tf.cast(tf.concat(self._object_type, 0), tf.int64)

    # We are predicting more steps than needed by the eval code. Subsample.
    interval = (
        self._metrics_config.track_steps_per_second //
        self._metrics_config.prediction_steps_per_second)
    prediction_trajectory = prediction_trajectory[...,
                                                  (interval - 1)::interval, :]

    return py_metrics_ops.motion_metrics(
        config=self._metrics_config.SerializeToString(),
        prediction_trajectory=prediction_trajectory,
        prediction_score=prediction_score,
        ground_truth_trajectory=ground_truth_trajectory,
        ground_truth_is_valid=ground_truth_is_valid,
        prediction_ground_truth_indices=prediction_ground_truth_indices,
        prediction_ground_truth_indices_mask=prediction_ground_truth_indices_mask,
        object_type=object_type)


model = SimpleModel(128, 11, 80)
optimizer = tf.keras.optimizers.Adam(learning_rate=1e-3)
loss_fn = tf.keras.losses.MeanSquaredError()
metrics_config = _default_metrics_config()
motion_metrics = MotionMetrics(metrics_config)
metric_names = config_util.get_breakdown_names_from_motion_config(
    metrics_config)


def train_step(inputs):
  with tf.GradientTape() as tape:
    # [batch_size, num_agents, D]
    states = inputs['input_states']

    # Predict. [batch_size, num_agents, steps, 2].
    pred_trajectory = model(states, training=True)

    # Set training target.
    prediction_start = metrics_config.track_history_samples + 1

    # [batch_size, num_agents, steps, 7]
    gt_trajectory = inputs['gt_future_states']
    gt_targets = gt_trajectory[..., prediction_start:, :2]

    # [batch_size, num_agents, steps]
    gt_is_valid = inputs['gt_future_is_valid']
    # [batch_size, num_agents, steps]
    weights = (
        tf.cast(inputs['gt_future_is_valid'][..., prediction_start:],
                tf.float32) *
        tf.cast(inputs['tracks_to_predict'][..., tf.newaxis], tf.float32))

    loss_value = loss_fn(gt_targets, pred_trajectory, sample_weight=weights)
  grads = tape.gradient(loss_value, model.trainable_weights)
  optimizer.apply_gradients(zip(grads, model.trainable_weights))

  # [batch_size, num_agents, steps, 2] ->
  # [batch_size, num_agents, 1, 1, steps, 2].
  # The added dimensions are top_k = 1, num_agents_per_joint_prediction = 1.
  pred_trajectory = pred_trajectory[:, :, tf.newaxis, tf.newaxis]

  # Fake the score since this model does not generate any score per predicted
  # trajectory.
  pred_score = tf.ones(shape=tf.shape(pred_trajectory)[:3])

  # [batch_size, num_agents].
  object_type = inputs['object_type']

  # [batch_size, num_agents].
  batch_size = tf.shape(inputs['tracks_to_predict'])[0]
  num_samples = tf.shape(inputs['tracks_to_predict'])[1]

  pred_gt_indices = tf.range(num_samples, dtype=tf.int64)
  # [batch_size, num_agents, 1].
  pred_gt_indices = tf.tile(pred_gt_indices[tf.newaxis, :, tf.newaxis],
                            (batch_size, 1, 1))
  # [batch_size, num_agents, 1].
  pred_gt_indices_mask = inputs['tracks_to_predict'][..., tf.newaxis]

  motion_metrics.update_state(pred_trajectory, pred_score, gt_trajectory,
                              gt_is_valid, pred_gt_indices,
                              pred_gt_indices_mask, object_type)

  return loss_value


dataset = tf.data.TFRecordDataset(FILENAME)
dataset = dataset.map(_parse)
dataset = dataset.batch(32)

epochs = 2
num_batches_per_epoch = 10

for epoch in range(epochs):
  print('\nStart of epoch %d' % (epoch,))
  start_time = time.time()

  # Iterate over the batches of the dataset.
  for step, batch in enumerate(dataset):
    loss_value = train_step(tf.cast(batch, tf.int64))

    # Log every 10 batches.
    if step % 10 == 0:
      print('Training loss (for one batch) at step %d: %.4f' %
            (step, float(loss_value)))
      print('Seen so far: %d samples' % ((step + 1) * 64))

    if step >= num_batches_per_epoch:
      break

  # Display metrics at the end of each epoch.
  train_metric_values = motion_metrics.result()
  for i, m in enumerate(
      ['min_ade', 'min_fde', 'miss_rate', 'overlap_rate', 'map']):
    for j, n in enumerate(metric_names):
      print('{}/{}: {}'.format(m, n, train_metric_values[i, j]))
'''