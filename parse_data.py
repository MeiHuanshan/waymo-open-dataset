import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()

FILENAME = ['dataset/uncompressed_scenario_training_training.tfrecord-00000-of-01000']

with tf.Session() as sess:
    Keys2Features={}

    reader = tf.TFRecordReader()
    filename_queue = tf.train.string_input_producer(FILENAME)
    coord = tf.train.Coordinator()
    threads = tf.train.start_queue_runners(sess=sess, coord=coord)
    file_sampleId, example = reader.read(filename_queue)
    sample_name,serialized_example=sess.run([file_sampleId,example])
    print(sample_name)
    print(type(serialized_example))
    example_proto = tf.train.Example.FromString(serialized_example)
    print(type(example_proto))
    print(dir(example_proto))
    print(example_proto.ListFields())
    features = example_proto.features
    count = 0
    key_set = set()
    print(features.feature.values())
    # for key in features.feature:
    #     print(key)
    #     if key not in key_set:
    #         key_set.add(key)
    #     count += 1
    #     if count > 100:
    #         exit()
    # print(sorted(list(key_set)))